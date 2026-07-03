#!/usr/bin/env python3
"""
Honest scorecard: episode-level, censoring-aware, channel-split precision.
==========================================================================

Fixes two statistical artifacts in the current README headline:

1. PSEUDO-REPLICATION — outcomes.csv tracks every CRITICAL/Q4 *day*;
   near-adjacent calls on the same market are one bet counted many times.
   This script merges calls into episodes (gap <= MERGE_GAP days per
   market) and scores each episode ONCE (an episode is TP if any of its
   calls resolved true_positive; FP only if all calls resolved).
2. CENSORING — calls whose 90-day window has not closed leave the
   denominator entirely; the resolution rate is reported separately.

Channel split (precision vs coverage): the Q4-only channel is scored
separately from the all-CRITICAL channel, so the strict rule's precision is
never diluted by the breadth-tuned rule's flood — and vice versa.

Output: signals/scorecard.json (self-describing) + a Markdown block on
stdout for README embedding. All headline numbers should render FROM this
artifact (single source of truth).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

MERGE_GAP_DAYS = 30
ROOT = Path(__file__).resolve().parent


def load_calls(path=None) -> pd.DataFrame:
    df = pd.read_csv(path or ROOT / "outcomes.csv", parse_dates=["call_date"])
    df["status"] = df["status"].fillna("pending").str.strip().str.lower()
    return df.sort_values(["market", "call_date"])


def merge_episodes(df: pd.DataFrame) -> pd.DataFrame:
    """One row per episode: market, start, end, n_calls, q4_flag, outcome."""
    episodes = []
    for market, g in df.groupby("market"):
        g = g.sort_values("call_date")
        cur = None
        for row in g.itertuples():
            if cur is None or (row.call_date - cur["end"]).days > MERGE_GAP_DAYS:
                if cur is not None:
                    episodes.append(cur)
                cur = {"market": market, "start": row.call_date,
                       "end": row.call_date, "n_calls": 0,
                       "q4": False, "statuses": []}
            cur["end"] = row.call_date
            cur["n_calls"] += 1
            cur["q4"] = cur["q4"] or (str(row.signal_type).strip() == "Q4"
                                      or str(row.quadrant).strip() == "Q4")
            cur["statuses"].append(row.status)
        if cur is not None:
            episodes.append(cur)

    rows = []
    for e in episodes:
        st = set(e["statuses"])
        if "true_positive" in st:
            outcome = "TP"
        elif st <= {"false_positive"}:
            outcome = "FP"
        else:
            outcome = "OPEN"       # any pending call -> episode censored
        rows.append({"market": e["market"],
                     "start": str(e["start"].date()),
                     "end": str(e["end"].date()),
                     "n_calls": e["n_calls"],
                     "channel": "Q4" if e["q4"] else "CRITICAL",
                     "outcome": outcome})
    return pd.DataFrame(rows)


def score(eps: pd.DataFrame) -> dict:
    def channel_stats(sub):
        resolved = sub[sub.outcome != "OPEN"]
        tp = int((resolved.outcome == "TP").sum())
        return {"episodes": int(len(sub)),
                "resolved": int(len(resolved)),
                "open_censored": int((sub.outcome == "OPEN").sum()),
                "tp": tp, "fp": int(len(resolved)) - tp,
                "precision_resolved_only":
                    round(tp / len(resolved), 3) if len(resolved) else None}
    return {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "unit": "episodes (calls merged per market, gap <= %d d); "
                "precision computed on RESOLVED episodes only" % MERGE_GAP_DAYS,
        "channels": {
            "Q4_precision_channel": channel_stats(eps[eps.channel == "Q4"]),
            "all_critical_coverage_channel": channel_stats(eps),
        },
        "note": "coverage-channel detection rate on the historical event "
                "ledger is a SENSITIVITY metric and lives in the validation "
                "section; it must not be quoted beside these precision "
                "numbers as if produced by the same rule.",
    }


def markdown_block(sc: dict) -> str:
    q4 = sc["channels"]["Q4_precision_channel"]
    al = sc["channels"]["all_critical_coverage_channel"]
    def fmt(c):
        p = c["precision_resolved_only"]
        return (f"{c['tp']}/{c['resolved']} resolved "
                f"({p * 100:.0f}%)" if p is not None else "no resolved episodes") \
               + f" · {c['open_censored']} open"
    return ("### Honest scorecard (episode-level, resolved-only)\n\n"
            f"- **Q4 precision channel**: {fmt(q4)}\n"
            f"- All-CRITICAL (coverage) channel: {fmt(al)}\n"
            f"- Unit: {sc['unit']}\n")


if __name__ == "__main__":
    calls = load_calls(sys.argv[1] if len(sys.argv) > 1 else None)
    eps = merge_episodes(calls)
    sc = score(eps)
    out = ROOT / "signals" / "scorecard.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(
        {**sc, "episodes": eps.to_dict("records")}, indent=1))
    print(markdown_block(sc))
    print(f"calls={len(calls)} -> episodes={len(eps)}  (written: {out})")
