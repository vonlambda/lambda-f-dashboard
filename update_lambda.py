#!/usr/bin/env python3
"""
update_lambda.py - Compute Lambda-F and update public GitHub README

This script:
1. Fetches market data from Yahoo Finance
2. Computes Lambda-F (factor covariance non-commutativity)
3. Generates updated README content
4. Pushes to public GitHub repo via API
"""

import sys
import os

# Make canonical lambda_factors.py (in parent C:\backtesting\) importable.
# Append (not insert at 0) so the engine's own modules still take precedence
# when other scripts here do `from update_lambda import ...`.
_PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_DIR not in sys.path:
    sys.path.append(_PARENT_DIR)

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from github import Github
from dotenv import load_dotenv
import re
import json
import warnings
warnings.filterwarnings('ignore')

# Canonical Lambda-F implementation (Method C — winner of 2026-05-02 bakeoff)
from lambda_factors import compute_lambda_method_c

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REGIME_HISTORY_FILE = os.path.join(SCRIPT_DIR, 'regime_history.json')
SIGNAL_LOG_FILE = os.path.join(SCRIPT_DIR, 'SIGNAL_LOG.md')
ARCHIVE_DIR = os.path.join(SCRIPT_DIR, 'archive')
CHART_ARCHIVE_DIR = os.path.join(SCRIPT_DIR, 'assets', 'archive')

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')  # e.g., "yourusername/lambda-f-dashboard"

# ============================================================================
# Market Configuration
# ============================================================================

MARKETS = {
    'Commodities': {
        'tickers': ['GLD', 'SLV', 'USO', 'UNG', 'CPER', 'DBA'],
    },
    'Gold': {
        'tickers': ['GLD', 'SLV', 'GDX', 'GDXJ', 'UUP', 'TLT'],
    },
    'Silver': {
        'tickers': ['SLV', 'GLD', 'SIL', 'DBB', 'UUP', 'TIP'],
    },
    'Crypto (BTC)': {
        'tickers': ['BTC-USD', 'ETH-USD', 'LTC-USD', 'XRP-USD'],
    },
    'Ethereum': {
        'tickers': ['ETH-USD', 'BTC-USD', 'LTC-USD', 'XRP-USD', 'BNB-USD', 'ADA-USD'],
    },
    'US Equity (SPY)': {
        'tickers': ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLB'],
    },
    'UK Equity (EWU)': {
        'tickers': ['EWU', 'FXB', 'EWUS', 'EWL'],
    },
    'Germany (EWG)': {
        'tickers': ['EWG', 'EWL', 'EWN', 'EWO', 'FXE'],
    },
    'Bonds': {
        'tickers': ['SHY', 'IEF', 'TLT', 'LQD', 'HYG', 'TIP'],
    },
    'Emerging Markets': {
        'tickers': ['EEM', 'FXI', 'EWZ', 'EWW', 'EWY'],  # INDA excluded (inception 2012)
    }
}

# Lambda-F Parameters (validated on historical data)
WINDOW = 105
EMA_SPAN = 5
SMOOTH_DAYS = 14
LOOKBACK_DAYS = 252

# Correlation Parameters (for synchronized selloff detection)
CORR_WINDOW = 21  # Rolling correlation window
CORR_LOOKBACK = 252  # Percentile calculation lookback

# Outcome Tracking Parameters (matches dashboard lift analysis)
OUTCOME_CONFIG = {
    'correction_threshold': 0.15,    # 15% drawdown (from lift table)
    'outcome_window_days': 90,       # 90-day window (from lift table)
    'episode_merge_gap_days': 30,    # Merge if normal gap < 30d (from exclusion rule)
    'min_episode_duration': 3,       # Min 3 days elevated
    'reflexivity_threshold': 60,     # R >= 60 for Q4
}

# ============================================================================
# Lambda-F Calculation Functions
# ============================================================================

