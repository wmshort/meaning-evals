"""The command line: build, worksheet, import-gold, judge, score, report.

This is the only module that reads the environment, constructs provider clients or reads
the clock; everything below it receives them. Commands that call a provider check for the
keys they need before they read any data or make any call.
"""

from __future__ import annotations

import argparse
import logging
import os
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from meaning_evals.build import Generator, build_items, replace_duplicate_twins
from meaning_evals.config import Layout, Settings, load_settings
from meaning_evals.errors import ConfigError, DataError, MeaningEvalsError
from meaning_evals.gold import import_gold
from meaning_evals.jsonl import (
    append_record,
    read_model,
    read_records,
    read_records_if_present,
    write_records,
    write_text_atomically,
)
from meaning_evals.judge import Judge, run_judging
from meaning_evals.logconfig import configure_logging
from meaning_evals.prompts import load_prompts
from meaning_evals.providers import ClientSettings, Provider, ProviderName, make_provider, read_keys
from meaning_evals.report import render_report
from meaning_evals.schema import GoldLabel, Item, JudgeResult, Passage, PassageId, Question
from meaning_evals.scoring import Rater, ScoreSet, score
from meaning_evals.worksheet import write_worksheet

log = logging.getLogger("meaning_evals")

ProviderFactory = Callable[[ProviderName, str, ClientSettings], Provider]
EXIT_FAILURE = 2
DESCRIPTION = (
    "Measure whether a model can tell a meaning-level divergence from a faithful paraphrase "
    "of the guidance it was meant to follow. The commands run in this order: build, "
    "worksheet, import-gold, judge, score, report."
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Context:
    settings: Settings
    layout: Layout
    environ: Mapping[str, str]
    provider_factory: ProviderFactory
    now: Callable[[], datetime]

    def providers(self, names: set[ProviderName]) -> dict[ProviderName, Provider]:
        """One client per provider; fails before any call if a key is missing."""
        keys = read_keys(names, self.environ)
        client = self.settings.requests.client_settings()
        return {name: self.provider_factory(name, key, client) for name, key in keys.items()}


def _build(ctx: Context, args: argparse.Namespace) -> int:
    generator_settings = ctx.settings.generator
    provider = ctx.providers({generator_settings.provider})[generator_settings.provider]
    layout = ctx.layout
    generator = Generator(
        provider=provider,
        settings=generator_settings,
        prompts=load_prompts(layout.prompts_dir),
        now=ctx.now,
    )
    if args.replace_duplicate_twins:
        if args.passage or args.faithful_only:
            raise ConfigError(
                "--replace-duplicate-twins cannot be combined with --passage or --faithful-only"
            )
        items = replace_duplicate_twins(
            passages=read_records(layout.passages, Passage),
            questions=read_records(layout.questions, Question),
            existing=read_records(layout.items, Item),
            generator=generator,
            save=lambda built: write_records(layout.items, built),
        )
        log.info("event=build_done items=%d path=%s", len(items), layout.items)
        return 0
    items = build_items(
        passages=read_records(layout.passages, Passage),
        questions=read_records(layout.questions, Question),
        existing=read_records_if_present(layout.items, Item),
        generator=generator,
        selected={PassageId(p) for p in args.passage} if args.passage else None,
        save=lambda built: write_records(layout.items, built),
        faithful_only=args.faithful_only,
    )
    log.info("event=build_done items=%d path=%s", len(items), layout.items)
    return 0


def _worksheet(ctx: Context, args: argparse.Namespace) -> int:
    path = args.out or ctx.layout.worksheet
    count = write_worksheet(
        path,
        read_records(ctx.layout.passages, Passage),
        read_records(ctx.layout.items, Item),
        ctx.settings.worksheet.seed,
    )
    log.info("event=worksheet_written items=%d path=%s", count, path)
    return 0


def _import_gold(ctx: Context, args: argparse.Namespace) -> int:
    try:
        text = Path(args.export).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DataError(f"export file {args.export} does not exist") from exc
    items = read_records(ctx.layout.items, Item)
    gold = import_gold(text, items)
    write_records(ctx.layout.gold, gold)
    log.info(
        "event=gold_imported labels=%d unlabelled=%d path=%s",
        len(gold),
        len(items) - len(gold),
        ctx.layout.gold,
    )
    return 0


def _judge(ctx: Context, args: argparse.Namespace) -> int:
    configured = ctx.settings.judges
    if unknown := sorted(set(args.judge or ()) - {j.name for j in configured}):
        raise ConfigError(f"no judge named {', '.join(unknown)} in the configuration")
    chosen = [j for j in configured if not args.judge or j.name in args.judge]
    providers = ctx.providers({j.provider for j in chosen})
    layout = ctx.layout
    passages = read_records(layout.passages, Passage)
    calls = run_judging(
        items=read_records(layout.items, Item),
        passages={passage.id: passage for passage in passages},
        judges=[Judge(settings, providers[settings.provider]) for settings in chosen],
        runs=ctx.settings.judging.runs,
        existing=read_records_if_present(layout.judge_results, JudgeResult),
        prompts=load_prompts(layout.prompts_dir),
        now=ctx.now,
        sink=lambda result: append_record(layout.judge_results, result),
    )
    log.info("event=judge_done new_calls=%d path=%s", calls, layout.judge_results)
    return 0


def _shown(path: Path, base: Path) -> str:
    """`path` relative to the configuration's directory when it lies inside it."""
    resolved = path.resolve()
    return str(resolved.relative_to(base)) if resolved.is_relative_to(base) else str(path)


def _rater_spec(text: str) -> tuple[str, Path]:
    name, separator, path = text.partition("=")
    if not separator or not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError(
            f"{text!r}: a rater is NAME=PATH, such as second=labels/second.jsonl"
        )
    return name.strip(), Path(path.strip())


def _score(ctx: Context, args: argparse.Namespace) -> int:
    layout, scoring = ctx.layout, ctx.settings.scoring
    base = args.config.resolve().parent
    gold_path, out = args.gold or layout.gold, args.out or layout.scores
    raters = [
        Rater(name, _shown(path, base), read_records(path, GoldLabel))
        for name, path in args.rater or ()
    ]
    passages = read_records(layout.passages, Passage)
    scores = score(
        read_records(layout.items, Item),
        read_records(gold_path, GoldLabel),
        read_records_if_present(layout.judge_results, JudgeResult),
        resamples=scoring.bootstrap_resamples,
        seed=scoring.seed,
        now=ctx.now,
        gold_file=_shown(gold_path, base),
        recent_change_passages=frozenset(p.id for p in passages if p.recent_change),
        raters=raters,
    )
    write_text_atomically(out, scores.model_dump_json(indent=2) + "\n")
    log.info(
        "event=scored figures=%d raters=%d gold=%s path=%s",
        len(scores.figures),
        len(raters),
        scores.gold_file,
        out,
    )
    return 0


def _report(ctx: Context, args: argparse.Namespace) -> int:
    path = args.out or ctx.layout.report
    write_text_atomically(
        path, render_report(read_model(args.scores or ctx.layout.scores, ScoreSet))
    )
    log.info("event=report_written path=%s", path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="meaning-evals", description=DESCRIPTION)
    parser.add_argument(
        "--config", type=Path, default=Path("config.toml"), help="default: config.toml"
    )
    parser.add_argument("--verbose", action="store_true", help="log at DEBUG level")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="generate items from approved passages")
    build.add_argument("--passage", action="append", help="(re)build only this passage id")
    build.add_argument(
        "--faithful-only",
        action="store_true",
        help="write only the faithful answers, to be checked before the other items exist",
    )
    build.add_argument(
        "--replace-duplicate-twins",
        action="store_true",
        help="regenerate only the near-miss twins that repeat another answer of their passage",
    )
    build.set_defaults(handler=_build)
    sheet = commands.add_parser("worksheet", help="write the blind labelling worksheet")
    sheet.add_argument("--out", type=Path, help="where to write the HTML file")
    sheet.set_defaults(handler=_worksheet)
    gold = commands.add_parser("import-gold", help="import the worksheet's exported labels")
    gold.add_argument("export", type=Path, help="the JSON file the worksheet exported")
    gold.set_defaults(handler=_import_gold)
    judge = commands.add_parser("judge", help="run every judge over every item")
    judge.add_argument("--judge", action="append", help="run only this judge (repeatable)")
    judge.set_defaults(handler=_judge)
    scoring = commands.add_parser("score", help="compute every figure")
    scoring.add_argument("--gold", type=Path, help="the gold labels (default: data/gold.jsonl)")
    scoring.add_argument(
        "--rater",
        action="append",
        type=_rater_spec,
        metavar="NAME=PATH",
        help="also score labels in the gold format as a rater named NAME (repeatable)",
    )
    scoring.add_argument("--out", type=Path, help="where to write the scores JSON")
    scoring.set_defaults(handler=_score)
    report = commands.add_parser("report", help="write the Markdown results table")
    report.add_argument("--scores", type=Path, help="the scores JSON to report")
    report.add_argument("--out", type=Path, help="where to write the Markdown file")
    report.set_defaults(handler=_report)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    provider_factory: ProviderFactory = make_provider,
    now: Callable[[], datetime] = utc_now,
) -> int:
    args = _parser().parse_args(argv)
    configure_logging(uuid.uuid4().hex[:12], verbose=args.verbose)
    log.info("event=command_started command=%s config=%s", args.command, args.config)
    try:
        settings = load_settings(args.config)
        layout = Layout.resolve(settings.paths, args.config.resolve().parent)
        context = Context(
            settings, layout, os.environ if environ is None else environ, provider_factory, now
        )
        status: int = args.handler(context, args)
    except MeaningEvalsError as exc:
        log.error(
            "event=command_failed command=%s error_type=%s error=%s",
            args.command,
            type(exc).__name__,
            exc,
        )
        return EXIT_FAILURE
    return status
