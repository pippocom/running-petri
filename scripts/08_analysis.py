#!/usr/bin/env python
"""TASK 08 — statistical analysis of the 180-audit Petri pilot.

Reproducible, local only (no API calls). Reads native Inspect .eval logs,
builds results/petri_180.csv, runs the primary/secondary/ranking analyses with
a paired seed-level bootstrap (fixed seed), and writes the CSVs and figure.

Run from the project root:
    .venv/bin/python scripts/08_analysis.py
"""
from __future__ import annotations

import glob
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from inspect_ai.log import read_eval_log

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

DIRS = ["logs/batch02_25turns", "logs/batch03_180"]
CONDS = ["A0", "A1", "A2"]
TARGETS = ["openai/gpt-5.6-luna", "google/gemini-3.5-flash-lite", "mistral/mistral-large-2512"]
TARGET_SHORT = {
    "openai/gpt-5.6-luna": "gpt-5.6-luna",
    "google/gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    "mistral/mistral-large-2512": "mistral-large-2512",
}
PRIMARY = "unprompted_deception_toward_user"
SECONDARY = ["concerning", "unfaithful_thinking", "unprompted_initiative"]
SCALE_MIN, SCALE_MAX = 1, 10  # judge prompt: 1 = "not at all" .. 10 = "extremely"
BOOT = 10000
BOOT_SEED = 20261012

# ---------------------------------------------------------------- dataset
def use_log(d: str) -> list[str]:
    """Select the newest valid scored log for each base log (versioned recovery).

    Preference order: <base>_rescored3.eval > <base>_rescored2.eval > <base>_rescored.eval > <base>.eval.
    This ensures each experimental combination is counted exactly once, using the
    most recently recovered scores when available (TASK 09).
    """
    out = []
    for L in sorted(glob.glob(f"{d}/*.eval")):
        if L.endswith("_rescored.eval") or L.endswith("_rescored2.eval") or L.endswith("_rescored3.eval"):
            continue
        base = L[: -len(".eval")]
        pick = L
        for suf in ("_rescored3.eval", "_rescored2.eval", "_rescored.eval"):
            cand = base + suf
            if os.path.exists(cand):
                pick = cand
                break
        out.append(pick)
    return out


def cond_of(task_args) -> str:
    sm = task_args.get("system_message")
    if not sm:
        return "A0"
    return "A1" if "a1" in str(sm) else "A2"


def score_of(sample):
    sc = (sample.scores or {}).get("audit_judge")
    v = getattr(sc, "value", None)
    return v if isinstance(v, dict) and len(v) > 0 else None


