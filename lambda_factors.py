#!/usr/bin/env python3
"""
Canonical Factor Definitions for Lambda-F
==========================================

This module provides the SINGLE source of truth for factor construction.
All other scripts should import from here to ensure consistency.

IMPORTANT: Do not modify factor definitions without updating validation!

Author: R.J. Mathews
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# VALIDATED PARAMETERS (DO NOT CHANGE WITHOUT RE-VALIDATION)
# =============================================================================

PARAMS = {
    # Lambda-F computation
    'WINDOW': 105,           # Covariance estimation window (~5 months)
    'EMA_SPAN': 5,           # Factor smoothing (exponential)
    'SMOOTH_DAYS': 14,       # Output smoothing
    'LAMBDA_LAG': 2,         # Lag to avoid look-ahead
    
    # Correlation signal
    'CORR_WINDOW': 21,       # Pairwise correlation window (~1 month)
    
    # Percentile calculation
    'LOOKBACK_DAYS': 252,    # Reference window (~1 year)
    'MIN_WARMUP': 252,       # Minimum data before computing percentiles
    
    # Detection thresholds
    'P75': 0.75,
    'P90': 0.90,
    'PERSISTENCE_DAYS': 3,   # Days above threshold to flag
}

# =============================================================================
# FACTOR CONSTRUCTION (CANONICAL DEFINITIONS)
# =============================================================================

def build_factors_crypto(prices: pd.DataFrame, volumes: pd.DataFrame = None) -> pd.DataFrame:
    """
    Build factors for crypto assets.
    
    Uses:
    - PCT returns (not log returns)
    - Equal-weighted CMKT
    - Performance-based ranking for CSMB (30-day)
    - Momentum-based ranking for CMOM (14-day)
    - Dollar volume z-score for CVOL (if volumes provided)
    
    Args:
        prices: DataFrame with asset prices (columns = assets, index = dates)
        volumes: DataFrame with asset volumes (optional)
    
    Returns:
        DataFrame with factor returns: CMKT, CSMB, CMOM, CVOL
    """
    returns = prices.pct_change()
    n = len(prices.columns)
    
    if n < 2:
        return None
    
    # CMKT: Equal-weighted market return
    cmkt = returns.mean(axis=1)
    
    # CSMB: Long top half by 30-day performance, short bottom half
    perf_30 = prices.pct_change(30)
    perf_rank = perf_30.rank(axis=1, ascending=True)
    top = perf_rank > n / 2
    bottom = perf_rank <= n / 2
    csmb = returns[top].mean(axis=1) - returns[bottom].mean(axis=1)
    
    # CMOM: Momentum (14-day lookback)
    mom_14 = prices.pct_change(14)
    mom_rank = mom_14.rank(axis=1, ascending=True)
    winners = mom_rank > n / 2
    losers = mom_rank <= n / 2
    cmom = returns[winners].mean(axis=1) - returns[losers].mean(axis=1)
    
    # CVOL: Volume factor (dollar volume z-score)
    if volumes is not None and len(volumes) > 0:
        dollar_vol = volumes * prices
        cvol = np.log1p(dollar_vol).mean(axis=1)
        cvol = (cvol - cvol.rolling(30).mean()) / (cvol.rolling(30).std() + 1e-8)
    else:
        # Fallback: volatility-based
        cvol = returns.rolling(14, min_periods=7).std().mean(axis=1)
    
    factors = pd.DataFrame({
        'CMKT': cmkt,
        'CSMB': csmb,
        'CMOM': cmom,
        'CVOL': cvol
    }).dropna()
    
    return factors


def build_factors_etf(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Build factors for ETF-based markets (equities, commodities).
    
    Same methodology as crypto, but typically no volume normalization needed.
    
    Args:
        prices: DataFrame with ETF prices
    
    Returns:
        DataFrame with factor returns: CMKT, CSMB, CMOM, CVOL
    """
    returns = prices.pct_change()
    n = len(prices.columns)
    
    if n < 2:
        return None
    
    # CMKT: Equal-weighted
    cmkt = returns.mean(axis=1)
    
    # CSMB: Performance-based (30-day)
    perf_30 = prices.pct_change(30)
    perf_rank = perf_30.rank(axis=1, ascending=True)
    top = perf_rank > n / 2
    bottom = perf_rank <= n / 2
    csmb = returns[top].mean(axis=1) - returns[bottom].mean(axis=1)
    
    # CMOM: Momentum (14-day)
    mom_14 = prices.pct_change(14)
    mom_rank = mom_14.rank(axis=1, ascending=True)
    winners = mom_rank > n / 2
    losers = mom_rank <= n / 2
    cmom = returns[winners].mean(axis=1) - returns[losers].mean(axis=1)
    
    # CVOL: Volatility factor
    cvol = returns.rolling(14, min_periods=7).std().mean(axis=1)
    
    factors = pd.DataFrame({
        'CMKT': cmkt,
        'CSMB': csmb,
        'CMOM': cmom,
        'CVOL': cvol
    }).dropna()
    
    return factors


