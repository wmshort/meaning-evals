# meaning-evals

An evaluation of model judges on one task: given a passage of official guidance, a
question about it and an answer, decide whether the answer departs from what the passage
means, and if it does, by which mechanism. Each divergent answer differs from a faithful
answer by one edit that changes its meaning; each near-miss twin rewords the same sentence
without changing it. The question is whether a judge separates the two. The construct is
faithfulness to a governing text: the judge has the source in front of it, and nothing is
measured about what any model believes.

## Items

Twelve passages of GOV.UK guidance (103 to 227 words each, retrieved on 2026-09-25 and used
under the Open Government Licence v3.0) on holiday notice, redundancy notice pay, parking
penalty challenges, flexible-working decisions, Statutory Sick Pay, Winter Fuel Payment
eligibility, Self Assessment penalties, Council Tax for students, tenancy deposits, jury
eligibility, MOT validity and school-attendance fines. Three of them state rules that
changed in 2026, which a judge may not have learned in training.

Each passage has one question a member of the public might ask, and nine answers of two to
four sentences, all written by `gemini-3.8-flash` from the passage:

- a **faithful answer**;
- four **divergent answers**, each a copy of the faithful answer with one edit made by one
  of the passage's four assigned mechanisms;
- four **near-miss twins**, each rewording the sentence its divergent partner edits,
  without changing what it means.

That gives 108 items: 12 faithful answers, 48 divergent answers (eight per mechanism) and
48 twins. Every item, with its passage and question, is in `data/`. The mechanisms, defined
as the judges are given them:

| Mechanism | Definition |
|---|---|
| Deontic reversal | An obligation and a permission are swapped: a *may* becomes a *must*, or the reverse. |
| Condition omission | A condition the guidance attaches is dropped, so something the guidance makes conditional is stated without its condition. |
| Temporal-condition reversal | The *when* is changed: the timing or order the guidance sets (*before*, *after*, *within*, *until*) is altered. |
| Scope shift | Who or what the guidance covers is changed: a *some* is widened to an *all*. |
| Quantitative divergence | A number, limit, amount or deadline differs from the one the guidance gives. |
| Polarity reversal | What the guidance denies is asserted, or what it asserts is denied. |

In the labels, a limiting requirement removed outright is a scope shift; a quantitative
divergence gives a different number.

## Labels

One annotator, the author (William Short, a cognitive linguist), labelled every item: whether
the answer diverges and, if it does, the mechanism, the span of the answer that carries it,
and a rationale quoting the passage. The annotator confirmed each faithful answer against
its passage before the other items were generated, and labelled all 108 items in a shuffled
order that showed nothing about how any answer was made. The 22 labels that then disagreed
with the design (16 on whether the answer diverges, 6 on the mechanism) were re-examined with
the judges' outputs in view, and 21 were corrected. The labels in `data/gold.jsonl` are the
reference for every figure below. Of the 48 edits written to diverge, the annotator judges
47 to change the meaning; the remaining one drops a clause the context already supplies.

## Judges

| Judge | Provider | Model | Reasoning effort |
|---|---|---|---|
| `claude` | Anthropic | `claude-sonnet-5` | `high` |
| `gpt` | OpenAI | `gpt-6-sol` | `high` |
| `gpt-astra` | OpenAI | `gpt-6-astra` | `high` |
| `gemini` | Google | `gemini-3.8-flash` | provider default |

Each judge sees the passage, the question, the answer and the six definitions
(`prompts/judge_system.txt`, `prompts/judge.txt`), and returns structured JSON: whether the
answer diverges, the mechanism, and the shortest span of the answer that carries the
divergence. Every judge ran twice over all 108 items at its provider's default sampling, on
2026-09-25 (`gpt`, `gpt-astra`, `gemini`) and 2026-09-26 (`claude`). Every response reported
the model id requested, and none was malformed. `gemini` judges answers written by its own
model; the other three come from other providers.

## Metrics

For each judge and run, overall and for each mechanism: precision and recall against the
labels; the false-alarm rate on the twins, on the faithful answers and on all non-divergent
items, with the passages whose rules changed in 2026 also reported apart; Cohen's κ against
the labels, on the yes/no verdict and on the seven-way label (six mechanisms or none); and
the rate at which the quoted span occurs verbatim in the answer. For each judge, κ between
its two runs; for each pair of judges, κ between them beside each one's κ against the
labels. The difference between judge–judge κ and the mean judge–label κ tests whether the
judges share an error the labels do not.

Proportions carry exact 95% Clopper–Pearson intervals. κ and the differences carry 95%
percentile bootstrap intervals over items (10,000 resamples, fixed seed, shared by every
figure so that differences are paired).

## Results

