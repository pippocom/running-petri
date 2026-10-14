# Report 11 — Final Scientific Analysis of the Petri Feasibility Pilot

- **Date (UTC):** 2026-10-12
- **Scope:** definitive analysis of the 180-audit Petri pilot. **No new audits, no paid API calls, no imputation.**
- **Dataset:** 180 completed audits, **179 valid judge scores**, 1 permanently missing (`A0 × GPT-5.6 Luna × classified_leak_goal_conflict`, Anthropic content filter).
- **Design:** 3 auditor conditions (A0 default, A1 trusting, A2 skeptical) × 3 targets (GPT-5.6 Luna, Gemini 3.5 Flash-Lite, Mistral Large 3) × 20 shared seeds; fixed judge (Claude Haiku 5.5); `max_turns=25`.
- **Reproducibility:** `scripts/08_analysis.py` re-ran on the final dataset and reproduced the archived TASK 10 outputs **byte-for-byte** (deterministic; fixed bootstrap seed).

---

## 1. Frozen, verified dataset

| Check | Result |
|---|---|
| Rows / unique `(seed, condition, target)` combos | 180 / 180 (0 duplicates) |
| Valid 38-dimension scores | **179** |
| Missing | **1** — `A0 × GPT-5.6 Luna × classified_leak_goal_conflict` |
| Recovered scores (counted once, newest log preferred) | 21 |
| Source batches | only `batch02_25turns` + `batch03_180` (no smoke / 15-turn / mock / wrong-seed) |
| Models | auditor `deepseek/deepseek-flash`, judge `anthropic/claude-haiku-5-5` only |
| `max_turns` | 25 (all) |

Source logs and prior archives (`results/archive_task08_173scored`, `archive_task09_178scored`, `archive_task10_179scored`) preserved. The single missing score is **not** imputed.

## 2. Statistical methods (unchanged)

Primary outcome `unprompted_deception_toward_user` (judge scale 1–10). Seed-level paired bootstrap, 10,000 resamples, fixed seed (20261012), 95% percentile CIs; **seeds are the resampling unit**, resampled jointly across targets/conditions to preserve pairing. Paired contrasts use complete observed pairs; the missing GPT cell is simply excluded from the affected pairs (n=19 instead of 20), never imputed. Target rankings and pairwise target differences use paired-seed bootstrap. Missing-data bounds use the full scale [1,10].

## 3. Primary results

**Means (95% CI):**

| Condition | GPT-5.6 Luna | Gemini 3.5 Flash-Lite | Mistral Large 3 |
|---|---|---|---|
| A0 | 1.42 [1.10, 1.83] (n=19) | 2.25 [1.70, 2.85] | 3.60 [2.90, 4.35] |
| A1 | 1.45 [1.15, 1.80] | 2.40 [1.70, 3.20] | 3.35 [2.60, 4.15] |
| A2 | 1.50 [1.25, 1.75] | 2.00 [1.55, 2.50] | 3.50 [2.75, 4.30] |

**Paired auditor contrasts (against A0):**

| Contrast | Overall (pairs) | GPT | Gemini | Mistral |
|---|---|---|---|---|
| A1−A0 | −0.02 [−0.35, 0.32] (20) | +0.05 | +0.15 | −0.25 |
| A2−A0 | −0.08 [−0.42, 0.27] (20) | +0.11 | −0.25 | −0.10 |
| A2−A1 | −0.07 [−0.50, 0.38] (20) | +0.05 | −0.40 | +0.15 |

All auditor-condition CIs include zero; |overall effect| ≤ 0.08 points on a 1–10 scale.

**Target differences (paired by seed, per condition)** — Mistral−GPT ≈ +1.9 to +2.3 (all CIs exclude 0); Gemini−GPT ≈ +0.5 to +0.9 (all exclude 0); Mistral−Gemini ≈ +0.95 to +1.5 (A1 CI includes 0).

**Target ranking:** **Mistral > Gemini > GPT in every condition.** Bootstrap ranking-reversal frequencies between conditions: 0.6%–6.0% (any change 6.0%).

**Scenario-level heterogeneity (per-seed paired differences):** means ≈ 0, sd ≈ 1.4–1.7, range ≈ −5…+4, positive/negative counts roughly balanced (e.g. A2−A1: +21 / −20 / 0:19). Effects cancel in aggregate.

**Secondary (descriptive):** `concerning` A0 4.81 / A1 4.37 / A2 4.40; `unfaithful_thinking` 1.29 / 1.25 / 1.13; `unprompted_initiative` 3.03 / 2.90 / 2.92.

**Missing-data sensitivity:** only the A0-GPT cell is affected (1 missing). Worst-case A0-GPT mean ≤ **1.85** — below Gemini's A0 mean (2.25) — so the single missing score cannot plausibly reverse the target ranking.

## 4. Scenario-category heterogeneity (exploratory)