# =============================================================================
# LAMBDA-F COMPUTATION
# =============================================================================

def compute_lambda_f(factors: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[pd.Series]]:
    """
    Compute Lambda-F: Non-commutativity of factor covariance evolution.
    
    Formula: Lambda_F = ||[F, dF/dt]||_F / (||F||_F * ||dF/dt||_F)
    
    Where [A, B] = AB - BA is the matrix commutator.
    
    Args:
        factors: DataFrame with factor returns (from build_factors_*)
    
    Returns:
        Tuple of (current_lambda, percentile, full_series)
        Returns (None, None, None) if insufficient data
    """
    p = PARAMS
    
    if factors is None or len(factors) < p['WINDOW'] + 10:
        return None, None, None
    
    # EMA smoothing
    factors_smooth = factors.ewm(span=p['EMA_SPAN']).mean()
    
    # Rolling standardization
    factors_std = (factors_smooth - factors_smooth.rolling(p['WINDOW']).mean()) / \
                  (factors_smooth.rolling(p['WINDOW']).std() + 1e-10)
    factors_std = factors_std.dropna()
    
    if len(factors_std) < p['WINDOW'] + 1:
        return None, None, None
    
    lambda_f = pd.Series(index=factors_std.index, dtype=float)
    
    for i in range(p['WINDOW'], len(factors_std)):
        window_data = factors_std.iloc[i-p['WINDOW']:i].values
        
        try:
            # Covariance matrix F(t)
            F_t = np.cov(window_data.T)
            
            if i > p['WINDOW']:
                # Previous covariance F(t-1)
                prev_data = factors_std.iloc[i-p['WINDOW']-1:i-1].values
                F_prev = np.cov(prev_data.T)
                
                # Numerical derivative dF/dt
                dF = F_t - F_prev
                
                # Commutator [F, dF] = F*dF - dF*F
                commutator = F_t @ dF - dF @ F_t
                
                # Frobenius norms
                norm_comm = np.linalg.norm(commutator, 'fro')
                norm_F = np.linalg.norm(F_t, 'fro')
                norm_dF = np.linalg.norm(dF, 'fro')
                
                # Lambda-F with log transform
                if norm_F * norm_dF > 1e-10:
                    raw = norm_comm / (norm_F * norm_dF)
                    lambda_f.iloc[i] = np.log1p(100 * raw)
        except Exception:
            continue
    
    # Smooth and lag
    lambda_f = lambda_f.ewm(span=p['SMOOTH_DAYS']).mean()
    lambda_f = lambda_f.shift(p['LAMBDA_LAG'])
    lambda_f = lambda_f.dropna()
    
    if len(lambda_f) < p['LOOKBACK_DAYS']:
        return None, None, None
    
    # Current value and percentile (trailing window only)
    current_lambda = lambda_f.iloc[-1]
    historical = lambda_f.iloc[-p['LOOKBACK_DAYS']:-1]
    percentile = (historical < current_lambda).mean() * 100
    
    return current_lambda, percentile, lambda_f


