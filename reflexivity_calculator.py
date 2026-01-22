#!/usr/bin/env python3
"""
reflexivity_calculator.py - Calculate reflexivity score for game-theoretic classification

Reflexivity components (per paper Section 5):
1. Leverage (funding rates, margin debt)
2. Sentiment (Fear & Greed index)

Quadrant classification:
- Q1: Low Lambda-F, Low Reflexivity (STABLE)
- Q2: Low Lambda-F, High Reflexivity (FRAGILE)
- Q3: High Lambda-F, Low Reflexivity (ROTATING)
- Q4: High Lambda-F, High Reflexivity (CRITICAL - crash risk)

Only Q4 episodes count as TRUE_POSITIVE when correction occurs.
"""

import requests
from typing import Optional, Dict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Reflexivity thresholds (from paper)
REFLEXIVITY_THRESHOLD = 60  # R >= 60 for "high" reflexivity
LAMBDA_ELEVATED_PCT = 75    # Lambda-F >= P75 for "elevated"

# Funding rate scoring (annualized)
FUNDING_THRESHOLDS = {
    50: 100,   # >50% annual = max score
    20: 75,    # >20% annual
    10: 50,    # >10% annual
    0: 25,     # >0% (bullish)
}

# Cache for API responses (simple in-memory)
_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def _get_cached(key: str) -> Optional[any]:
    """Get cached value if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if (datetime.now() - timestamp).seconds < CACHE_TTL_SECONDS:
            return value
    return None


def _set_cache(key: str, value: any) -> None:
    """Set cached value with timestamp."""
    _cache[key] = (value, datetime.now())


def fetch_fear_greed() -> Optional[int]:
    """
    Fetch Crypto Fear & Greed Index from alternative.me
    Returns: Value 0-100 (0=Extreme Fear, 100=Extreme Greed)
    """
    cached = _get_cached('fear_greed')
    if cached is not None:
        return cached

    try:
        response = requests.get(
            'https://api.alternative.me/fng/',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            value = int(data['data'][0]['value'])
            _set_cache('fear_greed', value)
            return value
    except Exception as e:
        print(f"  Warning: Failed to fetch Fear & Greed: {e}")

    return None


def fetch_btc_funding_rate() -> Optional[float]:
    """
    Fetch BTC perpetual funding rate from CoinGecko derivatives API.
    Returns: Annualized funding rate as percentage (e.g., 25.5 for 25.5%)
    """
    cached = _get_cached('btc_funding')
    if cached is not None:
        return cached

    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/derivatives',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            # Find BTC perpetual swaps
            btc_perps = [
                d for d in data
                if 'BTC' in d.get('symbol', '').upper()
                and d.get('contract_type') == 'perpetual'
            ]
            if btc_perps:
                # Average funding rate across exchanges
                rates = [
                    float(p.get('funding_rate', 0)) * 100  # Convert to percentage
                    for p in btc_perps
                    if p.get('funding_rate') is not None
                ]
                if rates:
                    avg_rate = sum(rates) / len(rates)
                    # Annualize (8h funding * 3 * 365)
                    annual_rate = avg_rate * 3 * 365
                    _set_cache('btc_funding', annual_rate)
                    return annual_rate
    except Exception as e:
        print(f"  Warning: Failed to fetch BTC funding rate: {e}")

    return None


def score_funding_rate(annual_rate: Optional[float]) -> int:
    """
    Convert annualized funding rate to score 0-100.
    Higher funding = more leveraged longs = higher reflexivity risk.
    """
    if annual_rate is None:
        return 50  # Neutral if unavailable

    for threshold, score in sorted(FUNDING_THRESHOLDS.items(), reverse=True):
        if annual_rate > threshold:
            return score

    return 0  # Negative funding (shorts paying longs)


def get_reflexivity(market: str) -> Optional[float]:
    """
    Calculate composite reflexivity score for a market.

    For crypto markets: Average of funding rate score and Fear & Greed
    For non-crypto: Returns None (reflexivity data not available)

    Returns: Reflexivity score 0-100, or None if unavailable
    """
    # Only crypto markets have reliable reflexivity data
    crypto_markets = ['Crypto (BTC)', 'Ethereum']

    if market not in crypto_markets:
        # For non-crypto, we don't have reliable reflexivity data
        # Return None to indicate Q4 classification not possible
        return None

    # Fetch components
    fear_greed = fetch_fear_greed()
    funding_rate = fetch_btc_funding_rate()
    funding_score = score_funding_rate(funding_rate)

    # Compute composite
    if fear_greed is not None:
        # Average of sentiment and leverage
        reflexivity = (fear_greed + funding_score) / 2
    else:
        # Use funding alone if sentiment unavailable
        reflexivity = funding_score

    return reflexivity


def get_quadrant(lambda_pct: float, reflexivity: Optional[float]) -> str:
    """
    Determine game-theoretic quadrant based on Lambda-F and reflexivity.

    Returns:
        Q1: STABLE (low Lambda, low reflexivity)
        Q2: FRAGILE (low Lambda, high reflexivity)
        Q3: ROTATING (high Lambda, low reflexivity)
        Q4: CRITICAL (high Lambda, high reflexivity)
        Q3* (with asterisk): High Lambda but reflexivity unavailable
    """
    high_lambda = lambda_pct >= LAMBDA_ELEVATED_PCT

    if reflexivity is None:
        # Reflexivity data unavailable (non-crypto markets)
        return "Q3*" if high_lambda else "Q1*"

    high_reflexivity = reflexivity >= REFLEXIVITY_THRESHOLD

    if high_lambda:
        return "Q4" if high_reflexivity else "Q3"
    else:
        return "Q2" if high_reflexivity else "Q1"


def get_reflexivity_components(market: str) -> Dict[str, any]:
    """
    Get detailed reflexivity breakdown for debugging/display.

    Returns dict with:
        - fear_greed: int or None
        - funding_rate_annual: float or None
        - funding_score: int
        - composite: float or None
    """
    fear_greed = fetch_fear_greed() if market in ['Crypto (BTC)', 'Ethereum'] else None
    funding_rate = fetch_btc_funding_rate() if market in ['Crypto (BTC)', 'Ethereum'] else None
    funding_score = score_funding_rate(funding_rate)

    composite = get_reflexivity(market)

    return {
        'fear_greed': fear_greed,
        'funding_rate_annual': funding_rate,
        'funding_score': funding_score,
        'composite': composite
    }


if __name__ == "__main__":
    # Test reflexivity calculation
    print("Testing reflexivity calculator...")
    print()

    for market in ['Crypto (BTC)', 'Ethereum', 'Commodities', 'US Equity (SPY)']:
        print(f"Market: {market}")
        components = get_reflexivity_components(market)
        print(f"  Fear & Greed: {components['fear_greed']}")
        print(f"  Funding Rate (annual): {components['funding_rate_annual']:.1f}%" if components['funding_rate_annual'] else "  Funding Rate: N/A")
        print(f"  Funding Score: {components['funding_score']}")
        print(f"  Composite Reflexivity: {components['composite']:.1f}" if components['composite'] else "  Composite: N/A")

        # Test quadrant classification
        for lambda_pct in [50, 80]:
            quadrant = get_quadrant(lambda_pct, components['composite'])
            print(f"  Lambda {lambda_pct}% -> {quadrant}")
        print()
