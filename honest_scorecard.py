#!/usr/bin/env python3
"""Channel-isolated, episode-level descriptive precision from retained calls.

Run without arguments to synchronize scorecard JSON and the README headline.
Use --check in CI to refuse stale artifacts. No prices or outcomes are fetched.
"""

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import pandas as pd

MERGE_GAP_DAYS = 30
ROOT = Path(__file__).resolve().parent
CHANNELS = ("Q4_precision_channel", "all_critical_coverage_channel")
EPISODE_COLUMNS = ["market", "start", "end", "n_calls", "outcome"]
START = "<!-- SCORECARD_START -->"
END = "<!-- SCORECARD_END -->"


def normalize_calls(df: pd.DataFrame) -> pd.DataFrame:
    required = {"market", "call_date", "signal_type", "quadrant", "status"}
    if not required <= set(df.columns):
        raise ValueError(f"Missing call fields: {sorted(required - set(df.columns))}")
    df = df.copy()
    df["call_date"] = pd.to_datetime(df["call_date"], errors="raise")
    if df["call_date"].isna().any() or df["market"].isna().any():
        raise ValueError("Market and call date must be known")
    df["market"] = df["market"].astype(str).str.strip()
    if (df["market"] == "").any():
        raise ValueError("Market must not be empty")
    df["status"] = df["status"].fillna("pending").str.strip().str.lower()
    if not df["status"].isin(["pending", "true_positive", "false_positive"]).all():
        raise ValueError("Unknown outcome status")
    df["signal_type"] = df["signal_type"].fillna("").str.strip()
    df["quadrant"] = df["quadrant"].fillna("").str.strip()
    if not df["signal_type"].isin(["CRITICAL", "Q4"]).all():
        raise ValueError("Outcome ledger must contain CRITICAL/Q4 calls only")
    return df.sort_values(["market", "call_date", "signal_type", "quadrant", "status"])


def load_calls(path=None) -> pd.DataFrame:
    return normalize_calls(pd.read_csv(path or ROOT / "outcomes.csv"))


def merge_episodes(df: pd.DataFrame) -> pd.DataFrame:
    """Merge an already selected population; never infer channel from a cluster."""
    df = normalize_calls(df)
    episodes = []
    for market, group in df.groupby("market", sort=True):
        current = None
        for row in group.itertuples():
            if current is None or row.call_date - current["end"] > pd.Timedelta(days=MERGE_GAP_DAYS):
                if current is not None:
                    episodes.append(current)
                current = {"market": market, "start": row.call_date,
                           "end": row.call_date, "n_calls": 0, "statuses": []}
            current["end"] = row.call_date
            current["n_calls"] += 1
            current["statuses"].append(row.status)
        if current is not None:
            episodes.append(current)
    rows = []
    for episode in episodes:
        statuses = set(episode.pop("statuses"))
        # Success can resolve before the horizon; failure requires every call
        # in this channel's episode to resolve. Preserve this legacy endpoint.
        outcome = "TP" if "true_positive" in statuses else (
            "FP" if statuses == {"false_positive"} else "OPEN")
        rows.append({**episode, "start": str(episode["start"].date()),
                     "end": str(episode["end"].date()), "outcome": outcome})
    return pd.DataFrame(rows, columns=EPISODE_COLUMNS)


def channel_episodes(calls: pd.DataFrame) -> dict:
    calls = normalize_calls(calls)
    q4 = (calls["signal_type"] == "Q4") | (calls["quadrant"] == "Q4")
    return {CHANNELS[0]: merge_episodes(calls[q4]),
            CHANNELS[1]: merge_episodes(calls)}