def fetch_data(tickers, days=900):
    """Fetch historical price data from Yahoo Finance (rolling window approach)"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    data = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            df = t.history(start=start_date, end=end_date, interval='1d')
            if not df.empty and len(df) > 100:
                df.index = pd.to_datetime(df.index.date)
                data[ticker] = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"  Warning: Failed to fetch {ticker}: {e}")
    
    if len(data) < 2:
        return None
    
    # Get common index
    common_idx = data[list(data.keys())[0]]['Close'].index
    for t in list(data.keys())[1:]:
        common_idx = common_idx.intersection(data[t]['Close'].index)
    common_idx = sorted(common_idx)
    
    # Build prices DataFrame
    # Causal: ffill only — bfill would use a future close to fill an
    # earlier missing close (lookahead). See docs/MASTER.md audit B-L1.
    prices = pd.DataFrame({
        t: data[t]['Close'].reindex(common_idx) for t in data.keys()
    }).ffill()

    return prices


def compute_returns(prices):
    """Compute log returns (matches paper methodology)"""
    return np.log(prices / prices.shift(1))


def compute_factors(returns_df, prices_df):
    """Compute market factors from returns"""
    returns_df = returns_df.dropna(how='all', axis=1).dropna()
    
    if len(returns_df.columns) < 2:
        return None
    
    n = len(returns_df.columns)
    
    # CMKT: Equal-weighted market
    cmkt = returns_df.mean(axis=1)
    
    # CSMB: Performance-based long-short factor (see paper Section 4.1)
    # Note: Called "Size Factor" in paper but uses performance ranking, not market cap
    perf_30 = prices_df.pct_change(30)
    perf_rank = perf_30.rank(axis=1, ascending=True)
    top = perf_rank > n / 2
    bottom = perf_rank <= n / 2
    csmb = returns_df[top].mean(axis=1) - returns_df[bottom].mean(axis=1)
    
    # CMOM: Momentum (14-day)
    mom_14 = prices_df.pct_change(14)
    mom_rank = mom_14.rank(axis=1, ascending=True)
    winners = mom_rank > n / 2
    losers = mom_rank <= n / 2
    cmom = returns_df[winners].mean(axis=1) - returns_df[losers].mean(axis=1)
    
    # CVOL: Volatility factor
    cvol = returns_df.rolling(14, min_periods=7).std().mean(axis=1)
    
    factors = pd.DataFrame({
        'CMKT': cmkt,
        'CSMB': csmb,
        'CMOM': cmom,
        'CVOL': cvol
    }).dropna()
    
    return factors


def compute_lambda_f(factors):
    """
    Compute Lambda-F: Non-commutativity of factor covariance evolution
    
    Lambda_F = ||[F, dF/dt]||_F / (||F||_F * ||dF/dt||_F)
    
    Where [A,B] = AB - BA is the matrix commutator
    
    Returns: (current_lambda, percentile, lambda_series)
    """
    if factors is None or len(factors) < WINDOW + 10:
        return None, None, None
    
    # EMA smoothing
    factors_smooth = factors.ewm(span=EMA_SPAN).mean()
    
    # Rolling standardization
    factors_std = (factors_smooth - factors_smooth.rolling(WINDOW).mean()) / \
                  (factors_smooth.rolling(WINDOW).std() + 1e-10)
    factors_std = factors_std.dropna()
    
    if len(factors_std) < WINDOW + 1:
        return None, None, None
    
    lambda_f = pd.Series(index=factors_std.index, dtype=float)
    
    for i in range(WINDOW, len(factors_std)):
        window_data = factors_std.iloc[i-WINDOW:i].values
        
        try:
            # Covariance matrix F(t)
            F_t = np.cov(window_data.T)
            
            if i > WINDOW:
                # Previous covariance F(t-1)
                prev_data = factors_std.iloc[i-WINDOW-1:i-1].values
                F_prev = np.cov(prev_data.T)
                
                # Numerical derivative dF/dt
                dF = F_t - F_prev
                
                # Commutator [F, dF] = F*dF - dF*F
                commutator = F_t @ dF - dF @ F_t
                
                # Frobenius norms
                norm_comm = np.linalg.norm(commutator, 'fro')
                norm_F = np.linalg.norm(F_t, 'fro')
                norm_dF = np.linalg.norm(dF, 'fro')
                
                # Lambda-F with log transform for numerical stability (validated)
                if norm_F * norm_dF > 1e-10:
                    raw = norm_comm / (norm_F * norm_dF)
                    lambda_f.iloc[i] = np.log1p(100 * raw)
        except Exception:
            continue
    
    # Smooth the output (validated: EWM span)
    lambda_f = lambda_f.ewm(span=SMOOTH_DAYS).mean()
    lambda_f = lambda_f.dropna()
    
    # Apply lag (validated parameter)
    lambda_f = lambda_f.shift(2)
    lambda_f = lambda_f.dropna()
    
    if len(lambda_f) < LOOKBACK_DAYS:
        return None, None, None
    
    # Current value and historical percentile
    current_lambda = lambda_f.iloc[-1]
    historical = lambda_f.iloc[-LOOKBACK_DAYS:-1]
    percentile = (historical < current_lambda).mean() * 100
    
    return current_lambda, percentile, lambda_f


def get_regime(lambda_series, lookback_days=252):
    """
    Classify regime based on trailing 30-day window detection logic.
    
    Detection Rules (matching paper):
    - CRITICAL: ≥3 days above P90 in trailing 30-day window
    - ELEVATED: ≥3 days above P75 (but <3 days above P90) in trailing 30-day window  
    - Normal: <3 days above P75 in trailing 30-day window
    
    Returns: regime string
    """
    if lambda_series is None or len(lambda_series) < 31:
        return "--"
    
    # Get trailing 30-day window (not including today for threshold calc)
    trailing_30 = lambda_series.iloc[-31:-1]
    current_value = lambda_series.iloc[-1]
    
    # Calculate thresholds from historical data (last LOOKBACK_DAYS)
    historical = lambda_series.iloc[-lookback_days:-1] if len(lambda_series) > lookback_days else lambda_series.iloc[:-1]
    p75 = historical.quantile(0.75)
    p90 = historical.quantile(0.90)
    
    # Count days above thresholds in trailing 30-day window (including today)
    trailing_31 = lambda_series.iloc[-31:]
    days_above_p75 = (trailing_31 > p75).sum()
    days_above_p90 = (trailing_31 > p90).sum()
    
    # Apply detection rules
    if days_above_p90 >= 3:
        return "**CRITICAL**"
    elif days_above_p75 >= 3:
        return "ELEVATED"
    else:
        return "Normal"


def get_current_percentile(lambda_series, lookback_days=252):
    """Get current Lambda-F percentile (expanding ex-ante, matches Method C bakeoff)."""
    if lambda_series is None or len(lambda_series) < 2:
        return None

    current_value = lambda_series.iloc[-1]
    historical = lambda_series.iloc[:-1]
    if len(historical) < lookback_days:
        return None
    percentile = (historical < current_value).mean() * 100
    return percentile


def get_days_elevated(lambda_series, lookback_days=252, trailing_days=31):
    """
    Get count of elevated days in the trailing window.
    Thresholds use expanding ex-ante history (matches Method C bakeoff).
    Returns tuple: (days_above_p75, days_above_p90)
    """
    if lambda_series is None or len(lambda_series) < trailing_days:
        return 0, 0

    historical = lambda_series.iloc[:-1]
    if len(historical) < lookback_days:
        return 0, 0
    p75 = historical.quantile(0.75)
    p90 = historical.quantile(0.90)

    trailing = lambda_series.iloc[-trailing_days:]
    days_p75 = int((trailing > p75).sum())
    days_p90 = int((trailing > p90).sum())
    return days_p75, days_p90


# ============================================================================
# Correlation Signal Functions (for synchronized selloff detection)
# ============================================================================

def compute_rolling_correlation(prices, window=21):
    """
    Compute rolling average pairwise correlation.
    
    This catches synchronized selloffs that Lambda-F misses (e.g., Q4 2018 US).
    """
    if prices is None or len(prices) < window + 10:
        return None
    
    returns = prices.pct_change().dropna()
    
    if len(returns) < window + 10:
        return None
    
    avg_corr = pd.Series(index=returns.index, dtype=float)
    
    for i in range(window, len(returns)):
        window_returns = returns.iloc[i-window:i]
        corr_matrix = window_returns.corr()
        
        # Extract upper triangle (excluding diagonal)
        n = len(corr_matrix)
        if n < 2:
            continue
        upper_tri = corr_matrix.values[np.triu_indices(n, k=1)]
        avg_corr.iloc[i] = upper_tri.mean()
    
    return avg_corr.dropna()


def get_correlation_percentile(avg_corr, lookback_days=252):
    """Get current correlation percentile (expanding ex-ante, matches Method C bakeoff)."""
    if avg_corr is None or len(avg_corr) < lookback_days + 1:
        return None

    current_value = avg_corr.iloc[-1]
    historical = avg_corr.iloc[:-1]
    percentile = (historical < current_value).mean() * 100
    return percentile


def get_combined_regime(lambda_series, corr_series, lookback_days=252):
    """
    Combined regime using both Lambda-F and Correlation signals.
    
    Two-signal system:
    - Lambda-F detects rotation (institutional repositioning)
    - Correlation detects synchronization (panic selloffs)
    
    Combined rules:
    - CRITICAL: Lambda-F >= P90 OR Correlation >= P90
    - ELEVATED: Lambda-F >= P75 OR Correlation >= P75
    - Normal: Neither signal elevated
    
    Returns: (regime, signal_source)
    - signal_source: 'L' (Lambda), 'C' (Correlation), 'LC' (both), '' (none)
    """
    lambda_elevated = False
    lambda_critical = False
    corr_elevated = False
    corr_critical = False
    
    # Check Lambda-F (expanding ex-ante percentile, matches Method C bakeoff)
    if lambda_series is not None and len(lambda_series) >= 31:
        historical = lambda_series.iloc[:-1]
        if len(historical) < lookback_days:
            return "Normal", ""
        p75 = historical.quantile(0.75)
        p90 = historical.quantile(0.90)
        
        trailing_31 = lambda_series.iloc[-31:]
        days_above_p75 = (trailing_31 > p75).sum()
        days_above_p90 = (trailing_31 > p90).sum()
        
        if days_above_p90 >= 3:
            lambda_critical = True
            lambda_elevated = True
        elif days_above_p75 >= 3:
            lambda_elevated = True
    
    # Check Correlation (current percentile)
    if corr_series is not None and len(corr_series) >= lookback_days + 1:
        corr_pct = get_correlation_percentile(corr_series, lookback_days)
        if corr_pct is not None:
            if corr_pct >= 90:
                corr_critical = True
                corr_elevated = True
            elif corr_pct >= 75:
                corr_elevated = True
    
    # Determine combined regime
    if lambda_critical or corr_critical:
        regime = "**CRITICAL**"
        if lambda_critical and corr_critical:
            source = "(LC)"
        elif lambda_critical:
            source = "(L)"
        else:
            source = "(C)"
    elif lambda_elevated or corr_elevated:
        regime = "ELEVATED"
        if lambda_elevated and corr_elevated:
            source = "(LC)"
        elif lambda_elevated:
            source = "(L)"
        else:
            source = "(C)"
    else:
        regime = "Normal"
        source = ""
    
    return regime, source


# ============================================================================
# Regime History Functions
# ============================================================================

def load_regime_history():
    """Load regime history from JSON file"""
    if os.path.exists(REGIME_HISTORY_FILE):
        try:
            with open(REGIME_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_regime_history(history):
    """Save regime history to JSON file"""
    with open(REGIME_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def update_regime_history(market_name, current_regime, history):
    """Update regime history, return 'since' date"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if market_name not in history:
        # First time seeing this market
        history[market_name] = {'regime': current_regime, 'since': today}
        return today
    
    if history[market_name]['regime'] != current_regime:
        # Regime changed - update since date
        history[market_name] = {'regime': current_regime, 'since': today}
        return today
    
    # Regime unchanged - return existing since date
    return history[market_name]['since']


