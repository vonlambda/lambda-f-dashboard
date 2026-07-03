#!/usr/bin/env python3
"""
Verification for honest_scorecard.py: episode merge + censoring semantics.
Run: python tests/test_scorecard.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from honest_scorecard import merge_episodes, score  # noqa: E402


def test_merge_and_censoring():
    df = pd.DataFrame({
        "call_date": pd.to_datetime(
            ["2026-01-01", "2026-01-03", "2026-01-05",   # one episode, 3 calls
             "2026-03-15",                                # separate episode
             "2026-05-01"]),                              # pending episode
        "market": ["Silver"] * 3 + ["Silver", "Gold"],
        "signal_type": ["CRITICAL", "Q4", "CRITICAL", "CRITICAL", "Q4"],
        "quadrant": ["Q3", "Q4", "Q3", "Q1", "Q4"],
        "ticker": ["SLV"] * 4 + ["GLD"],
        "price_at_call": [1.0] * 5,
        "max_dd_30d": [0.0] * 5, "max_dd_60d": [0.0] * 5, "max_dd_90d": [0.0] * 5,
        "status": ["false_positive", "true_positive", "false_positive",
                   "false_positive", "pending"],
    })
    eps = merge_episodes(df.sort_values(["market", "call_date"]))
    assert len(eps) == 3, f"expected 3 episodes, got {len(eps)}"

    e1 = eps[(eps.market == "Silver") & (eps.start == "2026-01-01")].iloc[0]
    assert e1.n_calls == 3, "adjacent calls did not merge"
    assert e1.outcome == "TP", "episode with any TP call must score TP once"
    assert e1.channel == "Q4", "episode containing a Q4 call is Q4-channel"

    gold = eps[eps.market == "Gold"].iloc[0]
    assert gold.outcome == "OPEN", "pending call must censor the episode"

    sc = score(eps)
    q4 = sc["channels"]["Q4_precision_channel"]
    assert q4["resolved"] == 1 and q4["tp"] == 1 and q4["open_censored"] == 1
    assert q4["precision_resolved_only"] == 1.0
    print("scorecard verification: 5 calls -> 3 episodes, merge/censoring/"
          "channel-split all correct -- PASS")


if __name__ == "__main__":
    test_merge_and_censoring()
