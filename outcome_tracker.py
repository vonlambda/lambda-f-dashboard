"""
outcome_tracker.py — Tier 3 Phase A: per-call outcome tracking.

Records every CRITICAL or Q4 call as a row in outcomes.csv with the
representative-asset price at call time. Each daily run updates pending
rows with t+30 / t+60 / t+90-day max drawdowns from the call price.

True-positive rule (PRE-REGISTERED 2026-05-02): a call is a TRUE POSITIVE
if the representative asset experienced a >=20% peak-to-trough drawdown
from price_at_call within 90 days. 20% is the industry-standard
bear-market threshold (Bloomberg / Reuters / CFA Institute reference).
This rule is locked before any code; do not retune.

Patent reference: Claims 17 (detection-rate validation) and 18 (lead time).
"""

import os
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import yfinance as yf
import pandas as pd

# True-positive threshold: 20% peak-to-trough drawdown within 90 days
TP_DRAWDOWN_THRESHOLD = 0.20
TP_WINDOW_DAYS = 90

# Representative ticker per market (one canonical asset per basket)
REPRESENTATIVE_TICKER = {
    'Commodities':         'DBC',     # broad commodity ETF
    'Gold':                'GLD',
    'Silver':              'SLV',
    'Crypto (BTC)':        'BTC-USD',
    'Ethereum':            'ETH-USD',
    'US Equity (SPY)':     'SPY',
    'UK Equity (EWU)':     'EWU',
    'Germany (EWG)':       'EWG',
    'Bonds':               'TLT',
    'Emerging Markets':    'EEM',
}

# CSV schema (10 columns)
OUTCOMES_FIELDS = [
    'call_date', 'market', 'signal_type', 'quadrant',
    'ticker', 'price_at_call',
    'max_dd_30d', 'max_dd_60d', 'max_dd_90d',
    'status',
]

# Cache for fetched price series
_price_cache: Dict[str, pd.Series] = {}


def _outcomes_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'outcomes.csv')


def _fetch_prices(ticker: str, days_back: int = 400) -> Optional[pd.Series]:
    """Fetch close prices for a ticker, with simple in-process cache."""
    if ticker in _price_cache:
        return _price_cache[ticker]
    try:
        df = yf.download(ticker, period=f'{days_back}d', interval='1d',
                         progress=False, auto_adjust=False)
        if df is None or len(df) == 0:
            return None
        close = df['Close']
        if hasattr(close, 'columns'):
            close = close.iloc[:, 0]
        close = close.dropna()
        _price_cache[ticker] = close
        return close
    except Exception as e:
        print(f"  outcome_tracker: failed to fetch {ticker}: {e}")
        return None


def _max_drawdown_from(prices: pd.Series, call_date: pd.Timestamp,
                       window_days: int) -> Optional[float]:
    """
    Max peak-to-trough drawdown from call_date over window_days.

    Returns the deepest decline from the call price as a positive fraction
    (e.g., 0.23 for a 23% drawdown). Returns None if not enough data.
    """
    if prices is None or len(prices) == 0:
        return None
    end_date = call_date + pd.Timedelta(days=window_days)
    if prices.index[-1] < end_date:
        return None  # window not yet complete

    window = prices.loc[call_date:end_date]
    if len(window) < 2:
        return None
    price_at_call = float(window.iloc[0])
    min_after = float(window.iloc[1:].min())
    if price_at_call <= 0:
        return None
    dd = (price_at_call - min_after) / price_at_call
    return max(0.0, dd)


def _classify(max_dd_90d: Optional[float]) -> str:
    """Map 90d max drawdown to status."""
    if max_dd_90d is None:
        return 'pending'
    return 'true_positive' if max_dd_90d >= TP_DRAWDOWN_THRESHOLD else 'false_positive'