def format_since_date(since_date):
    """Format date as ISO YYYY-MM-DD for clarity"""
    # Keep ISO format for unambiguous dates
    return since_date


# ============================================================================
# GitHub Update Functions
# ============================================================================

def compute_all_markets():
    """Compute Lambda-F and Correlation for all configured markets"""
    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Load regime history
    history = load_regime_history()
    
    for market_name, config in MARKETS.items():
        print(f"Processing {market_name}...")
        
        prices = fetch_data(config['tickers'])
        if prices is None:
            print(f"  No data for {market_name}")
            results.append({
                'market': market_name,
                'lambda_val': '--',
                'lambda_pct': '--',
                'lambda_days': '--',
                'corr_val': '--',
                'corr_pct': '--',
                'regime': '--',
                'since': '--',
                'date': today
            })
            continue
        
        if len(prices) < 200:
            print(f"  Insufficient price data for {market_name} ({len(prices)} days)")
            results.append({
                'market': market_name,
                'lambda_val': '--',
                'lambda_pct': '--',
                'lambda_days': '--',
                'corr_val': '--',
                'corr_pct': '--',
                'regime': '--',
                'since': '--',
                'date': today
            })
            continue
        
        # Compute Lambda-F via canonical Method C (z-scored returns directly
        # as factor matrix + 14d SMA smoothing). Replaces the prior inline
        # CMKT/CSMB/CMOM/CVOL pipeline (Method B). See docs/BAKEOFF_RESULTS.md
        # for the 2026-05-02 bakeoff that selected this method.
        current_lambda, _, lambda_series = compute_lambda_method_c(prices)
        
        # Compute Correlation
        corr_series = compute_rolling_correlation(prices, window=CORR_WINDOW)
        corr_pct = get_correlation_percentile(corr_series, lookback_days=CORR_LOOKBACK)
        current_corr = corr_series.iloc[-1] if corr_series is not None and len(corr_series) > 0 else None
        
        if current_lambda is None:
            print(f"  Insufficient data for {market_name}")
            results.append({
                'market': market_name,
                'lambda_val': '--',
                'lambda_pct': '--',
                'lambda_days': '--',
                'corr_val': '--',
                'corr_pct': '--',
                'regime': '--',
                'since': '--',
                'date': today
            })
        else:
            # Get percentiles
            lambda_pct = get_current_percentile(lambda_series, lookback_days=LOOKBACK_DAYS)
            
            # Get days elevated in trailing window (P75 and P90)
            days_p75, days_p90 = get_days_elevated(lambda_series, lookback_days=LOOKBACK_DAYS)
            
            # Combined two-signal regime detection
            regime, source = get_combined_regime(lambda_series, corr_series, lookback_days=LOOKBACK_DAYS)
            regime_display = f"{regime} {source}".strip()

            # Capture prior regime BEFORE history is mutated, so we can show
            # what changed today (Tier 1 T1.3 / T1.4 — Δ block + NEW badge)
            prior_regime = history.get(market_name, {}).get('regime')
            since_date = update_regime_history(market_name, regime_display, history)
            since_display = format_since_date(since_date)
            changed_today = (prior_regime is not None and prior_regime != regime_display)
            
            # Format values - show the relevant threshold count
            # If CRITICAL (P90 triggered), show P90 days; else show P75 days
            lambda_val_str = f"{current_lambda:.2f}"
            lambda_pct_str = f"{lambda_pct:.0f}%"
            if days_p90 >= 3:
                # CRITICAL - show P90 count with marker
                lambda_days_str = f"{days_p90}d*"
            elif days_p75 >= 3:
                # ELEVATED — match the regime classification rule (audit B1)
                lambda_days_str = f"{days_p75}d"
            else:
                lambda_days_str = "--"
            corr_val_str = f"{current_corr:.2f}" if current_corr is not None else "--"
            corr_pct_str = f"{corr_pct:.0f}%" if corr_pct is not None else "--"
            
            print(f"  L={lambda_val_str} ({lambda_pct_str}, {lambda_days_str}), C={corr_val_str} ({corr_pct_str}), {regime_display}, Since: {since_display}")
            
            results.append({
                'market': market_name,
                'lambda_val': lambda_val_str,
                'lambda_pct': lambda_pct_str,
                'lambda_days': lambda_days_str,  # Shows P90 count if CRITICAL, else P75 count
                'corr_val': corr_val_str,
                'corr_pct': corr_pct_str,
                'regime': regime_display,
                'prior_regime': prior_regime,
                'changed_today': changed_today,
                'since': since_display,
                'date': today
            })
    
    # Save updated regime history
    save_regime_history(history)
    
    return results