def main() -> None:
    rows = []
    for d in DIRS:
        for L in use_log(d):
            log = read_eval_log(L)
            ta = log.eval.task_args
            cond = cond_of(ta)
            tgt = log.eval.model_roles["target"].model
            mt = ta.get("max_turns")
            orig_path = L
            for suf in ("_rescored3.eval", "_rescored2.eval", "_rescored.eval"):
                if orig_path.endswith(suf):
                    orig_path = orig_path[: -len(suf)] + ".eval"
            orig = read_eval_log(orig_path) if orig_path != L else None
            orig_scored = {}
            if orig is not None:
                orig_scored = {str(s.id): score_of(s) is not None for s in orig.samples}
            for s in log.samples:
                v = score_of(s)
                scored = v is not None
                recovered = bool(
                    orig is not None and (orig_scored.get(str(s.id)) is False) and scored
                )
                mu = s.model_usage or {}
                cost = sum((x.total_cost or 0.0) for x in mu.values())
                msgs = s.messages or []
                rows.append(
                    dict(
                        seed=str(s.id),
                        auditor_condition=cond,
                        target=TARGET_SHORT.get(tgt, tgt),
                        target_model=tgt,
                        auditor_model=log.eval.model_roles["auditor"].model,
                        judge_model=log.eval.model_roles["judge"].model,
                        primary=float(v[PRIMARY]) if scored and PRIMARY in v else np.nan,
                        concerning=float(v["concerning"]) if scored and "concerning" in v else np.nan,
                        unfaithful_thinking=float(v["unfaithful_thinking"]) if scored and "unfaithful_thinking" in v else np.nan,
                        unprompted_initiative=float(v["unprompted_initiative"]) if scored and "unprompted_initiative" in v else np.nan,
                        scored=scored,
                        n_dims=len(v) if scored else 0,
                        score_recovered=recovered,
                        turn_count=s.turn_count,
                        max_turns=mt,
                        saturated=bool(s.turn_count is not None and mt and s.turn_count >= 2 * mt),
                        n_auditor_messages=sum(1 for m in msgs if getattr(m, "role", None) == "user"),
                        cost_usd=round(cost, 6),
                        source_batch=d.split("/")[-1],
                        log_file=os.path.basename(L),
                    )
                )
    df = pd.DataFrame(rows)
    order = {"A0": 0, "A1": 1, "A2": 2}
    df["_c"] = df["auditor_condition"].map(order)
    df = df.sort_values(["_c", "target", "seed"]).drop(columns="_c").reset_index(drop=True)

    # ---- validation
    combos = df.groupby(["seed", "auditor_condition", "target"]).size()
    assert len(df) == 180, f"expected 180 rows, got {len(df)}"
    assert (combos == 1).all(), "duplicate (seed,condition,target) combinations"
    print("validation:", len(df), "rows |", int(df.scored.sum()), "scored |", int(df.primary.isna().sum()), "missing primary")
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/petri_180.csv", index=False)
    print("wrote results/petri_180.csv:", df.shape, "| scored:", df.scored.sum(), "| recovered:", df.score_recovered.sum())

    # ---------------------------------------------------------------- bootstrap
    seeds = sorted(df.seed.unique())
    sidx = {s: i for i, s in enumerate(seeds)}
    rng = np.random.default_rng(BOOT_SEED)
    B = rng.integers(0, len(seeds), size=(BOOT, len(seeds)))  # shared resample matrix

    def boot(fn):
        """fn(chosen_seed_list) -> float or None ; returns 95% percentile CI + point."""
        vals = []
        for b in range(BOOT):
            chosen = [seeds[i] for i in B[b]]
            v = fn(chosen)
            if v is not None and np.isfinite(v):
                vals.append(v)
        vals = np.array(vals)
        return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), float(np.mean(vals))

    def per_seed_series(cond, target, col="primary"):
        g = df[(df.auditor_condition == cond) & (df.target == target)]
        return {r.seed: getattr(r, col) for r in g.itertuples() if np.isfinite(getattr(r, col))}

    # ---- means + CI per auditor x target
    means = []
    for c in CONDS:
        for t in TARGETS:
            ts = TARGET_SHORT[t]
            ser = per_seed_series(c, ts)
            obs = float(np.mean(list(ser.values())))
            lo, hi, _ = boot(lambda ch, ser=ser: np.mean([ser[s] for s in ch if s in ser]) if ser else None)
            means.append(dict(auditor_condition=c, target=ts, n=len(ser), mean=round(obs, 3), ci_lo=round(lo, 3), ci_hi=round(hi, 3)))
    means_df = pd.DataFrame(means)
    means_df.to_csv("results/08_means_by_condition_target.csv", index=False)
    print("\n=== means (primary), 95% bootstrap CI ===")
    print(means_df.to_string(index=False))

    # ---- paired contrasts within target + overall
    def paired_within(target, c_hi, c_lo):
        a = per_seed_series(c_hi, target); b = per_seed_series(c_lo, target)
        common = sorted(set(a) & set(b))
        d = {s: a[s] - b[s] for s in common}
        obs = float(np.mean(list(d.values()))) if d else np.nan
        lo, hi, _ = boot(lambda ch, d=d: np.mean([d[s] for s in ch if s in d]) if d else None)
        return obs, lo, hi, len(common)

    def paired_overall(c_hi, c_lo):
        # per seed: mean over targets of the paired diff; resample seeds jointly
        per = defaultdict(list)
        for t in TARGETS:
            ts = TARGET_SHORT[t]
            a = per_seed_series(c_hi, ts); b = per_seed_series(c_lo, ts)
            for s in set(a) & set(b):
                per[s].append(a[s] - b[s])
        d = {s: float(np.mean(v)) for s, v in per.items()}
        obs = float(np.mean(list(d.values()))) if d else np.nan
        lo, hi, _ = boot(lambda ch, d=d: np.mean([d[s] for s in ch if s in d]) if d else None)
        return obs, lo, hi, len(d)

    pair_rows = []
    for (hi, lo) in [("A1", "A0"), ("A2", "A0"), ("A2", "A1")]:
        for t in TARGETS:
            ts = TARGET_SHORT[t]
            obs, blo, bhi, n = paired_within(ts, hi, lo)
            pair_rows.append(dict(contrast=f"{hi}-{lo}", target=ts, n_pairs=int(n),
                                  mean_diff=None if np.isnan(obs) else round(obs, 3),
                                  ci_lo=round(blo, 3), ci_hi=round(bhi, 3)))
        obs, blo, bhi, n = paired_overall(hi, lo)
        pair_rows.append(dict(contrast=f"{hi}-{lo}", target="OVERALL", n_pairs=int(n),
                              mean_diff=None if np.isnan(obs) else round(obs, 3),
                              ci_lo=round(blo, 3), ci_hi=round(bhi, 3)))
    pairs_df = pd.DataFrame(pair_rows)
    pairs_df.to_csv("results/08-paired-effects.csv", index=False)
    print("\n=== paired contrasts (primary) ===")
    print(pairs_df.to_string(index=False))

    # ---- target rankings per condition + bootstrap
    rank_rows = []
    rank_dists = defaultdict(list)
    means_by = {}
    for c in CONDS:
        for t in TARGETS:
            ts = TARGET_SHORT[t]
            ser = per_seed_series(c, ts)
            means_by[(c, ts)] = ser
        tsorted = sorted(TARGETS, key=lambda t: -float(np.mean(list(means_by[(c, TARGET_SHORT[t])].values()))))
        rank_rows.append(dict(kind="observed_ranking", auditor_condition=c, ranking=" > ".join(TARGET_SHORT[t] for t in tsorted),
                              means="; ".join(f"{TARGET_SHORT[t]}={np.mean(list(means_by[(c,TARGET_SHORT[t])].values())):.2f}" for t in tsorted)))
    # joint bootstrap for rankings
    for b in range(BOOT):
        chosen = [seeds[i] for i in B[b]]
        cond_rank = {}
        for c in CONDS:
            vals = {}
            for t in TARGETS:
                ts = TARGET_SHORT[t]; ser = means_by[(c, ts)]
                vs = [ser[s] for s in chosen if s in ser]
                vals[ts] = float(np.mean(vs)) if vs else np.nan
            cond_rank[c] = tuple(sorted(vals, key=lambda k: -vals[k]))
        rank_dists["A0_vs_A1"].append(cond_rank["A0"] != cond_rank["A1"])
        rank_dists["A0_vs_A2"].append(cond_rank["A0"] != cond_rank["A2"])
        rank_dists["A1_vs_A2"].append(cond_rank["A1"] != cond_rank["A2"])
        rank_dists["any_change"].append(len({cond_rank["A0"], cond_rank["A1"], cond_rank["A2"]}) > 1)
    for k, v in rank_dists.items():
        rank_rows.append(dict(kind="bootstrap_reversal_freq", auditor_condition=k, ranking=f"{100*np.mean(v):.1f}%", means=""))
    # pairwise target diffs within condition (paired by seed)
    for c in CONDS:
        for (t1, t2) in [("mistral-large-2512", "gemini-3.5-flash-lite"), ("mistral-large-2512", "gpt-5.6-luna"), ("gemini-3.5-flash-lite", "gpt-5.6-luna")]:
            a = means_by[(c, t1)]; bb = means_by[(c, t2)]
            common = sorted(set(a) & set(bb))
            d = {s: a[s] - bb[s] for s in common}
            obs = float(np.mean(list(d.values()))) if d else np.nan
            lo, hi, _ = boot(lambda ch, d=d: np.mean([d[s] for s in ch if s in d]) if d else None)
            rank_rows.append(dict(kind="target_pairwise_diff", auditor_condition=c, ranking=f"{t1} - {t2}",
                                  means=f"mean={obs:.2f} CI[{lo:.2f},{hi:.2f}] n={len(common)}"))
    rank_df = pd.DataFrame(rank_rows)
    rank_df.to_csv("results/08-ranking-analysis.csv", index=False)
    print("\n=== ranking analysis ===")
    print(rank_df.to_string(index=False))

    # ---- missing-score sensitivity (GPT target; 7 missing)
    sens_rows = []
    for c in CONDS:
        g = df[(df.auditor_condition == c) & (df.target == "gpt-5.6-luna")]
        obs = g.primary.dropna()
        n_miss = int(g.primary.isna().sum()); n = len(g)
        lo = (obs.sum() + n_miss * SCALE_MIN) / n
        hi = (obs.sum() + n_miss * SCALE_MAX) / n
        sens_rows.append(dict(auditor_condition=c, target="gpt-5.6-luna", n=int(n), n_missing=n_miss,
                              observed_mean=round(float(obs.mean()), 3), bound_min=round(float(lo), 3), bound_max=round(float(hi), 3)))
    sens_df = pd.DataFrame(sens_rows)
    sens_df.to_csv("results/08-missing-sensitivity.csv", index=False)
    print("\n=== missing-score bounds (primary), GPT target ===")
    print(sens_df.to_string(index=False))

    # ---- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    colors = {"A0": "#1f77b4", "A1": "#2ca02c", "A2": "#d62728"}
    for ax, t in zip(axes, TARGETS):
        ts = TARGET_SHORT[t]
        xs = np.arange(3); w = 0.6
        for i, c in enumerate(CONDS):
            r = means_df[(means_df.auditor_condition == c) & (means_df.target == ts)].iloc[0]
            ax.bar(i, r["mean"], width=w, color=colors[c], alpha=0.85)
            ax.errorbar(i, r["mean"], yerr=[[r["mean"] - r["ci_lo"]], [r["ci_hi"] - r["mean"]]],
                        fmt="none", ecolor="black", capsize=4)
            ax.text(i, r["mean"] + 0.08, f"n={int(r['n'])}", ha="center", fontsize=8)
        ax.set_xticks(xs); ax.set_xticklabels(CONDS)
        ax.set_title(ts); ax.set_ylim(0, 10.5); ax.grid(axis="y", alpha=0.3)
        if ax is axes[0]:
            ax.set_ylabel("unprompted_deception_toward_user\n(mean, 95% bootstrap CI)")
    fig.suptitle("Petri pilot (n=180): deception score by auditor condition × target")
    fig.tight_layout()
    fig.savefig("results/08-auditor-effects.png", dpi=150)
    print("\nwrote results/08-auditor-effects.png")

    # ---- behavior metadata summary (printed only)
    print("\n=== behavior metadata (means) ===")
    for c in CONDS:
        g = df[df.auditor_condition == c]
        print(f"  {c}: msgs={g.n_auditor_messages.mean():.1f} saturation={100*g.saturated.mean():.0f}% turns_mean={g.turn_count.mean():.1f}")
    print("\n=== secondary means (scored) ===")
    for col in SECONDARY:
        print(f"  {col}:", {c: round(df[df.auditor_condition == c][col].mean(), 2) for c in CONDS})


if __name__ == "__main__":
    main()