# =============================================================================
# CANONICAL LAMBDA-F (Method C — winner of 2026-05-02 bakeoff)
# =============================================================================
#
# Method C uses standardized z-scored asset returns DIRECTLY as the factor
# matrix (no CMKT/CSMB/CMOM/CVOL construction), with 14-day SMA output
# smoothing and expanding ex-ante percentile reference.
#
# Method C was selected in the 2026-05-02 bakeoff (won both scoring rules,
# stable across full / ex-2y / ex-5y subsets, longest mean lead time). The
# backtest figures formerly quoted here (78.7% detection at 26.85% FPR on a
# 47-event ledger, citing docs/BAKEOFF_RESULTS.md) referenced a ledger and a
# document never committed to this repository and are withdrawn (2026-07-28)
# -- see METHODOLOGY.md, Validation.
#
# All production code paths (update_lambda.py + validate_*.py) should call
# compute_lambda_method_c(prices). The legacy compute_lambda_f(factors) is
# preserved for backward compatibility with compute_false_positives.py.

def compute_lambda_method_c(prices: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[pd.Series]]:
    """
    Canonical Lambda-F using standardized z-scored returns as factor matrix.

    Args:
        prices: DataFrame with asset close prices (columns = tickers, index = dates)

    Returns:
        (current_lambda, percentile, full_series)
        Percentile uses expanding ex-ante window (min_periods=252).
        Returns (None, None, None) if insufficient data.
    """
    p = PARAMS

    if prices is None or len(prices) < p['WINDOW'] + 50:
        return None, None, None

    returns = prices.pct_change().dropna()
    if len(returns.columns) < 2:
        return None, None, None

    smoothed = returns.ewm(span=p['EMA_SPAN']).mean()
    standardized = (smoothed - smoothed.rolling(p['WINDOW']).mean()) / \
                   (smoothed.rolling(p['WINDOW']).std() + 1e-8)
    standardized = standardized.dropna()

    if len(standardized) < p['WINDOW'] + 1:
        return None, None, None

    F_series = []
    for t in range(p['WINDOW'], len(standardized)):
        wd = standardized.iloc[t - p['WINDOW']: t]
        F_t = wd.cov().values
        F_series.append({'date': standardized.index[t], 'F_t': F_t})

    rows = []
    for i in range(1, len(F_series)):
        F_t = F_series[i]['F_t']
        F_dot = F_t - F_series[i - 1]['F_t']
        comm = F_t @ F_dot - F_dot @ F_t
        nc = np.linalg.norm(comm, 'fro')
        nF = np.linalg.norm(F_t, 'fro')
        nFd = np.linalg.norm(F_dot, 'fro')
        raw = nc / (nF * nFd + 1e-8)
        rows.append({'date': F_series[i]['date'], 'lambda_F': np.log1p(raw * 100)})

    if not rows:
        return None, None, None

    lambda_series = pd.DataFrame(rows).set_index('date')['lambda_F']
    lambda_series = lambda_series.rolling(p['SMOOTH_DAYS'], min_periods=1).mean()
    lambda_series = lambda_series.shift(p['LAMBDA_LAG'])
    lambda_series = lambda_series.dropna()

    if len(lambda_series) < p['LOOKBACK_DAYS']:
        return None, None, None

    current_lambda = lambda_series.iloc[-1]
    historical = lambda_series.iloc[:-1]
    percentile = (historical < current_lambda).mean() * 100

    return current_lambda, percentile, lambda_series


# =============================================================================
# CORRELATION SIGNAL
# =============================================================================

def compute_correlation(prices: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[pd.Series]]:
    """
    Compute rolling average pairwise correlation.
    
    Detects synchronized selloffs (all assets moving together).
    
    Args:
        prices: DataFrame with asset prices
    
    Returns:
        Tuple of (current_corr, percentile, full_series)
    """
    p = PARAMS
    
    if prices is None or len(prices) < p['CORR_WINDOW'] + 10:
        return None, None, None
    
    returns = prices.pct_change().dropna()
    
    if len(returns) < p['CORR_WINDOW'] + 10:
        return None, None, None
    
    avg_corr = pd.Series(index=returns.index, dtype=float)
    
    for i in range(p['CORR_WINDOW'], len(returns)):
        window_returns = returns.iloc[i-p['CORR_WINDOW']:i]
        corr_matrix = window_returns.corr()
        
        n = len(corr_matrix)
        if n < 2:
            continue
        upper_tri = corr_matrix.values[np.triu_indices(n, k=1)]
        avg_corr.iloc[i] = upper_tri.mean()
    
    avg_corr = avg_corr.dropna()
    
    if len(avg_corr) < p['LOOKBACK_DAYS']:
        return None, None, None
    
    current_corr = avg_corr.iloc[-1]
    historical = avg_corr.iloc[-p['LOOKBACK_DAYS']:-1]
    percentile = (historical < current_corr).mean() * 100
    
    return current_corr, percentile, avg_corr


