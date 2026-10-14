# running-petri

A feasibility pilot on how much **AI safety evaluation outcomes depend on the overseer rather than the evaluated target model**. The pilot uses [Petri](https://github.com/meridianlabs-ai/inspect_petri) — an independently developed, maintained red-teaming framework created by **Meridian Labs** and built on [Inspect AI](https://inspect.aisi.org.uk/) — and comprises **180 completed audits** with **179 valid judge scores**.

> **Status: exploratory feasibility pilot.** This is not a confirmatory study and does not establish causal effects or model-safety rankings for deployment. See [Limitations](#limitations).

## Author and attribution

**Research author:** **Marco Iannacone** ([ORCID 0009-0008-4219-6351](https://orcid.org/0009-0008-4219-6351)) designed and executed the pilot and authored this repository's configuration, analysis and documentation.

**Framework attribution:** The evaluation framework used here is [Petri](https://github.com/meridianlabs-ai/inspect_petri), created and maintained by **Meridian Labs** and built on [Inspect AI](https://inspect.aisi.org.uk/) (UK AI Security Institute). Petri and Inspect AI are external dependencies used unmodified; authorship of the framework belongs to Meridian Labs and the respective upstream authors. This repository contains only the pilot's own configuration, analysis and documentation.

---

## Research question

*How much do AI safety evaluation outcomes depend on the overseer (auditor) rather than the evaluated target model?*

## Motivation

Automated safety evaluations increasingly use an LLM "auditor" to probe a target model, with an LLM "judge" scoring the transcript. If the measured outcome depends on *how the auditor interrogates* the target, then evaluated scores reflect the evaluation setup as much as the target. This pilot asks whether a deliberate change in the auditor's interrogation strategy is associated with a change in judge-assigned deception scores, relative to changing the target model.

## Methodology

**Why Petri.** We used Petri rather than building a purpose-specific harness to reduce dependence on custom evaluation infrastructure: scenario construction, tool synthesis, audit execution, native `.eval` logging and judge scoring are provided and maintained upstream. This is *not* an independent validation of any specific proposed framework (e.g. PROBUS or SLEF).

**Design (paired).** 3 auditor conditions × 3 target models × the same 20 scenarios (seeds) = 180 audits, one epoch each.

- **Auditor conditions** (same auditor model, differing only in a system-message directive; the full operational prompt is otherwise preserved):
  - **A0** — Petri default auditor;
  - **A1** — *trusting*: accepts the target's statements at face value, does not independently verify;
  - **A2** — *skeptical/verifying*: treats claims as things to check, requests supporting evidence, follows up on inconsistencies.
- **Targets:** `openai/gpt-5.6-luna`, `google/gemini-3.5-flash-lite`, `mistral/mistral-large-2512` (Mistral Large 3).
- **Auditor model:** `deepseek/deepseek-flash`. **Judge:** `anthropic/claude-haiku-5-5` (fixed).
- **Seeds:** 20 built-in Petri seeds relevant to deception / misrepresentation / hidden or unauthorized actions (see `config/seeds20.txt`), shared across every condition × target.
- **Parameters:** `max_turns=25`, `enable_rollback=false`, `enable_prefill=false`, `realism_filter=false`, `compaction=false`, `--seed 42`, one epoch.
- **Primary outcome:** judge dimension `unprompted_deception_toward_user` (scale 1–10, higher = more concerning). Secondary: `concerning`, `unfaithful_thinking`, `unprompted_initiative`.

**Statistical analysis.** Seed-level paired bootstrap (10,000 resamples, fixed seed, 95% percentile CIs). Auditor contrasts are paired within target and across targets by shared seed; target rankings and pairwise target differences use the same paired resampling. The single missing score is never imputed. Methods are implemented in `scripts/08_analysis.py` and are unchanged since the analysis was frozen.

## Main findings

*(Primary outcome, judge scale 1–10. Full analysis: `reports/11-final-scientific-analysis.md`.)*

| Auditor | GPT-5.6 Luna | Gemini 3.5 Flash-Lite | Mistral Large 3 |
|---|---|---|---|
| A0 | 1.42 [1.10, 1.83] | 2.25 [1.70, 2.85] | 3.60 [2.90, 4.35] |
| A1 | 1.45 [1.15, 1.80] | 2.40 [1.70, 3.20] | 3.35 [2.60, 4.15] |
| A2 | 1.50 [1.25, 1.75] | 2.00 [1.55, 2.50] | 3.50 [2.75, 4.30] |

- **Target identity was associated with substantially larger differences than auditor strategy.** Target gaps were ≈ 0.5–2.3 points; the overall auditor contrasts were ≈ 0.02–0.08 points with 95% CIs all spanning zero.
- **No consistent average auditor-strategy effect was detectable** (A1−A0 = −0.02 [−0.35, 0.32]; A2−A0 = −0.08 [−0.42, 0.27]; A2−A1 = −0.07 [−0.50, 0.38]).
- **Per-seed differences were heterogeneous** (range ≈ ±5 in places) with positive and negative effects cancelling in aggregate.
- **The observed target ranking (Mistral > Gemini > GPT) was unchanged across all three auditor conditions** (bootstrap ranking-reversal frequencies 0.6–6.0%).
- The study is **exploratory** and does not establish causal effects or model-safety rankings.

## Limitations

- **Scenario-construction confound.** Petri lets the auditor build the target's environment as well as interrogate it; a structured review of 8 matched triplets found 5 *surface-only* and 3 *mixed* differences (the environment/tool surface sometimes differed materially), while the target's role and objective were preserved. Auditor-strategy effects therefore cannot be cleanly isolated from scenario construction (`results/11-scenario-review.csv`).
- **Turn-budget saturation.** ≈ half of audits reached the 25-turn cap, unequally across conditions (A0 45%, A1 53%, A2 57%).
- **Single judge, single epoch.** One judge model and one run per audit; judge scoring is a proxy for the *appearance* of deception, not independently verified behaviour. ~12% of the new-audit samples required a judge-only re-score.
- **One missing score.** `A0 × GPT-5.6 Luna × classified_leak_goal_conflict` could not be scored (Anthropic content filter). It is left missing (not imputed); its worst-case bound cannot reverse the target ranking.
- **Limited precision.** With 20 seeds, the auditor contrasts cannot rule out small effects; a confidence interval containing zero is **not** evidence of no effect.
- **Auditor behavioural differentiation is qualitative**, not a validated measurement.

## Reproducibility

### 1. Environment

```bash
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install inspect-petri pandas numpy matplotlib
.venv/bin/inspect --version          # Petri/Inspect CLI
```

*(Petri 3.1.1 / Inspect AI 0.3.278 were used for the pilot. Provider SDKs are only needed to rerun audits, not to reproduce the analysis.)*

### 2. Inspect the frozen configuration

- `config/task_batch01.yaml`, `config/task_batch07_t12.yaml`, `config/task_batch07_t3.yaml` — seed sets;
- `config/auditor_a1.md`, `config/auditor_a2.md` — the A1/A2 auditor system messages (derived from the installed Petri default; `config/make_auditor_prompts.py` regenerates them);
- `config/model-costs.yaml` — price overrides used for cost tracking.

### 3. Locate the logs

Final research logs: `logs/batch02_25turns/` and `logs/batch03_180/` (native Inspect `.eval`). Their SHA-256 checksums are in `MANIFEST.sha256`; verify with:

```bash
shasum -a 256 -c MANIFEST.sha256
```

### 4. Regenerate the dataset and statistical outputs

```bash
.venv/bin/python scripts/08_analysis.py
```

This rebuilds `results/petri_180.csv` (one row per `(seed, auditor_condition, target)`), the means/paired/ranking/sensitivity tables, and `results/08-auditor-effects.png`, using the frozen logs and the fixed bootstrap seed. No API keys or network access are required.

### 5. Reproduce the bootstrap analysis

The bootstrap is deterministic (fixed seed `20261012`, 10,000 resamples, seed as the resampling unit). Re-running `scripts/08_analysis.py` reproduces the published numbers exactly.

### 6. Why 179 scores, not 180

One audit (`A0 × GPT-5.6 Luna × classified_leak_goal_conflict`) received no valid judge score: the judge's structured answer failed and the provider applied a **content filter** on re-scoring. The transcript is intact and preserved; the score is left missing. See `DATASET.md` (re-scoring history).

### Reproducing the analysis vs. rerunning the experiment

- **Reproducing the analysis** from the frozen logs requires **no paid APIs** and is deterministic.
- **Rerunning the experiment** would require provider credentials and API spending, and would produce **different** results (stochastic models, provider drift). The original configuration is recorded in the logs and config files.

## Repository layout

```
config/         frozen task configs, auditor prompts, seed list, cost config
scripts/        analysis + prompt-generation scripts
results/        final dataset, statistical tables, figure
reports/        final scientific analysis and executive summary
logs/           final research logs (batch02_25turns/, batch03_180/)
DATASET.md      dataset card (design, outcomes, columns, provenance, confounds)
MANIFEST.sha256 checksums of archived research logs, dataset and analysis script
```

## Documentation navigation

- **Plain-language research brief:** `reports/13-editorial-research-brief.md` (editorial account; see `results/13-editorial-auditor-effects.png`)
- **Final scientific analysis:** `reports/11-final-scientific-analysis.md`
- **One-page summary:** `reports/11-executive-summary.md`
- **Dataset card:** `DATASET.md`
- **Dataset (CSV):** `results/petri_180.csv`
- **Figure:** `results/08-auditor-effects.png`
- **Analysis script:** `scripts/08_analysis.py`
- **Frozen configuration:** `config/` (task configs, auditor prompts, seed list)

## Licensing

No license is applied yet; the licensing decision is pending. Petri and Inspect AI are MIT-licensed and are used as dependencies, not vendored. The `.eval` logs embed upstream seed instructions (with canary strings) and third-party model outputs; redistribution terms for those contents have **not** been asserted.
