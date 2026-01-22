#!/usr/bin/env python3
"""
correction_detector.py - Detect corrections in equal-weighted baskets

Per the dashboard lift analysis:
- Correction threshold: >=15% drawdown from watermark
- Outcome window: 90 days from episode start

The watermark (high watermark) is the peak basket price since episode start.
A correction is detected when current basket price drops >=15% from watermark.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, NamedTuple


class CorrectionEvent(NamedTuple):
    """Represents a detected correction."""
    correction_date: date
    correction_magnitude: float  # Negative percentage (e.g., -18.5)
    watermark_price: float
    watermark_date: date
    trough_price: float
    lead_time_days: int  # Days from episode start to correction


def compute_basket_price(prices: pd.DataFrame, tickers: List[str]) -> pd.Series:
    """
    Compute equal-weighted basket price from constituent prices.

    Args:
        prices: DataFrame with ticker columns and date index
        tickers: List of tickers to include in basket

    Returns:
        Series of basket prices (equal-weighted average)
    """
    available = [t for t in tickers if t in prices.columns]
    if not available:
        return pd.Series(dtype=float)

    # Equal-weighted = simple mean of Close prices
    basket = prices[available].mean(axis=1)
    return basket


def detect_correction(
    prices: pd.DataFrame,
    tickers: List[str],
    episode: Dict,
    threshold: float = 0.15
) -> Optional[CorrectionEvent]:
    """
    Detect if a correction has occurred since episode start.

    A correction is detected when the equal-weighted basket drops
    >=threshold (default 15%) from its peak (watermark) since episode start.

    Args:
        prices: DataFrame with price data (must have 'Close' or ticker columns)
        tickers: List of tickers in this market's basket
        episode: Episode dict with 'start_date', 'watermark_price', 'watermark_date'
        threshold: Correction threshold as decimal (0.15 = 15%)

    Returns:
        CorrectionEvent if correction detected, None otherwise
    """
    if prices is None or prices.empty:
        return None

    # Parse episode start date
    start_date = episode.get('start_date')
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    # Compute basket
    basket = compute_basket_price(prices, tickers)
    if basket.empty:
        return None

    # Ensure index is datetime
    basket.index = pd.to_datetime(basket.index)

    # Filter to episode period
    episode_basket = basket[basket.index.date >= start_date]
    if episode_basket.empty:
        return None

    # Get watermark from episode or compute fresh
    stored_watermark = episode.get('watermark_price')
    stored_watermark_date = episode.get('watermark_date')

    if stored_watermark is not None:
        # Use stored watermark as starting point
        watermark_price = stored_watermark
        if isinstance(stored_watermark_date, str):
            watermark_date = datetime.strptime(stored_watermark_date, '%Y-%m-%d').date()
        else:
            watermark_date = stored_watermark_date
    else:
        # Compute watermark from scratch
        watermark_price = episode_basket.iloc[0]
        watermark_date = episode_basket.index[0].date()

    # Update watermark if we have new highs
    for idx, price in episode_basket.items():
        if price > watermark_price:
            watermark_price = price
            watermark_date = idx.date()

    # Check for correction (drawdown from watermark)
    current_price = episode_basket.iloc[-1]
    drawdown = (current_price - watermark_price) / watermark_price

    if drawdown <= -threshold:
        # Correction detected!
        # Find the exact date when threshold was first breached
        drawdowns = (episode_basket - watermark_price) / watermark_price

        # Find first date where drawdown exceeded threshold
        breach_mask = drawdowns <= -threshold
        if breach_mask.any():
            correction_date = breach_mask.idxmax().date()  # First True
        else:
            correction_date = episode_basket.index[-1].date()

        # Find trough (minimum price) for magnitude calculation
        trough_price = episode_basket.min()
        trough_drawdown = (trough_price - watermark_price) / watermark_price

        # Calculate lead time
        lead_time = (correction_date - start_date).days

        return CorrectionEvent(
            correction_date=correction_date,
            correction_magnitude=round(trough_drawdown * 100, 2),  # As percentage
            watermark_price=watermark_price,
            watermark_date=watermark_date,
            trough_price=trough_price,
            lead_time_days=lead_time
        )

    return None


def update_watermark(
    prices: pd.DataFrame,
    tickers: List[str],
    episode: Dict
) -> Dict:
    """
    Update episode watermark with latest price data.

    Args:
        prices: DataFrame with price data
        tickers: List of tickers in basket
        episode: Episode dict to update

    Returns:
        Updated episode dict with new watermark if applicable
    """
    if prices is None or prices.empty:
        return episode

    start_date = episode.get('start_date')
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    basket = compute_basket_price(prices, tickers)
    if basket.empty:
        return episode

    basket.index = pd.to_datetime(basket.index)
    episode_basket = basket[basket.index.date >= start_date]

    if episode_basket.empty:
        return episode

    # Current watermark
    current_watermark = episode.get('watermark_price', 0)

    # Check for new high
    max_price = episode_basket.max()
    if max_price > current_watermark:
        max_date = episode_basket.idxmax().date()
        episode['watermark_price'] = float(max_price)
        episode['watermark_date'] = max_date.strftime('%Y-%m-%d')

    return episode


def check_expiry(episode: Dict, window_days: int = 90) -> bool:
    """
    Check if episode has expired without correction.

    Args:
        episode: Episode dict with 'start_date'
        window_days: Maximum days to wait for correction

    Returns:
        True if episode has expired, False otherwise
    """
    start_date = episode.get('start_date')
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    expiry_date = start_date + timedelta(days=window_days)
    today = datetime.now().date()

    return today > expiry_date


if __name__ == "__main__":
    # Test with sample data
    print("Testing correction detector...")

    # Create sample prices
    dates = pd.date_range('2026-01-01', periods=60, freq='D')
    np.random.seed(42)

    # Simulate a market that peaks then corrects
    prices_data = {
        'GLD': 100 + np.cumsum(np.random.randn(60) * 0.5),
        'SLV': 50 + np.cumsum(np.random.randn(60) * 0.3),
    }

    # Add a correction scenario
    prices_data['GLD'][30:] -= 20  # Sudden drop at day 30
    prices_data['SLV'][30:] -= 10

    prices = pd.DataFrame(prices_data, index=dates)

    # Test episode
    episode = {
        'start_date': '2026-01-05',
        'watermark_price': None,
        'watermark_date': None
    }

    tickers = ['GLD', 'SLV']

    print(f"\nBasket prices (first 5):")
    basket = compute_basket_price(prices, tickers)
    print(basket.head())

    print(f"\nBasket prices (around correction):")
    print(basket.iloc[28:35])

    print(f"\nTesting correction detection...")
    result = detect_correction(prices, tickers, episode, threshold=0.15)

    if result:
        print(f"\nCorrection detected!")
        print(f"  Date: {result.correction_date}")
        print(f"  Magnitude: {result.correction_magnitude:.1f}%")
        print(f"  Watermark: {result.watermark_price:.2f} on {result.watermark_date}")
        print(f"  Trough: {result.trough_price:.2f}")
        print(f"  Lead time: {result.lead_time_days} days")
    else:
        print("\nNo correction detected")