def _severity_emoji(regime):
    """Map a regime string to a severity emoji for at-a-glance reading."""
    if 'CRITICAL' in regime:
        return '🔴'
    if 'ELEVATED' in regime:
        return '🟠'
    if 'Normal' in regime:
        return '🟢'
    return '⚪'


def _severity_rank(regime):
    """Numeric severity for diff direction. Higher = more severe."""
    if 'CRITICAL' in regime:
        return 3
    if 'ELEVATED' in regime:
        return 2
    if 'Normal' in regime:
        return 1
    return 0


def _generate_diff_block(results):
    """Tier 1 T1.3: render 'what changed since yesterday' block.

    Shows entries that crossed regime boundaries today; lists unchanged
    markets compactly so readers know nothing was missed.
    """
    changed = [r for r in results if r.get('changed_today')]
    if not changed:
        return "_No regime changes since yesterday._"

    # Categorize: escalations (more severe today) vs de-escalations
    lines = []
    for r in changed:
        prior = r.get('prior_regime') or '--'
        now = r.get('regime', '--')
        prior_rank = _severity_rank(prior)
        now_rank = _severity_rank(now)
        emoji_now = _severity_emoji(now)
        # Strip source flag like "(L)" / "(LC)" for the headline arrow
        prior_label = prior.replace('**', '').split(' (')[0]
        now_label = now.replace('**', '').split(' (')[0]
        if now_rank > prior_rank:
            arrow = "↑"
        elif now_rank < prior_rank:
            arrow = "↓"
        else:
            arrow = "→"
        lines.append(f"- {emoji_now} **{r['market']}**: {prior_label} {arrow} {now_label}")

    unchanged = [r['market'] for r in results if not r.get('changed_today')]
    if unchanged:
        lines.append("")
        lines.append(f"_Unchanged: {', '.join(unchanged)}._")

    return "\n".join(lines)


