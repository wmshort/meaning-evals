# Changelog

Notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-03

### Added

- The `meaning_evals` package and command line (`build`, `worksheet`, `import-gold`,
  `judge`, `score`, `report`), with adapters for the Anthropic, OpenAI and Google APIs.
- 108 items from twelve GOV.UK passages, the labels, and the results of four judges, each
  run twice.
- Scoring per judge, run and mechanism: precision, recall, false-alarm rates, Cohen's κ,
  quote checks, run–run and judge–judge agreement, with exact intervals for proportions and
  paired bootstrap intervals for κ.