| Judge | Divergences found, of 47 | False alarms, of 61 | κ, diverges or not | κ, mechanism (run 1, run 2) |
|---|---|---|---|---|
| `gpt-6-sol` | 47, recall 1.00 [0.92, 1.00] | 0, rate 0.00 [0.00, 0.06] | 1.00 | 0.97 [0.93, 1.00], 0.97 |
| `gpt-6-astra` | 47, recall 1.00 [0.92, 1.00] | 0, rate 0.00 [0.00, 0.06] | 1.00 | 0.99 [0.95, 1.00], 0.99 |
| `gemini-3.8-flash` | 47, recall 1.00 [0.92, 1.00] | 0, rate 0.00 [0.00, 0.06] | 1.00 | 0.97 [0.93, 1.00], 0.97 |
| `claude-sonnet-5` | 46, recall 0.98 [0.89, 1.00] | 0, rate 0.00 [0.00, 0.06] | 0.98 [0.94, 1.00] | 0.93 [0.86, 0.98], 0.90 [0.82, 0.96] |

Both runs of every judge gave the same yes/no verdict on every item; the only difference
between runs is Claude's mechanism on two items.

- **Twins.** No judge flagged any of the 48 near-miss twins in either run (upper bound
  0.07 per run). The judges responded to changes of meaning, not to edits as such.
- **Misses.** Claude passed `flexible-working-decision-90f5dc0cf4` in both runs, an answer
  that shortens the refusal ground "extra costs that will damage the business" to "extra
  costs". No other judge missed a divergence.
- **Mechanisms.** Where a judge's mechanism differs from the label, the edit sits between
  two categories, as when dropping a condition also widens who the guidance covers. Scope
  shift is the least consistently named: judges gave that name to 3 to 6 of its 7 cases.
- **Shared error.** Judge–judge κ minus mean judge–label κ is 0.00 for every pair of the
  three judges without a miss, and −0.01 for each pair that includes Claude.
- **Changed rules.** No judge flagged any of the 15 non-divergent items from the passages
  whose rules changed in 2026 (upper bound 0.22).
- **Same family, stronger model.** `gemini` judged answers its own model wrote no better
  than the other judges did, and `gpt-6-astra` detected nothing `gpt-6-sol` missed. At this
  ceiling neither comparison can show a difference.

Every figure, per run and per mechanism, with its interval and n, is in `results/report.md`.

## Limitations

- **The task is saturated.** Each divergence is one edit, in an answer of two to four
  sentences, against a passage the judge is given. The results show that these judges find
  such an edit and leave meaning-preserving rewordings alone. They say nothing about long
  answers, several divergences in one answer, divergences that depend on implicature, or
  outputs not written to diverge, and the items cannot rank the four judges.
- **The labels come from one annotator,** and the corrected labels were made with the
  judges' outputs in view. The labels agree with the judges' majority verdict on every
  item, so the reference is not independent of the judges. Each label's rationale quotes
  the passage it rests on, so each can be checked against the source.
- **The judges are told the six mechanisms.** Detection here is classification into a
  given set, not open-ended discovery.
- **One generator wrote every answer,** and the same model is one of the judges.
- **Scope.** 108 items from twelve passages of one source, in English. Every model ran at
  its provider's default sampling, twice.

## Reproducing the results

The code needs Python 3.12 and [uv](https://docs.astral.sh/uv/). Scoring and reporting use
only the committed data and need no API key:

```sh
uv sync
uv run meaning-evals score     # writes results/scores.json
uv run meaning-evals report    # writes results/report.md
```

Re-running the judges calls the providers. Keys are read from the environment only
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`; see `.env.example`), and a command
stops before any call if a key it needs is missing. `judge` resumes where it stopped and
appends to `data/runs/judge-results.jsonl`; to run the judges afresh, move that file aside
first.

```sh
uv run meaning-evals judge                 # every judge in config.toml, two runs each
uv run meaning-evals judge --judge claude  # one judge
```

The same package builds a new item set from new passages: `build` generates the answers
(`--faithful-only` first, so the faithful answers can be checked before the rest exist),
`worksheet` writes a self-contained HTML page for labelling items blind, and `import-gold`
validates its export into `data/gold.jsonl`. `score --gold PATH` scores against another
label file, and `score --rater NAME=PATH` scores a second label file as one more rater
beside the judges. Models, efforts, timeouts and seeds are in `config.toml`; prompts are in
`prompts/`.

```sh
uv run pytest -q
uv run ruff check
uv run mypy src
```

No test touches the network.

## Repository layout

```
meaning-evals/
├── config.toml            # models, efforts, request limits, seeds, paths
├── prompts/               # generator and judge prompts
├── src/meaning_evals/     # the package and its command line
├── tests/
├── data/
│   ├── passages.jsonl     # the twelve passages, with source URL and retrieval date
│   ├── questions.jsonl    # one question per passage, with its four mechanisms
│   ├── items.jsonl        # the 108 answers, with the model that wrote each
│   ├── gold.jsonl         # the labels
│   └── runs/judge-results.jsonl  # every judge call: verdict, raw reply, model id, time
└── results/
    ├── scores.json        # every figure with its interval and n
    └── report.md          # the same figures as tables
```

## Licence

The code is released under the [MIT licence](LICENSE). The questions, answers, labels and
judge results in `data/` are released under CC BY 4.0 ([`data/LICENSE`](data/LICENSE)). The
passages remain under the Open Government Licence v3.0, and every passage record carries the
statement *Contains public sector information licensed under the Open Government Licence
v3.0.*
