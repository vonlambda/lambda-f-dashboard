#!/usr/bin/env python3
"""
outcome_recorder.py - Record episode outcomes to events.csv

Appends validated episodes to events.csv matching the existing schema:
event_id,event_name,market,start_date,end_date,event_type,detected_by,result

Outcome types:
- TRUE_POSITIVE: Q4 episode followed by >=15% correction
- PARTIAL: Q3 episode followed by correction (rotation without cascade)
- FALSE_POSITIVE: Episode expired without correction
"""

import os
import csv
from datetime import datetime
from typing import Dict, Optional

from correction_detector import CorrectionEvent


def get_next_event_id(events_file: str) -> int:
    """
    Get the next event_id by reading existing events.csv.

    Args:
        events_file: Path to events.csv

    Returns:
        Next event_id (max existing + 1)
    """
    if not os.path.exists(events_file):
        return 1

    max_id = 0
    try:
        with open(events_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    event_id = int(row.get('event_id', 0))
                    max_id = max(max_id, event_id)
                except (ValueError, TypeError):
                    continue
    except Exception:
        pass

    return max_id + 1


def determine_event_type(episode: Dict, correction: Optional[CorrectionEvent]) -> str:
    """
    Determine event_type based on episode characteristics.

    Args:
        episode: Episode dict with trigger_type, quadrant, etc.
        correction: CorrectionEvent if correction detected

    Returns:
        Event type string (e.g., 'rotation', 'synchronized_selloff')
    """
    trigger = episode.get('trigger_type', 'L')
    quadrant = episode.get('quadrant', 'Q3')

    if 'C' in trigger and 'L' not in trigger:
        return 'synchronized_selloff'
    elif quadrant == 'Q4':
        return 'leveraged_rotation'
    elif 'LC' in trigger:
        return 'rotation_with_panic'
    else:
        return 'rotation'


def determine_detected_by(episode: Dict) -> str:
    """
    Determine detected_by field from episode trigger.

    Args:
        episode: Episode dict with trigger_type

    Returns:
        Detection method string
    """
    trigger = episode.get('trigger_type', 'L')

    if trigger == 'LC':
        return 'Lambda-F + Correlation'
    elif trigger == 'C':
        return 'Correlation'
    else:
        return 'Lambda-F'


def format_event_name(market: str, start_date: str) -> str:
    """
    Generate human-readable event name.

    Args:
        market: Market name (e.g., 'Commodities')
        start_date: Episode start date (YYYY-MM-DD)

    Returns:
        Event name (e.g., 'Commodities Jan 2026')
    """
    try:
        dt = datetime.strptime(start_date, '%Y-%m-%d')
        month_year = dt.strftime('%b %Y')
    except (ValueError, TypeError):
        month_year = start_date

    # Clean market name
    clean_market = market.replace(' (BTC)', '').replace(' (SPY)', '').replace(' (EWU)', '').replace(' (EWG)', '')

    return f"{clean_market} {month_year}"


def record_outcome(
    market: str,
    episode: Dict,
    correction: Optional[CorrectionEvent],
    outcome: str,
    events_file: str = None
) -> Dict:
    """
    Record episode outcome to events.csv.

    Args:
        market: Market name
        episode: Episode dict with start_date, trigger_type, quadrant, etc.
        correction: CorrectionEvent if correction detected, None otherwise
        outcome: 'TRUE_POSITIVE', 'PARTIAL', or 'FALSE_POSITIVE'
        events_file: Path to events.csv (default: same directory as this script)

    Returns:
        Dict with the recorded event data
    """
    # Default events file path
    if events_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        events_file = os.path.join(script_dir, 'events.csv')

    # Get next event ID
    event_id = get_next_event_id(events_file)

    # Build event record
    start_date = episode.get('start_date', datetime.now().strftime('%Y-%m-%d'))

    if correction:
        end_date = correction.correction_date.strftime('%Y-%m-%d') \
            if hasattr(correction.correction_date, 'strftime') \
            else str(correction.correction_date)
    else:
        end_date = episode.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    event = {
        'event_id': event_id,
        'event_name': format_event_name(market, start_date),
        'market': market.replace(' (BTC)', '').replace(' (SPY)', '').replace(' (EWU)', '').replace(' (EWG)', ''),
        'start_date': start_date,
        'end_date': end_date,
        'event_type': determine_event_type(episode, correction),
        'detected_by': determine_detected_by(episode),
        'result': outcome
    }

    # Append to CSV
    file_exists = os.path.exists(events_file)

    with open(events_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'event_id', 'event_name', 'market', 'start_date', 'end_date',
            'event_type', 'detected_by', 'result'
        ])

        # Write header if new file
        if not file_exists:
            writer.writeheader()

        writer.writerow(event)

    print(f"  Recorded event #{event_id}: {event['event_name']} -> {outcome}")

    return event