def score(episodes_by_channel: dict) -> dict:
    if not isinstance(episodes_by_channel, dict) or set(episodes_by_channel) != set(CHANNELS):
        raise ValueError("Score requires independently merged channel populations")
    channels = {}
    for name in CHANNELS:
        episodes = episodes_by_channel[name]
        resolved = episodes[episodes["outcome"] != "OPEN"]
        tp = int((resolved["outcome"] == "TP").sum())
        channels[name] = {
            "episodes": len(episodes), "resolved": len(resolved),
            "open_censored": int((episodes["outcome"] == "OPEN").sum()),
            "tp": tp, "fp": len(resolved) - tp,
            "precision_resolved_only": round(tp / len(resolved), 3) if len(resolved) else None,
        }
    return {"schema_version": 2, "methodology": "channel-isolated-episodes-v2",
            "merge_gap_days": MERGE_GAP_DAYS,
            "channel_definitions": {
                CHANNELS[0]: "signal_type == Q4 OR quadrant == Q4, selected BEFORE merging",
                CHANNELS[1]: "all retained CRITICAL/Q4 calls, independently merged",
            },
            "outcome_rule": "any TP => TP; all FP => FP; otherwise OPEN, within each channel",
            "unit": "episodes per market, adjacent-call gap <= 30 days; resolved-only precision",
            "channels": channels,
            "note": "Descriptive legacy >=20% drawdown / 90-calendar-day call outcomes. "
                    "Success may resolve early; failure waits for all calls. Resolved-only precision "
                    "is subject to informative censoring, not unconditional accuracy or event recall. "
                    "Channel populations overlap; do not add their counts."}


def build_scorecard_text(ledger_text: str) -> dict:
    ledger_text = ledger_text.replace("\r\n", "\n")
    calls = normalize_calls(pd.read_csv(io.StringIO(ledger_text)))
    episodes = channel_episodes(calls)
    return {**score(episodes),
            "source": {"path": "outcomes.csv",
                       "sha256_utf8_lf": hashlib.sha256(ledger_text.encode("utf-8")).hexdigest(),
                       "latest_call_date": str(calls["call_date"].max().date()) if len(calls) else None,
                       "timing_note": "Latest call date is not an outcome availability or generation time."},
            "calls": {"total": len(calls), "pending": int((calls["status"] == "pending").sum())},
            "episodes_by_channel": {name: episodes[name].to_dict("records") for name in CHANNELS}}


def build_scorecard(path=None) -> dict:
    return build_scorecard_text(Path(path or ROOT / "outcomes.csv").read_text(encoding="utf-8"))


def json_text(sc: dict) -> str:
    return json.dumps(sc, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def markdown_headline(sc: dict) -> str:
    def fmt(channel):
        p = channel["precision_resolved_only"]
        value = (f"{channel['tp']}/{channel['resolved']} ({p * 100:.0f}%)"
                 if p is not None else "0 resolved")
        return f"{value}; {channel['open_censored']} open"
    all_calls, q4 = sc["channels"][CHANNELS[1]], sc["channels"][CHANNELS[0]]
    return (f"{START}\n**Episode hit rate (resolved-only): {fmt(all_calls)}**"
            f" | Q4 channel: {fmt(q4)} | {sc['calls']['pending']} calls pending"
            " | [methodology](METHODOLOGY.md) / [scorecard](signals/scorecard.json)\n"
            f"{END}")


def replace_headline(readme: str, sc: dict) -> str:
    if START in readme or END in readme:
        if readme.count(START) != 1 or readme.count(END) != 1:
            raise ValueError("Expected exactly one scorecard marker pair")
        pattern = re.escape(START) + r".*?" + re.escape(END)
    else:
        # One-time migration of the previous generated single-line headline.
        pattern = r"(?m)^[^\n]*\*\*Episode hit rate \(resolved-only\):[^\n]*$"
    result, count = re.subn(pattern, lambda _: markdown_headline(sc), readme,
                            flags=re.DOTALL if START in readme else 0)
    if count != 1:
        raise ValueError("Expected exactly one generated scorecard headline")
    return result


def sync_artifacts(root=ROOT, check=False) -> dict:
    root = Path(root)
    sc = build_scorecard(root / "outcomes.csv")
    readme_path, score_path = root / "README.md", root / "signals" / "scorecard.json"
    readme = readme_path.read_text(encoding="utf-8")
    expected_readme, expected_json = replace_headline(readme, sc), json_text(sc)
    if check:
        if not score_path.exists() or score_path.read_text(encoding="utf-8") != expected_json or readme != expected_readme:
            raise ValueError("Stale scorecard/README: run python honest_scorecard.py")
    else:
        score_path.parent.mkdir(parents=True, exist_ok=True)
        score_path.write_text(expected_json, encoding="utf-8", newline="\n")
        readme_path.write_text(expected_readme, encoding="utf-8", newline="\n")
    return sc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = sync_artifacts(check=args.check)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(markdown_headline(result))
