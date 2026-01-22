#!/usr/bin/env python3
"""
episode_manager.py - Manage signal episode lifecycle

An "episode" is a period where a market is in ELEVATED or CRITICAL regime.
Episodes track:
- Start date (when regime became elevated)
- Peak signal (highest Lambda-F percentile during episode)
- Quadrant (Q1-Q4 based on Lambda-F + reflexivity)
- Watermark (peak basket price for correction detection)
- Expiry (90 days from start)

Episode merging:
If a market goes ELEVATED -> NORMAL -> ELEVATED within 30 days,
the episodes are merged into one continuous episode.
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
import pandas as pd

from correction_detector import compute_basket_price, update_watermark

# Configuration (matches dashboard parameters)
EPISODE_MERGE_GAP_DAYS = 30  # Merge episodes if gap < 30 days
OUTCOME_WINDOW_DAYS = 90     # Max days to wait for correction
MIN_EPISODE_DURATION = 3     # Min days elevated to count as episode


class EpisodeManager:
    """Manages active signal episodes across all markets."""

    def __init__(self, filepath: str):
        """
        Initialize episode manager.

        Args:
            filepath: Path to active_episodes.json
        """
        self.filepath = filepath
        self.episodes = self._load()
        self._closed_episodes: List[Dict] = []  # Episodes closed this run

    def _load(self) -> Dict:
        """Load episodes from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save(self) -> None:
        """Save episodes to JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(self.episodes, f, indent=2, default=str)

    def has_active(self, market: str) -> bool:
        """Check if market has an active episode."""
        return market in self.episodes and self.episodes[market].get('status') == 'ACTIVE'

    def get(self, market: str) -> Optional[Dict]:
        """Get episode for market, or None if not exists."""
        return self.episodes.get(market)

    def get_closed_episodes(self) -> List[Dict]:
        """Get episodes that were closed during this run."""
        return self._closed_episodes

    def update(
        self,
        market: str,
        regime: str,
        lambda_pct: float,
        reflexivity: Optional[float],
        quadrant: str,
        prices: pd.DataFrame,
        tickers: List[str]
    ) -> None:
        """
        Update episode state for a market.

        Args:
            market: Market name (e.g., 'Commodities')
            regime: Current regime string (e.g., '**CRITICAL** (L)')
            lambda_pct: Current Lambda-F percentile
            reflexivity: Current reflexivity score (or None)
            quadrant: Current quadrant (Q1-Q4)
            prices: Price DataFrame for watermark tracking
            tickers: List of tickers in this market
        """
        today = datetime.now().date()
        is_elevated = 'CRITICAL' in regime or 'ELEVATED' in regime

        if market in self.episodes:
            episode = self.episodes[market]

            if is_elevated:
                # Update existing episode
                self._update_episode(
                    market, episode, lambda_pct, reflexivity, quadrant, prices, tickers
                )
            else:
                # Market returned to normal
                self._handle_normal(market, episode, today)
        else:
            # No existing episode
            if is_elevated:
                # Start new episode
                self._create_episode(
                    market, regime, lambda_pct, reflexivity, quadrant, prices, tickers
                )

    def _create_episode(
        self,
        market: str,
        regime: str,
        lambda_pct: float,
        reflexivity: Optional[float],
        quadrant: str,
        prices: pd.DataFrame,
        tickers: List[str]
    ) -> None:
        """Create a new episode for a market."""
        today = datetime.now().date()

        # Determine trigger type from regime string
        if '(LC)' in regime:
            trigger_type = 'LC'
        elif '(L)' in regime:
            trigger_type = 'L'
        elif '(C)' in regime:
            trigger_type = 'C'
        else:
            trigger_type = 'L'  # Default

        # Compute initial watermark
        basket = compute_basket_price(prices, tickers) if prices is not None else None
        if basket is not None and not basket.empty:
            watermark_price = float(basket.iloc[-1])
            watermark_date = today.strftime('%Y-%m-%d')
        else:
            watermark_price = None
            watermark_date = None

        # Generate episode ID
        prefix = market[:4].upper().replace(' ', '').replace('(', '').replace(')', '')
        episode_id = f"{prefix}-{today.strftime('%Y-%m-%d')}"

        self.episodes[market] = {
            'episode_id': episode_id,
            'start_date': today.strftime('%Y-%m-%d'),
            'trigger_type': trigger_type,
            'peak_lambda_pct': lambda_pct,
            'peak_corr_pct': None,  # Updated separately if needed
            'peak_reflexivity': reflexivity,
            'quadrant': quadrant,
            'peak_date': today.strftime('%Y-%m-%d'),
            'watermark_price': watermark_price,
            'watermark_date': watermark_date,
            'status': 'ACTIVE',
            'expiry_date': (today + timedelta(days=OUTCOME_WINDOW_DAYS)).strftime('%Y-%m-%d'),
            'normal_since': None  # Track when it went normal (for merge logic)
        }

        print(f"  Episode started: {market} ({episode_id})")

    def _update_episode(
        self,
        market: str,
        episode: Dict,
        lambda_pct: float,
        reflexivity: Optional[float],
        quadrant: str,
        prices: pd.DataFrame,
        tickers: List[str]
    ) -> None:
        """Update an existing active episode."""
        today = datetime.now().date()

        # Clear normal_since since we're back to elevated
        episode['normal_since'] = None

        # Update peak if current is higher
        if lambda_pct > episode.get('peak_lambda_pct', 0):
            episode['peak_lambda_pct'] = lambda_pct
            episode['peak_date'] = today.strftime('%Y-%m-%d')

        # Update reflexivity peak
        if reflexivity is not None:
            current_peak = episode.get('peak_reflexivity')
            if current_peak is None or reflexivity > current_peak:
                episode['peak_reflexivity'] = reflexivity

        # Update quadrant if we reach Q4 (highest risk)
        if quadrant == 'Q4':
            episode['quadrant'] = 'Q4'
        elif episode.get('quadrant') != 'Q4':
            # Only update if not already Q4
            episode['quadrant'] = quadrant

        # Update watermark
        if prices is not None:
            episode = update_watermark(prices, tickers, episode)

        self.episodes[market] = episode

    def _handle_normal(self, market: str, episode: Dict, today: date) -> None:
        """Handle market returning to normal regime."""
        normal_since = episode.get('normal_since')

        if normal_since is None:
            # First day of normal - record it
            episode['normal_since'] = today.strftime('%Y-%m-%d')
            self.episodes[market] = episode
            return

        # Check how long it's been normal
        normal_date = datetime.strptime(normal_since, '%Y-%m-%d').date()
        days_normal = (today - normal_date).days

        if days_normal >= EPISODE_MERGE_GAP_DAYS:
            # Episode ended - gap too long to merge
            # Check if it expired or should be marked for outcome tracking
            self._expire_episode(market, episode, 'GAP_EXPIRED')
        # else: Keep tracking, might return to elevated within merge window

    def _expire_episode(self, market: str, episode: Dict, reason: str) -> None:
        """Mark an episode as expired (no correction within window)."""
        today = datetime.now()

        episode['status'] = 'EXPIRED'
        episode['end_date'] = today.strftime('%Y-%m-%d')
        episode['outcome'] = 'FALSE_POSITIVE'
        episode['close_reason'] = reason

        self._closed_episodes.append({
            'market': market,
            'episode': episode.copy()
        })

        # Remove from active episodes
        del self.episodes[market]
        print(f"  Episode expired: {market} ({reason})")

    def close(self, market: str, outcome: str) -> Optional[Dict]:
        """
        Close an episode with a specific outcome.

        Args:
            market: Market name
            outcome: 'TRUE_POSITIVE', 'PARTIAL', or 'FALSE_POSITIVE'

        Returns:
            The closed episode dict, or None if not found
        """
        if market not in self.episodes:
            return None

        episode = self.episodes[market]
        today = datetime.now()

        episode['status'] = 'CLOSED'
        episode['end_date'] = today.strftime('%Y-%m-%d')
        episode['outcome'] = outcome
        episode['close_reason'] = 'CORRECTION_DETECTED' if outcome != 'FALSE_POSITIVE' else 'MANUAL'

        self._closed_episodes.append({
            'market': market,
            'episode': episode.copy()
        })

        del self.episodes[market]
        print(f"  Episode closed: {market} -> {outcome}")

        return episode

    def check_expiries(self) -> None:
        """Check all active episodes for expiry."""
        today = datetime.now().date()

        to_expire = []
        for market, episode in self.episodes.items():
            expiry_str = episode.get('expiry_date')
            if expiry_str:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                if today > expiry_date:
                    to_expire.append(market)

        for market in to_expire:
            self._expire_episode(market, self.episodes[market], 'WINDOW_EXPIRED')

    def should_merge(self, market: str, last_end_date: str, new_start_date: str) -> bool:
        """
        Check if two episodes should be merged.

        Args:
            market: Market name
            last_end_date: End date of previous episode (YYYY-MM-DD)
            new_start_date: Start date of potential new episode (YYYY-MM-DD)

        Returns:
            True if episodes should be merged (gap < 30 days)
        """
        end = datetime.strptime(last_end_date, '%Y-%m-%d').date()
        start = datetime.strptime(new_start_date, '%Y-%m-%d').date()
        gap_days = (start - end).days

        return gap_days < EPISODE_MERGE_GAP_DAYS

    def get_summary(self) -> Dict:
        """Get summary of all active episodes."""
        summary = {}
        for market, episode in self.episodes.items():
            if episode.get('status') == 'ACTIVE':
                summary[market] = {
                    'start': episode.get('start_date'),
                    'peak': episode.get('peak_lambda_pct'),
                    'quadrant': episode.get('quadrant'),
                    'days_active': (datetime.now().date() -
                                   datetime.strptime(episode['start_date'], '%Y-%m-%d').date()).days
                }
        return summary


if __name__ == "__main__":
    import tempfile

    print("Testing episode manager...")

    # Use temp file for testing
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        test_file = f.name

    mgr = EpisodeManager(test_file)

    # Simulate price data
    dates = pd.date_range('2026-01-01', periods=30, freq='D')
    prices = pd.DataFrame({
        'GLD': [100 + i * 0.5 for i in range(30)],
        'SLV': [50 + i * 0.3 for i in range(30)]
    }, index=dates)
    tickers = ['GLD', 'SLV']

    # Test creating episode
    print("\n1. Creating episode for Commodities...")
    mgr.update('Commodities', '**CRITICAL** (L)', 85.0, 72.0, 'Q4', prices, tickers)
    print(f"   Active episodes: {list(mgr.episodes.keys())}")

    # Test updating episode
    print("\n2. Updating episode (higher signal)...")
    mgr.update('Commodities', '**CRITICAL** (LC)', 92.0, 78.0, 'Q4', prices, tickers)
    print(f"   Peak Lambda: {mgr.episodes['Commodities']['peak_lambda_pct']}")

    # Test normal transition
    print("\n3. Market goes normal...")
    mgr.update('Commodities', 'Normal', 45.0, 35.0, 'Q1', prices, tickers)
    print(f"   normal_since: {mgr.episodes['Commodities'].get('normal_since')}")

    # Test closing
    print("\n4. Closing episode...")
    closed = mgr.close('Commodities', 'TRUE_POSITIVE')
    print(f"   Closed: {closed['outcome']}")
    print(f"   Active episodes: {list(mgr.episodes.keys())}")

    # Cleanup
    os.unlink(test_file)
    print("\nTest complete!")