def record_false_positive(
    market: str,
    episode: Dict,
    events_file: str = None
) -> Dict:
    """
    Record a false positive (episode expired without correction).

    Args:
        market: Market name
        episode: Episode dict
        events_file: Path to events.csv

    Returns:
        Dict with the recorded event data
    """
    return record_outcome(
        market=market,
        episode=episode,
        correction=None,
        outcome='FALSE_POSITIVE',
        events_file=events_file
    )


def get_outcome_summary(events_file: str = None) -> Dict:
    """
    Get summary statistics from events.csv.

    Returns:
        Dict with counts by outcome type
    """
    if events_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        events_file = os.path.join(script_dir, 'events.csv')

    if not os.path.exists(events_file):
        return {'total': 0}

    summary = {
        'total': 0,
        'TRUE_POSITIVE': 0,
        'PARTIAL': 0,
        'FALSE_POSITIVE': 0,
        'DETECTED': 0,
        'EXCLUDED': 0,
        'NOT_DETECTED': 0
    }

    try:
        with open(events_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary['total'] += 1
                result = row.get('result', '')

                if result in summary:
                    summary[result] += 1
                elif 'DETECTED' in result:
                    summary['DETECTED'] += 1
                elif 'EXCLUDED' in result:
                    summary['EXCLUDED'] += 1
                elif 'NOT DETECTED' in result:
                    summary['NOT_DETECTED'] += 1
    except Exception:
        pass

    return summary


if __name__ == "__main__":
    import tempfile
    from datetime import date

    print("Testing outcome recorder...")

    # Create temp events file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
        test_file = f.name
        # Write header and one existing event
        f.write("event_id,event_name,market,start_date,end_date,event_type,detected_by,result\n")
        f.write("1,Test Event,Commodities,2025-01-01,2025-02-01,rotation,Lambda-F,DETECTED\n")

    print(f"\n1. Testing get_next_event_id...")
    next_id = get_next_event_id(test_file)
    print(f"   Next ID: {next_id}")
    assert next_id == 2, f"Expected 2, got {next_id}"

    print(f"\n2. Testing record_outcome (TRUE_POSITIVE)...")
    episode = {
        'start_date': '2026-01-15',
        'end_date': '2026-02-20',
        'trigger_type': 'LC',
        'quadrant': 'Q4',
        'peak_lambda_pct': 92
    }
    correction = CorrectionEvent(
        correction_date=date(2026, 2, 15),
        correction_magnitude=-18.5,
        watermark_price=125.0,
        watermark_date=date(2026, 1, 20),
        trough_price=102.0,
        lead_time_days=31
    )

    event = record_outcome(
        market='Commodities',
        episode=episode,
        correction=correction,
        outcome='TRUE_POSITIVE',
        events_file=test_file
    )
    print(f"   Recorded: {event}")

    print(f"\n3. Testing record_false_positive...")
    fp_episode = {
        'start_date': '2026-01-05',
        'end_date': '2026-04-05',
        'trigger_type': 'L',
        'quadrant': 'Q3',
        'peak_lambda_pct': 78
    }
    fp_event = record_false_positive(
        market='Gold',
        episode=fp_episode,
        events_file=test_file
    )
    print(f"   Recorded: {fp_event}")

    print(f"\n4. Testing get_outcome_summary...")
    summary = get_outcome_summary(test_file)
    print(f"   Summary: {summary}")

    # Cleanup
    os.unlink(test_file)
    print("\nTest complete!")