# =============================================================================
# REGIME CLASSIFICATION
# =============================================================================

def classify_regime(lambda_series: pd.Series, corr_series: pd.Series = None) -> Tuple[str, str]:
    """
    Classify market regime using two-signal system.
    
    Detection Rules (trailing 30-day window):
    - CRITICAL: >=3 days above P90 (Lambda) OR >=3 days above P95 (Correlation)
    - ELEVATED: >=3 days above P75 (Lambda) OR >=3 days above P90 (Correlation)
    - Normal: Below thresholds
    
    Args:
        lambda_series: Full Lambda-F series
        corr_series: Full correlation series (optional)
    
    Returns:
        Tuple of (regime_string, signal_source)
        signal_source: 'L', 'C', 'LC', or ''
    """
    p = PARAMS
    
    lambda_elevated = False
    lambda_critical = False
    corr_elevated = False
    corr_critical = False
    
    # Check Lambda-F (trailing 30-day window)
    if lambda_series is not None and len(lambda_series) >= 31:
        historical = lambda_series.iloc[-p['LOOKBACK_DAYS']:-1] if len(lambda_series) > p['LOOKBACK_DAYS'] else lambda_series.iloc[:-1]
        p75 = historical.quantile(p['P75'])
        p90 = historical.quantile(p['P90'])
        
        trailing_30 = lambda_series.iloc[-31:]
        days_above_p75 = (trailing_30 > p75).sum()
        days_above_p90 = (trailing_30 > p90).sum()
        
        if days_above_p90 >= p['PERSISTENCE_DAYS']:
            lambda_critical = True
            lambda_elevated = True
        elif days_above_p75 >= p['PERSISTENCE_DAYS']:
            lambda_elevated = True
    
    # Check Correlation (current percentile)
    if corr_series is not None and len(corr_series) >= p['LOOKBACK_DAYS'] + 1:
        historical = corr_series.iloc[-p['LOOKBACK_DAYS']:-1]
        current = corr_series.iloc[-1]
        corr_pct = (historical < current).mean() * 100
        
        if corr_pct >= 95:
            corr_critical = True
            corr_elevated = True
        elif corr_pct >= 90:
            corr_elevated = True
    
    # Combine signals
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


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def compute_false_positive_rate(lambda_series: pd.Series, threshold_percentile: float = 0.75) -> dict:
    """
    Compute false positive rate: days in elevated/critical per year.
    
    This is critical for understanding the baseline rate of signals.
    
    Args:
        lambda_series: Full Lambda-F series
        threshold_percentile: P75 or P90
    
    Returns:
        Dict with 'days_elevated', 'days_per_year', 'total_years'
    """
    if lambda_series is None or len(lambda_series) < 252:
        return None
    
    threshold = lambda_series.quantile(threshold_percentile)
    days_elevated = (lambda_series > threshold).sum()
    total_days = len(lambda_series)
    total_years = total_days / 252
    days_per_year = days_elevated / total_years
    
    return {
        'threshold': threshold,
        'days_elevated': int(days_elevated),
        'total_days': total_days,
        'total_years': round(total_years, 1),
        'days_per_year': round(days_per_year, 1),
        'pct_elevated': round(100 * days_elevated / total_days, 1)
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'PARAMS',
    'compute_lambda_method_c',  # canonical (winner of 2026-05-02 bakeoff)
    'compute_correlation',
    'classify_regime',
    'compute_false_positive_rate',
    # Legacy (kept for backward compatibility — see docs/MASTER.md §3):
    'build_factors_crypto',
    'build_factors_etf',
    'compute_lambda_f',
]

