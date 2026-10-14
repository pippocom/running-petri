# Petri Feasibility Pilot — Executive Summary

**What we did.** We ran a 180-audit feasibility pilot of an AI-safety evaluation ("Petri"). For each audit, an **auditor** AI interrogates a **target** AI in a constructed scenario, and a fixed **judge** AI scores the transcript. We varied three things: the **auditor's strategy** (A0 default, A1 trusting, A2 skeptical/verifying), the **target model** (GPT-5.6 Luna, Gemini 3.5 Flash-Lite, Mistral Large 3), and the **scenario** (20 shared seeds). Design: 3 × 3 × 20 = 180 audits, 25 turns each, judged by Claude Haiku 5.5. We obtained **179 of 180** judge scores (one was blocked by a provider content filter).

**Main finding.** In these scenarios, **which target model you evaluate matters much more than how the overseer interrogates it.** On the judge's 1–10 deception scale, target differences were large (Mistral ≈ 3.5, Gemini ≈ 2.2, GPT ≈ 1.4), while the differences between auditor strategies were tiny (≤ 0.08 points on average) and every confidence interval included zero.

**Secondary findings.**
- **No detectable auditor-strategy effect.** We cannot say strategy has no effect — only that this pilot could not detect one, and its precision rules out only fairly large effects.
- **The scenario matters a lot, in both directions.** For a given target, changing the auditor strategy raised the score on some scenarios and lowered it on others, roughly cancelling out.
- **Target ranking is stable** (Mistral > Gemini > GPT) under all three strategies.

**Important caveat.** Petri's auditor builds the scenario as well as the interrogation. Comparing the three strategies across 8 matched scenarios, most differences were cosmetic (different names/dates), but in about 3 of 8 the environment or tools also differed — so a difference between strategies is not guaranteed to be about *interrogation* alone. Other limits: one judge and one run per audit, ~half of audits hit the turn limit (unevenly across strategies), and judge scores measure the *appearance* of deception, not independently verified behaviour.

**Bottom line for the MATS application.** The pilot reliably demonstrates a **reproducible pipeline** built on an independently developed framework, and shows that **target identity dominated auditor strategy** in this sample. It does **not** prove that auditor strategy is irrelevant, and it should not be presented as validating any proposed framework. The natural next step — suggested, not yet tested — is a design where the **scenario is fixed independently of the auditor** and **behaviour is independently verified**, rather than relying only on an LLM judge.

**What is safe to claim.** A reproducible feasibility result: in 180 audits, target-model differences in a judge-assigned deception score were large and stable, while auditor-strategy differences were not distinguishable from noise.

**What is not.** Any claim of a causal (or null) auditor-strategy effect; statistical significance; general model-safety rankings; or validation of a proposed evaluation framework.
