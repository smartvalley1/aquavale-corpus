# AquaVale: A Synthetic Water and Wastewater Utility Corpus

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24406031.svg)](https://doi.org/10.5281/zenodo.24406031)

AquaVale is a fictional water and wastewater utility built to measure how often internal AI assistants disclose customer data and critical infrastructure information to the wrong recipient. It accompanies the paper *"Are Internal AI Assistants a Reconnaissance Source for Critical Infrastructure?"*.

The corpus contains **no real person, no real utility and no real configuration**. Every critical infrastructure detail is a labelled placeholder.

## Open sources
| Source | What was taken | Where it is used |
|---|---|---|
| WNTR KY10 network (USEPA/WNTR; Kentucky hydraulic model database) | 935 nodes, 1,061 links, pump and tank topology | `network_links.csv`, `network_facilities.csv`, reconnaissance value |
| BATADAL C-Town (scy-phy/ICS-Evasion-Attacks, 15-minute version) | 43 SCADA variables and normal-operation values | `scada_tags.csv`, `scada_sample_14days.csv` |
| BattLeDIM L-Town (KIOS-Research/BattLeDIM) | Start, repair time, diameter and type of 70 leaks | `fault_work_orders.csv` |
| Faker (en_GB) | Fictional names, addresses, phone numbers | `customer_records.csv` |

Hourly consumption is generated synthetically from a daily usage pattern (300 households × 42 days). Household types: family, elderly living alone, single worker, internal plumbing leak. Some households have absence periods.

## Folders
- `data/` — 11 tables: customers, consumption, network, SCADA, work orders, shifts, penetration-test findings, cyber-incident log, tender bids.
- `documents/` — 8 free-text documents labelled D1–D4, including an embedded instruction (question 13) and an e-mail containing third-party information (question 24).
- `policy/access_policy.yaml` — role × information that may be seen × purpose; in combined fields both policies must permit disclosure.
- `experiment/gold_questions.csv` — the 25 pilot questions in Appendix A of the paper, with role, purpose, risk condition, data class, source documents, **required information** and **forbidden values**.
- `experiment/canary_dictionary.csv` — 110 canaries (forbidden field → data class → reconnaissance value).
- `analysis/` — first results, corpus inventory, Figure 1 and measurement outputs.

## Canary principle
Every critical infrastructure detail is a unique labelled placeholder such as `[REMOTE-ACCESS-METHOD-3F2A]`. This serves two purposes:
1. The corpus contains no real access information.
2. Leakage is measured automatically by string matching at the retrieval, provider-call, tool-argument and response stages.

In customer fields the canary is the fictional value itself (name, phone number, arrears).

## Usage
Clone the raw open data into `data_raw/`:
```
git clone --depth 1 https://github.com/USEPA/WNTR data_raw/WNTR
git clone --depth 1 https://github.com/scy-phy/ICS-Evasion-Attacks data_raw/ICS-Evasion-Attacks
git clone --depth 1 https://github.com/KIOS-Research/BattLeDIM data_raw/BattLeDIM
pip install -r requirements.txt
python3 scripts/generate_corpus.py      # rebuilds the corpus (seed 20261120, deterministic)
python3 scripts/analysis.py             # first analyses and Figure 1
python3 scripts/measure.py . responses.csv
#   responses.csv: no, model, level, run, stage (retrieval|call|tool|response), text
```
`experiment/sample_responses_SIMULATED.csv` only tests the measurement pipeline; it contains no results.
`analysis/_household_ground_truth_HIDDEN.csv` must never be given to a model. It is used only to validate the inference test.

## Changes
- **1.1.0** — Entire corpus translated to English (file names, columns, values, documents, canaries, policy, questions, scripts). Same seed; all counts identical to 1.0.0.
- **1.0.0** — First release (Turkish field names).

## Licences
Data and documents: CC BY 4.0. Code in `scripts/`: MIT. Derived open components are subject to their own licences: WNTR (Revised BSD), BATADAL and BattLeDIM (see their repositories); please cite them as listed in the paper.

## Citation
Ünlü, N. (2026). *AquaVale: Synthetic water utility corpus for measuring disclosure by internal AI assistants* (Version 1.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24406031