def generate_table(results):
    """Generate markdown table from results with severity emojis, headline counts,
    Δ-since-yesterday block, and NEW badges (Tier 1: T1.1 / T1.2 / T1.3 / T1.4)."""
    n_crit = sum(1 for r in results if 'CRITICAL' in r.get('regime', ''))
    n_elev = sum(1 for r in results if 'ELEVATED' in r.get('regime', ''))
    n_norm = sum(1 for r in results if 'Normal' in r.get('regime', ''))
    n_na   = len(results) - n_crit - n_elev - n_norm

    headline_parts = [
        f"🔴 **{n_crit} CRITICAL**",
        f"🟠 **{n_elev} ELEVATED**",
        f"🟢 **{n_norm} NORMAL**",
    ]
    if n_na:
        headline_parts.append(f"⚪ {n_na} N/A")
    headline = " · ".join(headline_parts)

    today = datetime.now().strftime('%Y-%m-%d')
    diff_block = _generate_diff_block(results)

    lines = [
        headline,
        "",
        f"### Δ since yesterday",
        "",
        diff_block,
        "",
        "### Live signal table",
        "",
        "| Market | Lambda-F | L Pctl | Elev | Correlation | C Pctl | Regime | Since | Updated |",
        "|--------|----------|--------|------|-------------|--------|--------|-------|---------|",
    ]

    for r in results:
        emoji = _severity_emoji(r.get('regime', ''))
        new_badge = "🆕 " if r.get('changed_today') else ""
        market_with_emoji = f"{emoji} {new_badge}{r['market']}"
        lines.append(
            f"| {market_with_emoji} | {r.get('lambda_val', '--')} | {r.get('lambda_pct', '--')} | "
            f"{r.get('lambda_days', '--')} | {r.get('corr_val', '--')} | {r.get('corr_pct', '--')} | "
            f"{r['regime']} | {r.get('since', '--')} | {r['date']} |"
        )

    return "\n".join(lines)