def load_outcomes() -> List[Dict]:
    path = _outcomes_path()
    if not os.path.exists(path):
        return []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def save_outcomes(rows: List[Dict]) -> None:
    path = _outcomes_path()
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTCOMES_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _is_tracked_signal(quadrant: str, regime: str) -> Optional[str]:
    """
    Decide whether today's signal warrants tracking.

    Track if quadrant is Q4 OR regime contains CRITICAL.
    Returns the signal_type string for outcomes.csv, or None to skip.
    """
    if quadrant == 'Q4':
        return 'Q4'
    if 'CRITICAL' in (regime or ''):
        return 'CRITICAL'
    return None


def track_new_calls(results: List[Dict], today: Optional[str] = None) -> int:
    """
    Append new tracked-signal rows to outcomes.csv for any market that
    is in CRITICAL/Q4 today AND wasn't already recorded for today.

    Returns the number of new rows added.
    """
    if today is None:
        today = datetime.now().strftime('%Y-%m-%d')

    rows = load_outcomes()
    existing_keys = {(r['call_date'], r['market']) for r in rows}
    added = 0

    for r in results:
        market = r.get('market')
        if not market or market not in REPRESENTATIVE_TICKER:
            continue
        signal_type = _is_tracked_signal(r.get('quadrant', ''), r.get('regime', ''))
        if signal_type is None:
            continue
        key = (today, market)
        if key in existing_keys:
            continue

        ticker = REPRESENTATIVE_TICKER[market]
        prices = _fetch_prices(ticker, days_back=30)
        if prices is None or len(prices) == 0:
            continue
        price_at_call = float(prices.iloc[-1])

        rows.append({
            'call_date': today,
            'market': market,
            'signal_type': signal_type,
            'quadrant': r.get('quadrant', ''),
            'ticker': ticker,
            'price_at_call': f"{price_at_call:.4f}",
            'max_dd_30d': '',
            'max_dd_60d': '',
            'max_dd_90d': '',
            'status': 'pending',
        })
        added += 1

    if added:
        # Sort by call_date desc then market for stable display
        rows.sort(key=lambda r: (r['call_date'], r['market']))
        save_outcomes(rows)
    return added


def update_pending_outcomes() -> int:
    """
    For every pending row in outcomes.csv, compute t+30/t+60/t+90 max
    drawdowns where data is available; update status when 90d window closes.

    Returns the number of rows updated.
    """
    rows = load_outcomes()
    if not rows:
        return 0

    updated = 0
    today = pd.Timestamp.today().normalize()

    for row in rows:
        if row.get('status') != 'pending':
            continue
        try:
            call_date = pd.Timestamp(row['call_date'])
        except Exception:
            continue
        ticker = row.get('ticker')
        if not ticker:
            continue

        prices = _fetch_prices(ticker, days_back=400)
        if prices is None:
            continue

        changed = False
        for window, field in ((30, 'max_dd_30d'), (60, 'max_dd_60d'),
                              (90, 'max_dd_90d')):
            if today < call_date + pd.Timedelta(days=window):
                continue  # window not yet complete
            if row.get(field):
                continue  # already computed
            dd = _max_drawdown_from(prices, call_date, window)
            if dd is not None:
                row[field] = f"{dd:.4f}"
                changed = True

        # Resolve status when 90d data is in
        if row.get('max_dd_90d'):
            try:
                dd90 = float(row['max_dd_90d'])
                row['status'] = _classify(dd90)
                changed = True
            except (ValueError, TypeError):
                pass

        if changed:
            updated += 1

    if updated:
        save_outcomes(rows)
    return updated


