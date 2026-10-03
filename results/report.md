# meaning-evals results

Scored 2026-10-03T14:25:33.291856+00:00 on 108 items with a gold label (108 items built, 108 gold labels), against the gold labels in `data/gold.jsonl`.

Each cell reads `estimate [low, high] n=N`, where N is the number of items the figure is computed on. A proportion (precision, recall, a false-alarm or quote rate) carries an exact Clopper-Pearson interval; κ and the agreement differences carry a percentile bootstrap interval over items (10000 resamples, seed 20260925). Both are 95% intervals. `n/a` marks a figure that is undefined at that N. Malformed judge responses are counted, not scored.

## Judges and the models their responses reported

| Judge | Requested model | Model id reported by the responses | Temperature | Effort | Run | Calls | Malformed |
|---|---|---|---|---|---|---|---|
| claude | claude-sonnet-5 | claude-sonnet-5 | not set | high | 1 | 108 | 0 |
| claude | claude-sonnet-5 | claude-sonnet-5 | not set | high | 2 | 108 | 0 |
| gemini | gemini-3.8-flash | gemini-3.8-flash | not set | not set | 1 | 108 | 0 |
| gemini | gemini-3.8-flash | gemini-3.8-flash | not set | not set | 2 | 108 | 0 |
| gpt | gpt-6-sol | gpt-6-sol | not set | high | 1 | 108 | 0 |
| gpt | gpt-6-sol | gpt-6-sol | not set | high | 2 | 108 | 0 |
| gpt-astra | gpt-6-astra | gpt-6-astra | not set | high | 1 | 108 | 0 |
| gpt-astra | gpt-6-astra | gpt-6-astra | not set | high | 2 | 108 | 0 |

## Detection against the expert's labels