def update_github_readme(results):
    """Push updated README to GitHub"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("ERROR: GITHUB_TOKEN or GITHUB_REPO not set in .env")
        return False
    
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Get current README
        readme_file = repo.get_contents("README.md")
        current_content = readme_file.decoded_content.decode('utf-8')
        
        # Generate new table
        new_table = generate_table(results)
        
        # Replace between markers
        pattern = r'<!-- LAMBDA_START -->.*?<!-- LAMBDA_END -->'
        replacement = f"<!-- LAMBDA_START -->\n{new_table}\n<!-- LAMBDA_END -->"
        new_content = re.sub(pattern, replacement, current_content, flags=re.DOTALL)
        
        # Only update if changed
        if new_content != current_content:
            repo.update_file(
                path="README.md",
                message=f"Update Lambda-F signals {datetime.now().strftime('%Y-%m-%d')}",
                content=new_content,
                sha=readme_file.sha
            )
            print("README.md updated successfully on GitHub")
        else:
            print("No changes to README.md")
        
        return True
        
    except Exception as e:
        print(f"Error updating GitHub: {e}")
        return False


# ============================================================================
# Audit Trail / Archiving Functions
# ============================================================================

def append_to_signal_log(results):
    """Append daily readings to SIGNAL_LOG.md (append-only audit trail)"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Build row data
    row_data = {'date': today}
    for r in results:
        market = r['market']
        pct = r.get('lambda_pct', '--')
        regime = r.get('regime', '--')
        
        # Format: "98% **C**" or "77% E" or "59%"
        if '**CRITICAL**' in regime:
            val = f"{pct} **C**"
        elif 'ELEVATED' in regime:
            val = f"{pct} E"
        else:
            val = pct
        
        # Map market names to short columns
        col_map = {
            'Commodities': 'commodities',
            'Gold': 'gold',
            'Silver': 'silver',
            'Crypto (BTC)': 'crypto',
            'Ethereum': 'ethereum',
            'US Equity (SPY)': 'us_eq',
            'UK Equity (EWU)': 'uk_eq',
            'Germany (EWG)': 'germany',
            'Bonds': 'bonds',
            'Emerging Markets': 'em'
        }
        if market in col_map:
            row_data[col_map[market]] = val
    
    # Build markdown row (ASCII-only — em-dashes/special chars cause encoding
    # corruption when this file is read on Windows without explicit utf-8)
    row = f"| {today} | {row_data.get('commodities', '--')} | {row_data.get('gold', '--')} | " \
          f"{row_data.get('silver', '--')} | {row_data.get('crypto', '--')} | " \
          f"{row_data.get('ethereum', '--')} | {row_data.get('us_eq', '--')} | " \
          f"{row_data.get('uk_eq', '--')} | {row_data.get('germany', '--')} | " \
          f"{row_data.get('bonds', '--')} | {row_data.get('em', '--')} | -- |"

    # Read existing log (utf-8 explicit — fixes mojibake bug)
    if os.path.exists(SIGNAL_LOG_FILE):
        with open(SIGNAL_LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Check if today's entry already exists
        if f"| {today} |" in content:
            print(f"SIGNAL_LOG.md: {today} entry already exists, skipping")
            return

        # Find last table row and append after it
        lines = content.rstrip().split('\n')
        lines.append(row)
        content = '\n'.join(lines) + '\n'
    else:
        # Create new log (ASCII-safe — no em-dashes or >= unicode)
        content = f"""# Lambda-F Signal History

*Append-only log. Each row is a cryptographically timestamped Git commit.*

| Date | Commodities | Gold | Crypto | US Eq | UK Eq | Germany | Bonds | EM | Events |
|------|-------------|------|--------|-------|-------|---------|-------|----|--------|
{row}

---

**Legend:**
- **C** = CRITICAL (>=3 days above P90 in trailing 30d)
- **E** = ELEVATED (>=3 days above P75 in trailing 30d)
- Percentages are ex-ante Lambda-F percentiles
- Events column filled retroactively when market moves occur
"""

    with open(SIGNAL_LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"SIGNAL_LOG.md: Appended {today} entry")


def archive_readme_snapshot(results, regime_changed=False):
    """Archive README snapshot on regime changes"""
    today = datetime.now().strftime('%Y-%m-%d')
    archive_path = os.path.join(ARCHIVE_DIR, f'{today}.md')
    
    # Only archive on regime changes or weekly (Sunday)
    is_sunday = datetime.now().weekday() == 6
    
    if not regime_changed and not is_sunday:
        return
    
    # Create archive dir if needed
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Skip if already archived today
    if os.path.exists(archive_path):
        return
    
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        readme = repo.get_contents('README.md')
        content = readme.decoded_content.decode('utf-8')
        
        # Add archive header
        header = f"""---
archived: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
trigger: {'regime_change' if regime_changed else 'weekly'}
---

"""
        with open(archive_path, 'w') as f:
            f.write(header + content)
        
        print(f"Archived README snapshot to {archive_path}")
        
    except Exception as e:
        print(f"Warning: Failed to archive README: {e}")


def archive_chart():
    """Archive live chart weekly"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Only archive on Sunday or when explicitly called
    is_sunday = datetime.now().weekday() == 6
    if not is_sunday:
        return
    
    os.makedirs(CHART_ARCHIVE_DIR, exist_ok=True)
    
    source = os.path.join(SCRIPT_DIR, 'live_signals.png')
    dest = os.path.join(CHART_ARCHIVE_DIR, f'live_signals_{today}.png')
    
    if os.path.exists(source) and not os.path.exists(dest):
        import shutil
        shutil.copy2(source, dest)
        print(f"Archived chart to {dest}")


def push_signal_log_to_github():
    """Push SIGNAL_LOG.md to GitHub"""
    if not os.path.exists(SIGNAL_LOG_FILE):
        return
    
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        with open(SIGNAL_LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        try:
            existing = repo.get_contents('SIGNAL_LOG.md')
            repo.update_file(
                'SIGNAL_LOG.md',
                f'Update signal log {datetime.now().strftime("%Y-%m-%d")}',
                content,
                existing.sha
            )
        except:
            repo.create_file(
                'SIGNAL_LOG.md',
                f'Create signal log {datetime.now().strftime("%Y-%m-%d")}',
                content
            )
        
        print("SIGNAL_LOG.md pushed to GitHub")
        
    except Exception as e:
        print(f"Warning: Failed to push signal log: {e}")


def check_regime_changes(results, history):
    """Check if any regime changed today"""
    for r in results:
        market = r['market']
        current_regime = r.get('regime', '--')
        
        if market in history:
            old_regime = history[market].get('regime', '')
            if old_regime != current_regime:
                return True
    return False


# ============================================================================
# Live Chart Generation
# ============================================================================

def generate_and_upload_live_chart():
    """Generate live signal chart showing only CRITICAL markets and upload to GitHub."""
    try:
        # Import the chart generator
        from generate_live_chart import generate_live_chart
        
        print("\n" + "=" * 60)
        print("Generating Live Signal Chart")
        print("=" * 60)
        
        chart_path = generate_live_chart()
        
        if chart_path and os.path.exists(chart_path):
            # Upload to GitHub
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(GITHUB_REPO)
            
            with open(chart_path, 'rb') as f:
                content = f.read()
            
            try:
                existing = repo.get_contents('assets/live_signals.png')
                repo.update_file(
                    'assets/live_signals.png',
                    f'Update live signal chart {datetime.now().strftime("%Y-%m-%d")}',
                    content,
                    existing.sha
                )
            except:
                repo.create_file(
                    'assets/live_signals.png',
                    f'Add live signal chart {datetime.now().strftime("%Y-%m-%d")}',
                    content
                )
            
            print("Live chart uploaded to GitHub")
            return True
    except Exception as e:
        print(f"Error generating/uploading live chart: {e}")
    
    return False


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Lambda-F Daily Update")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load previous regime history for change detection
    old_history = load_regime_history().copy()
    
    # Compute all markets
    results = compute_all_markets()
    
    # Check for regime changes
    new_history = load_regime_history()
    regime_changed = check_regime_changes(results, old_history)
    if regime_changed:
        print("\n*** REGIME CHANGE DETECTED ***")
    
    # Update GitHub README table
    print("\nPushing table to GitHub...")
    update_github_readme(results)
    
    # Generate and upload live chart
    generate_and_upload_live_chart()
    
    # === AUDIT TRAIL ===
    print("\n" + "-" * 60)
    print("Updating Audit Trail")
    print("-" * 60)
    
    # 1. Append to SIGNAL_LOG.md (always)
    append_to_signal_log(results)
    
    # 2. Push signal log to GitHub
    push_signal_log_to_github()
    
    # 3. Archive README on regime changes or weekly
    archive_readme_snapshot(results, regime_changed=regime_changed)
    
    # 4. Archive chart weekly
    archive_chart()

    # === EPISODE LIFECYCLE (Signal-to-Correction Matching) ===
    print("\n" + "-" * 60)
    print("Episode Lifecycle Management")
    print("-" * 60)

    try:
        from episode_manager import EpisodeManager
        from correction_detector import detect_correction
        from reflexivity_calculator import get_reflexivity, get_quadrant
        from outcome_recorder import record_outcome

        episode_mgr = EpisodeManager(os.path.join(SCRIPT_DIR, 'active_episodes.json'))

        # Check for expired episodes first
        episode_mgr.check_expiries()

        for r in results:
            market = r['market']
            if r['regime'] == '--':
                continue

            tickers = MARKETS[market]['tickers']

            # Fetch prices for this market (reuse if possible)
            prices = fetch_data(tickers)
            if prices is None:
                continue

            # Get reflexivity + quadrant
            reflexivity = get_reflexivity(market)
            lambda_pct_str = r.get('lambda_pct', '0%')
            lambda_pct = float(lambda_pct_str.replace('%', '')) if lambda_pct_str != '--' else 0
            quadrant = get_quadrant(lambda_pct, reflexivity)

            # Update episode state
            episode_mgr.update(
                market=market,
                regime=r['regime'],
                lambda_pct=lambda_pct,
                reflexivity=reflexivity,
                quadrant=quadrant,
                prices=prices,
                tickers=tickers
            )

            # Check for correction in active episodes
            if episode_mgr.has_active(market):
                episode = episode_mgr.get(market)
                correction = detect_correction(
                    prices=prices,
                    tickers=tickers,
                    episode=episode,
                    threshold=OUTCOME_CONFIG['correction_threshold']
                )
                if correction:
                    # Q4 = TRUE_POSITIVE, Q3 = PARTIAL
                    outcome = "TRUE_POSITIVE" if episode.get('quadrant') == "Q4" else "PARTIAL"
                    record_outcome(market, episode, correction, outcome)
                    episode_mgr.close(market, outcome)

        # Save updated episode state
        episode_mgr.save()

        # Print summary
        summary = episode_mgr.get_summary()
        if summary:
            print(f"  Active episodes: {len(summary)}")
            for market, info in summary.items():
                print(f"    {market}: {info['quadrant']}, {info['days_active']}d active, peak {info['peak']}%")
        else:
            print("  No active episodes")

        # Record any expired episodes as false positives
        for closed in episode_mgr.get_closed_episodes():
            if closed['episode'].get('outcome') == 'FALSE_POSITIVE':
                from outcome_recorder import record_false_positive
                record_false_positive(closed['market'], closed['episode'])

    except ImportError as e:
        print(f"  Warning: Episode lifecycle modules not available: {e}")
    except Exception as e:
        print(f"  Warning: Episode lifecycle error: {e}")

    print("\n" + "=" * 60)
    print("Update complete")
    print("=" * 60)