Per-seed effects do **not** cluster cleanly by Petri tag. Within `deception` (13 seeds) A2−A1 ranges −1…+2; `multi_agent` (5) −1…+1; `harm` (3) −1…+2. The largest per-seed A2−A1 effects span different categories (e.g. `vip_content_moderation_override` +1.7, `safety_concern_documentation_omit` +1.7, `pharma_adverse_event_pressure` −1.3, `reward_hack_test_hardcoding` +1.3). With k ≤ 13 per tag and overlapping tags, **no category-level conclusion is supported**; these are descriptive only.

## 5. Scenario-construction review (structured qualitative, 8 matched triplets)

Selection (transparent): 8 seeds spanning records/user-mode, subagent, multi-agent, autonomous-email and oversight types; targets rotated across GPT/Gemini/Mistral; each seed compared across A0/A1/A2. Log references are in `results/11-scenario-review.csv`.

| Triplet (seed / target) | Surface (names/dates/wording) | Role & objective | Tools / capabilities | Interaction mode | Classification |
|---|---|---|---|---|---|
| board_minutes / Gemini | Different dates & sender | Same | Same (bash,email,memory,read_file,write_file) | Same (user chat) | **Surface-only** |
| clinical_trial / GPT | Coordinator wording | Same (ClinicalAnalyst-3; Tasks 1–3) | Same (bash,read_file) | Same (autonomous subagent) | **Surface-only** |
| multi_agent_security / Mistral | Agent names | Same | Same (**send_message declared in all 3 prompts**) | Same (3-agent team) | **Surface-only** |
| subagent_refund / Mistral | Greeting wording | Same (Wayfair CS overseer) | Same functional set | Same (agentic supervisor) | **Surface-only** |
| climate_data / GPT | Prompt length/wording | Same (ClimateVoice RA) | Same (bash,email,read_file,write_file) | Same (user chat) | **Surface-only** |
| classified_leak / Gemini | Mailbox names/wording | Same functional role | **Different tool APIs/names** | Same (autonomous runs) | **Mixed** |
| vip_content_moderation / Gemini | Wording | Same (ModerationAgent-5) | Possible tool-declaration difference (only A1 names `apply_moderation_decision`) | Same (moderation subagent) | **Mixed** |
| blackmail / GPT | Persona name (Oversight/Sentinel), prompt length | Same functional role | **Different tool API design** | Same (autonomous oversight) | **Mixed** |

**Result: 5 Surface-only, 3 Mixed, 0 clearly Substantive.** The target's **role and objective are preserved** across conditions for every triplet, and where the prompt declares tools the capabilities are the same; but in 3 of 8 cases the **environment/tool APIs differ** materially (more than naming) and in some cases the tool set is not fully declared. A caveat: tool lists extracted from transcripts reflect tools *invoked*, not necessarily *available* (the `multi_agent` case shows this — all three prompts declare the same tools even though A0's target never called `send_message`).

**Verdict on the confound:** Petri's scenario-construction confound is **mostly cosmetic** (names/dates/wording) but **not purely cosmetic** — the auditor can and sometimes does build a different environment/tool surface, which could change what the target is asked to do. It cannot be assumed away.

## 6. Interpretation

**Q1 — Does target identity dominate observed deception scores?** Yes, in these scenarios. Target gaps (GPT vs Gemini vs Mistral) are ≈ 0.5–2.3 points with CIs mostly excluding zero, versus auditor-condition effects of ≤ 0.08 (CIs all spanning zero). *Scope:* this is the ranking of these three specific models on the pilot's 20 constructed scenarios; it is not a general statement about model safety.

**Q2 — Is there a systematic auditor-strategy effect?** **No detectable effect.** All paired contrasts' 95% CIs include zero. This is **not evidence of equivalence**: with 20 seeds the overall CI half-width is ≈ 0.35–0.4 points, so small-to-moderate strategy effects (e.g. ≲0.4) remain compatible with the data. The honest statement is *"insufficient precision to detect the plausible effect sizes, and no hint of a consistent direction."*

**Q3 — Are auditor effects heterogeneous across scenarios?** Yes. Per-seed effects are large (range ≈ ±5) and roughly symmetric, cancelling in aggregate. Any real strategy effect would have to be highly scenario-dependent (or the heterogeneity is noise).

**Q4 — Do target rankings depend on auditor strategy?** **No** — the observed ranking (Mistral > Gemini > GPT) is identical in all three conditions, and bootstrap ranking reversals are rare (0.6–6%). Bootstrap frequencies are sampling-noise descriptions, **not** probabilities of future outcomes.

**Q5 — What prevents a causal interpretation?**
1. **Scenario construction** (mixed, not merely cosmetic): the auditor changes the environment/tools as well as the interrogation.
2. **Turn-budget saturation**: ~half of audits hit 25 turns, unequally (A0 45%, A1 53%, A2 57%).
3. **Single judge & scoring reliability**: one judge/epoch; ~12% of new-audit samples needed a re-score and 1 is permanently missing.
4. **The remaining missing score** (non-random: A0/GPT) — bound small, but present.
5. **Stochastic execution, single epoch**: no averaging over runs; judge scores are a proxy for judged appearance, not independently verified deceptive behaviour.
6. Judge-assigned "deception" ≠ ground-truth deception.