| Judge (reported model) | Run | Precision | Recall | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | False alarms: recently changed guidance | False alarms: other guidance | κ, diverges or not | κ, mechanism | Quote found |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 1.00 [0.92, 1.00] n=46 | 0.98 [0.89, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 0.98 [0.94, 1.00] n=108 | 0.93 [0.86, 0.98] n=108 | 1.00 [0.92, 1.00] n=46 |
| claude (claude-sonnet-5) | 2 | 1.00 [0.92, 1.00] n=46 | 0.98 [0.89, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 0.98 [0.94, 1.00] n=108 | 0.90 [0.82, 0.96] n=108 | 1.00 [0.92, 1.00] n=46 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |
| gpt (gpt-6-sol) | 1 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |
| gpt (gpt-6-sol) | 2 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.92, 1.00] n=47 | 1.00 [0.92, 1.00] n=47 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.00 [0.00, 0.22] n=15 | 0.00 [0.00, 0.08] n=46 | 1.00 [1.00, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | 1.00 [0.92, 1.00] n=47 |

## By mechanism

### Deontic reversal

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| claude (claude-sonnet-5) | 2 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt (gpt-6-sol) | 1 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gpt (gpt-6-sol) | 2 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |

### Condition omission

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 0.88 [0.47, 1.00] n=8 | 0.88 [0.47, 1.00] n=8 | 0.88 [0.47, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.87 [0.59, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| claude (claude-sonnet-5) | 2 | 0.78 [0.40, 0.97] n=9 | 0.88 [0.47, 1.00] n=8 | 0.88 [0.47, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.81 [0.52, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt (gpt-6-sol) | 1 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gpt (gpt-6-sol) | 2 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |

### Temporal-condition reversal

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| claude (claude-sonnet-5) | 2 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| gpt (gpt-6-sol) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt (gpt-6-sol) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 1 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |
| gpt-astra (gpt-6-astra) | 2 | 0.89 [0.52, 1.00] n=9 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.94 [0.76, 1.00] n=108 | 1.00 [0.66, 1.00] n=9 |

### Scope shift

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 1.00 [0.40, 1.00] n=4 | 0.57 [0.18, 0.90] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.71 [0.27, 1.00] n=108 | 1.00 [0.40, 1.00] n=4 |
| claude (claude-sonnet-5) | 2 | 1.00 [0.29, 1.00] n=3 | 0.43 [0.10, 0.82] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.58 [0.00, 0.90] n=108 | 1.00 [0.29, 1.00] n=3 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |
| gpt (gpt-6-sol) | 1 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |
| gpt (gpt-6-sol) | 2 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.54, 1.00] n=6 | 0.86 [0.42, 1.00] n=7 | 1.00 [0.59, 1.00] n=7 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.92 [0.66, 1.00] n=108 | 1.00 [0.54, 1.00] n=6 |

### Quantitative divergence

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| claude (claude-sonnet-5) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gemini (gemini-3.8-flash) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gemini (gemini-3.8-flash) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt (gpt-6-sol) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt (gpt-6-sol) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |

### Polarity reversal

| Judge (reported model) | Run | Precision | Recall | Detected, any mechanism | False alarms: near-miss twins | False alarms: faithful answers | False alarms: all non-divergent | κ, this mechanism or not | Quote found |
|---|---|---|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) | 1 | 0.73 [0.39, 0.94] n=11 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.83 [0.58, 1.00] n=108 | 1.00 [0.72, 1.00] n=11 |
| claude (claude-sonnet-5) | 2 | 0.70 [0.35, 0.93] n=10 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.76 [0.47, 0.95] n=108 | 1.00 [0.69, 1.00] n=10 |
| gemini (gemini-3.8-flash) | 1 | 0.80 [0.44, 0.97] n=10 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.88 [0.65, 1.00] n=108 | 1.00 [0.69, 1.00] n=10 |
| gemini (gemini-3.8-flash) | 2 | 0.80 [0.44, 0.97] n=10 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.88 [0.65, 1.00] n=108 | 1.00 [0.69, 1.00] n=10 |
| gpt (gpt-6-sol) | 1 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| gpt (gpt-6-sol) | 2 | 1.00 [0.59, 1.00] n=7 | 0.88 [0.47, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 0.93 [0.73, 1.00] n=108 | 1.00 [0.59, 1.00] n=7 |
| gpt-astra (gpt-6-astra) | 1 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |
| gpt-astra (gpt-6-astra) | 2 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 1.00 [0.63, 1.00] n=8 | 0.00 [0.00, 0.07] n=48 | 0.00 [0.00, 0.26] n=12 | 0.00 [0.00, 0.06] n=61 | 1.00 [1.00, 1.00] n=108 | 1.00 [0.63, 1.00] n=8 |

## Self-agreement: run 1 against run 2

Difference is the agreement between the two raters minus the mean of their agreements with the expert, on the same items and resamples. A positive difference means they agree with each other more than with the expert.

| Judges | Run | Labels compared | κ, run 1 and run 2 | κ, run 1 and gold | κ, run 2 and gold | Difference |
|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) |  | diverges or not | 1.00 [1.00, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 0.02 [0.00, 0.06] n=108 |
| claude (claude-sonnet-5) |  | mechanism (seven labels) | 0.97 [0.93, 1.00] n=108 | 0.93 [0.86, 0.98] n=108 | 0.90 [0.82, 0.96] n=108 | 0.06 [-0.00, 0.13] n=108 |
| claude (claude-sonnet-5) |  | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| claude (claude-sonnet-5) |  | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 0.87 [0.59, 1.00] n=108 | 0.81 [0.52, 1.00] n=108 | 0.10 [-0.07, 0.35] n=108 |
| claude (claude-sonnet-5) |  | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.07 [0.00, 0.27] n=108 |
| claude (claude-sonnet-5) |  | Scope shift or not | 0.85 [0.00, 1.00] n=108 | 0.71 [0.27, 1.00] n=108 | 0.58 [0.00, 0.90] n=108 | 0.20 [-0.21, 0.62] n=108 |
| claude (claude-sonnet-5) |  | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) |  | Polarity reversal or not | 0.95 [0.81, 1.00] n=108 | 0.83 [0.58, 1.00] n=108 | 0.76 [0.47, 0.95] n=108 | 0.15 [-0.04, 0.42] n=108 |
| gemini (gemini-3.8-flash) |  | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) |  | mechanism (seven labels) | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.03 [0.00, 0.07] n=108 |
| gemini (gemini-3.8-flash) |  | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) |  | Condition omission or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) |  | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.07 [0.00, 0.27] n=108 |
| gemini (gemini-3.8-flash) |  | Scope shift or not | 1.00 [1.00, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.08 [0.00, 0.34] n=108 |
| gemini (gemini-3.8-flash) |  | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) |  | Polarity reversal or not | 1.00 [1.00, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 0.12 [0.00, 0.35] n=108 |
| gpt (gpt-6-sol) |  | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) |  | mechanism (seven labels) | 1.00 [1.00, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.03 [0.00, 0.07] n=108 |
| gpt (gpt-6-sol) |  | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.06 [0.00, 0.24] n=108 |
| gpt (gpt-6-sol) |  | Condition omission or not | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.06 [0.00, 0.24] n=108 |
| gpt (gpt-6-sol) |  | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) |  | Scope shift or not | 1.00 [1.00, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.08 [0.00, 0.34] n=108 |
| gpt (gpt-6-sol) |  | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) |  | Polarity reversal or not | 1.00 [1.00, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.07 [0.00, 0.27] n=108 |
| gpt-astra (gpt-6-astra) |  | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt-astra (gpt-6-astra) |  | mechanism (seven labels) | 1.00 [1.00, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | 0.01 [0.00, 0.05] n=108 |
| gpt-astra (gpt-6-astra) |  | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt-astra (gpt-6-astra) |  | Condition omission or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt-astra (gpt-6-astra) |  | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.06 [0.00, 0.24] n=108 |
| gpt-astra (gpt-6-astra) |  | Scope shift or not | 1.00 [1.00, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.08 [0.00, 0.34] n=108 |
| gpt-astra (gpt-6-astra) |  | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt-astra (gpt-6-astra) |  | Polarity reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |

## Judge against judge

Difference is the agreement between the two raters minus the mean of their agreements with the expert, on the same items and resamples. A positive difference means they agree with each other more than with the expert.

| Judges | Run | Labels compared | κ, the two judges | κ, first judge and gold | κ, second judge and gold | Difference |
|---|---|---|---|---|---|---|
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | mechanism (seven labels) | 0.96 [0.90, 1.00] n=108 | 0.93 [0.86, 0.98] n=108 | 0.97 [0.93, 1.00] n=108 | 0.01 [-0.04, 0.06] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Condition omission or not | 0.87 [0.59, 1.00] n=108 | 0.87 [0.59, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.07 [-0.20, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.07 [0.00, 0.27] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Scope shift or not | 0.79 [0.32, 1.00] n=108 | 0.71 [0.27, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.03 [-0.29, 0.24] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 1 | Polarity reversal or not | 0.95 [0.81, 1.00] n=108 | 0.83 [0.58, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 0.09 [-0.06, 0.31] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | mechanism (seven labels) | 0.93 [0.86, 0.98] n=108 | 0.90 [0.82, 0.96] n=108 | 0.97 [0.93, 1.00] n=108 | -0.01 [-0.06, 0.05] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Condition omission or not | 0.81 [0.52, 1.00] n=108 | 0.81 [0.52, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.10 [-0.24, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Temporal-condition reversal or not | 1.00 [1.00, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.07 [0.00, 0.27] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Scope shift or not | 0.65 [0.00, 1.00] n=108 | 0.58 [0.00, 0.90] n=108 | 0.92 [0.66, 1.00] n=108 | -0.10 [-0.43, 0.20] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gemini (gemini-3.8-flash) | 2 | Polarity reversal or not | 0.89 [0.68, 1.00] n=108 | 0.76 [0.47, 0.95] n=108 | 0.88 [0.65, 1.00] n=108 | 0.07 [-0.12, 0.31] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | mechanism (seven labels) | 0.93 [0.86, 0.98] n=108 | 0.93 [0.86, 0.98] n=108 | 0.97 [0.93, 1.00] n=108 | -0.02 [-0.06, 0.02] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 0.87 [0.59, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.04 [-0.10, 0.23] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Temporal-condition reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Scope shift or not | 0.79 [0.32, 1.00] n=108 | 0.71 [0.27, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.03 [-0.28, 0.24] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 1 | Polarity reversal or not | 0.76 [0.47, 0.95] n=108 | 0.83 [0.58, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | -0.12 [-0.25, -0.03] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | mechanism (seven labels) | 0.93 [0.86, 0.98] n=108 | 0.90 [0.82, 0.96] n=108 | 0.97 [0.93, 1.00] n=108 | -0.01 [-0.06, 0.05] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.06 [0.00, 0.24] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Condition omission or not | 0.88 [0.65, 1.00] n=108 | 0.81 [0.52, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 0.01 [-0.16, 0.21] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Temporal-condition reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Scope shift or not | 0.65 [0.00, 1.00] n=108 | 0.58 [0.00, 0.90] n=108 | 0.92 [0.66, 1.00] n=108 | -0.10 [-0.43, 0.20] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt (gpt-6-sol) | 2 | Polarity reversal or not | 0.81 [0.53, 1.00] n=108 | 0.76 [0.47, 0.95] n=108 | 0.93 [0.73, 1.00] n=108 | -0.03 [-0.20, 0.14] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | mechanism (seven labels) | 0.93 [0.86, 0.98] n=108 | 0.93 [0.86, 0.98] n=108 | 0.99 [0.95, 1.00] n=108 | -0.03 [-0.06, -0.01] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Condition omission or not | 0.87 [0.59, 1.00] n=108 | 0.87 [0.59, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.07 [-0.20, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Temporal-condition reversal or not | 0.87 [0.60, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.07 [-0.19, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Scope shift or not | 0.79 [0.32, 1.00] n=108 | 0.71 [0.27, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.03 [-0.28, 0.24] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 1 | Polarity reversal or not | 0.83 [0.58, 1.00] n=108 | 0.83 [0.58, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.09 [-0.21, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | diverges or not | 0.98 [0.94, 1.00] n=108 | 0.98 [0.94, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.01 [-0.03, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | mechanism (seven labels) | 0.90 [0.82, 0.96] n=108 | 0.90 [0.82, 0.96] n=108 | 0.99 [0.95, 1.00] n=108 | -0.04 [-0.08, -0.01] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Condition omission or not | 0.81 [0.52, 1.00] n=108 | 0.81 [0.52, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.10 [-0.24, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Temporal-condition reversal or not | 0.87 [0.60, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.07 [-0.19, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Scope shift or not | 0.65 [0.00, 1.00] n=108 | 0.58 [0.00, 0.90] n=108 | 0.92 [0.66, 1.00] n=108 | -0.10 [-0.43, 0.20] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| claude (claude-sonnet-5) / gpt-astra (gpt-6-astra) | 2 | Polarity reversal or not | 0.76 [0.47, 0.95] n=108 | 0.76 [0.47, 0.95] n=108 | 1.00 [1.00, 1.00] n=108 | -0.12 [-0.27, -0.03] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | mechanism (seven labels) | 0.94 [0.89, 0.99] n=108 | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | -0.03 [-0.06, -0.01] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Temporal-condition reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Scope shift or not | 0.82 [0.48, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.09 [-0.30, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 1 | Polarity reversal or not | 0.81 [0.53, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | -0.09 [-0.22, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | mechanism (seven labels) | 0.94 [0.89, 0.99] n=108 | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | -0.03 [-0.06, -0.01] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Temporal-condition reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Scope shift or not | 0.82 [0.48, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.09 [-0.30, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt (gpt-6-sol) | 2 | Polarity reversal or not | 0.81 [0.53, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | -0.09 [-0.22, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | mechanism (seven labels) | 0.96 [0.90, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | -0.02 [-0.05, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Condition omission or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Temporal-condition reversal or not | 0.87 [0.60, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.07 [-0.19, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Scope shift or not | 0.82 [0.48, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.09 [-0.30, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 1 | Polarity reversal or not | 0.88 [0.65, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.06 [-0.17, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | mechanism (seven labels) | 0.96 [0.90, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | -0.02 [-0.05, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Deontic reversal or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Condition omission or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Temporal-condition reversal or not | 0.87 [0.60, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.07 [-0.19, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Scope shift or not | 0.82 [0.48, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | -0.09 [-0.30, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gemini (gemini-3.8-flash) / gpt-astra (gpt-6-astra) | 2 | Polarity reversal or not | 0.88 [0.65, 1.00] n=108 | 0.88 [0.65, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.06 [-0.17, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | mechanism (seven labels) | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | -0.01 [-0.02, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Temporal-condition reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Scope shift or not | 1.00 [1.00, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.08 [0.00, 0.34] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 1 | Polarity reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | diverges or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | mechanism (seven labels) | 0.97 [0.93, 1.00] n=108 | 0.97 [0.93, 1.00] n=108 | 0.99 [0.95, 1.00] n=108 | -0.01 [-0.02, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Deontic reversal or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Condition omission or not | 0.94 [0.76, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Temporal-condition reversal or not | 0.94 [0.76, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.94 [0.76, 1.00] n=108 | -0.03 [-0.12, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Scope shift or not | 1.00 [1.00, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.92 [0.66, 1.00] n=108 | 0.08 [0.00, 0.34] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Quantitative divergence or not | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | 0.00 [0.00, 0.00] n=108 |
| gpt (gpt-6-sol) / gpt-astra (gpt-6-astra) | 2 | Polarity reversal or not | 0.93 [0.73, 1.00] n=108 | 0.93 [0.73, 1.00] n=108 | 1.00 [1.00, 1.00] n=108 | -0.04 [-0.13, 0.00] n=108 |

## Where the expert and the generation intent disagree

The expert's label stands in every figure above.

| Item | Built as | Intended mechanism | Expert: diverges | Expert: mechanism |
|---|---|---|---|---|
| holiday-booking-72716a0ed7 | divergent | condition_omission | no | none |
| winter-fuel-eligibility-7ac52b3b97 | divergent | scope_shift | yes | condition_omission |