def compute_detection_stats(rows: Optional[List[Dict]] = None) -> Dict:
    """
    Aggregate outcomes for README headline rendering.

    Returns dict with:
        total_resolved, true_positives, false_positives, detection_rate,
        pending, by_market (dict of market -> {tp, fp, pending})
    """
    if rows is None:
        rows = load_outcomes()

    tp = sum(1 for r in rows if r.get('status') == 'true_positive')
    fp = sum(1 for r in rows if r.get('status') == 'false_positive')
    pending = sum(1 for r in rows if r.get('status') == 'pending')
    total_resolved = tp + fp
    rate = (tp / total_resolved * 100) if total_resolved else None

    by_market = {}
    for r in rows:
        m = r.get('market', 'Unknown')
        d = by_market.setdefault(m, {'tp': 0, 'fp': 0, 'pending': 0})
        s = r.get('status', 'pending')
        if s == 'true_positive':
            d['tp'] += 1
        elif s == 'false_positive':
            d['fp'] += 1
        else:
            d['pending'] += 1

    return {
        'total_resolved': total_resolved,
        'true_positives': tp,
        'false_positives': fp,
        'pending': pending,
        'detection_rate': rate,
        'by_market': by_market,
    }


def compute_systemic_score(results: List[Dict]) -> Dict:
    """
    Cross-market systemic regime score (patent Claim 16).

    Weighted sum of quadrants across all markets:
      Q4 = 3, Q3 = 2, Q2 = 1, Q1 = 0
    Range: 0 (all Q1) to 30 (all Q4) for 10 markets.
    Threshold: >= 15 = "ELEVATED SYSTEMIC RISK".

    Returns dict with: score, max_score, label.
    """
    weights = {'Q4': 3, 'Q3': 2, 'Q3*': 2, 'Q2': 1, 'Q1': 0, 'Q1*': 0}
    score = sum(weights.get(r.get('quadrant', ''), 0) for r in results)
    max_score = 3 * len(results)
    pct = (score / max_score * 100) if max_score else 0

    if pct >= 50:
        label = 'ELEVATED SYSTEMIC RISK'
        emoji = '🔴'
    elif pct >= 33:
        label = 'WATCH'
        emoji = '🟠'
    elif pct >= 17:
        label = 'NORMAL'
        emoji = '🟡'
    else:
        label = 'CALM'
        emoji = '🟢'

    return {
        'score': score,
        'max_score': max_score,
        'pct': pct,
        'label': label,
        'emoji': emoji,
    }


def render_recent_calls_table(rows: Optional[List[Dict]] = None,
                              limit_days: int = 90) -> str:
    """
    Render the auto-tracked Recent Calls table for the README.

    Replaces the static "Notable Calls (Audit Trail)" with live outcomes.
    """
    if rows is None:
        rows = load_outcomes()
    if not rows:
        return "_No tracked calls yet — outcomes accumulate from the first CRITICAL/Q4 entry going forward._"

    cutoff = pd.Timestamp.today() - pd.Timedelta(days=limit_days)
    recent = [
        r for r in rows
        if pd.Timestamp(r.get('call_date', '1970-01-01')) >= cutoff
    ]
    if not recent:
        return f"_No CRITICAL/Q4 calls in the last {limit_days} days._"

    recent.sort(key=lambda r: r['call_date'], reverse=True)

    lines = [
        "| Date | Market | Signal | Quadrant | T+30 DD | T+60 DD | T+90 DD | Status |",
        "|------|--------|--------|----------|---------|---------|---------|--------|",
    ]
    for r in recent:
        def _fmt_dd(s):
            try:
                return f"{float(s) * 100:.1f}%"
            except (ValueError, TypeError):
                return "_pending_"

        status = r.get('status', 'pending')
        if status == 'true_positive':
            status_str = "✅ True positive"
        elif status == 'false_positive':
            status_str = "⚪ Below threshold"
        else:
            status_str = "_pending_"

        lines.append(
            f"| {r.get('call_date', '--')} | {r.get('market', '--')} | "
            f"{r.get('signal_type', '--')} | {r.get('quadrant', '--')} | "
            f"{_fmt_dd(r.get('max_dd_30d'))} | {_fmt_dd(r.get('max_dd_60d'))} | "
            f"{_fmt_dd(r.get('max_dd_90d'))} | {status_str} |"
        )

    return "\n".join(lines)