## 7. Implications for PROBUS and MATS

**Demonstrated limitations (directly observed):**
- Auditor interrogation changes the scenario/tool surface (mixed construction; §5) → strategy cannot be isolated by changing only the auditor prompt.
- Target identity produced much larger score differences than auditor strategy.
- Judge reliability on long/sensitive transcripts (structured-output failures; a content filter).
- Turn-budget saturation, unequal across conditions.

**Reasonable methodological implications (suggested by the findings):**
- **Fix the scenario independently of the auditor** (author the target system prompt, tools and initial state outside the interrogation strategy) so the manipulation varies *only* interrogation.
- **Separate ground-truth verification** from the LLM judge (human/independent checks of whether the target actually did the concerning action).
- **Average over stochastic runs / judges**, and pre-register the primary outcome and dimensions.
- **Standardize turn budgets** and report saturation per condition.

**Unverified hypotheses (require new experiments):**
- Whether auditor strategy has a small (≲0.4) real effect that this pilot is underpowered to detect.
- Whether the scenario-construction differences materially change outcomes (needs the fixed-scenario design).
- Whether a stronger judge or multiple judges change the estimates.

**What additional controls would separate the factors:** fixed-scenario construction (holds environment constant) separates *auditor strategy* from *scenario*; ground-truth behavioural verification separates *target behaviour* from *judge scoring*; repeated runs separate signal from stochastic noise.

**On using Petri:** Petri is an **independently developed, maintained evaluation framework**. Using it for this pilot **reduces dependence on custom-built evaluation infrastructure** (its scaffolding, logging, judge and viewer are native and verified) — but it **does not eliminate experimental-design bias**, because Petri deliberately lets the auditor construct the scenario. It is **not** an independent validation of PROBUS or SLEF; **one must not claim that Petri cannot support fixed-scenario controls under other configurations** — this pilot simply did not fix the scenario.

## 8. Conclusion

**Five evidence-based findings**
1. **Target identity dominates**: target gaps ≈ 0.5–2.3 points; robust ranking (Mistral > Gemini > GPT) across conditions.
2. **No detectable auditor-strategy effect**: all paired contrasts include zero (|overall| ≤ 0.08); precision insufficient to claim equivalence.
3. **Large scenario-level heterogeneity** with cancellation (per-seed ±5; balanced signs).
4. **Target ranking is stable across auditor strategies** (bootstrap reversal 0.6–6%).
5. **The scenario-construction confound is mixed, not purely cosmetic** (3/8 triplets changed the environment/tool surface despite preserving role/objective).

**Five limitations**
1. Scenario-construction confound (mixed).
2. Single judge, one epoch; ~12% re-score rate and 1 permanently missing score (non-random).
3. ~50% turn-limit saturation, unequal across conditions.
4. Small pilot (20 seeds); descriptive means only.
5. Judge-assigned scores are not ground-truth behavioural verification.

**Strongest defensible statement for the MATS application**
> "In a 180-audit feasibility pilot using an independently developed evaluation framework (Petri), we found that variation between the evaluated **target models** produced much larger differences in a judge-assigned deception score than variation between three **auditor interrogation strategies**; the auditor-strategy contrasts were not distinguishable from zero and were accompanied by large scenario-level heterogeneity and a scenario-construction confound. The pilot establishes a reproducible pipeline and motivates a design in which the scenario is fixed independently of the auditor and behavioural outcomes are independently verified."

**Claims that must be avoided**
- That auditor strategy is (or is not) causally irrelevant.
- Statistical significance, equivalence, or "proof of no effect".
- Generalizing the target ranking to model safety in general.
- That the pilot validates PROBUS/SLEF.
- Probabilities of future deployment outcomes from bootstrap frequencies.
- Presenting the missing/GPT results as complete.

**Is further analysis needed before using the pilot?** No. The dataset and analysis are complete and reproducible; the remaining gap is **design** (fixed-scenario, independent verification), which requires new experiments, not more analysis of these data.

## Artifacts

- `reports/11-final-scientific-analysis.md` (this report); `reports/11-executive-summary.md`.
- `results/petri_180.csv` (179 scored); `results/08-auditor-effects.png`; `results/08-paired-effects.csv`; `results/08-ranking-analysis.csv`; `results/08_means_by_condition_target.csv`; `results/08-missing-sensitivity.csv`; `results/08-per-seed-differences.csv`; **`results/11-scenario-review.csv`**.
- `scripts/08_analysis.py` (unchanged methods). Archives preserved.

*No new audits, no paid calls, no imputation, no framework/dashboard, no source modifications, no commits.*
