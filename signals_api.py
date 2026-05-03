"""
signals_api.py — Tier 3 Phase B: JSON API endpoints.

Generates two public JSON files at the repo root that consumers can
fetch via raw.githubusercontent.com or GitHub Pages:

  signals/latest.json     today's full per-market state + headline aggregates
  signals/history.json    last 365 days of per-market percentiles + regime

Patent reference: Claim 23 (diagnostic-as-a-service — public data layer).
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional

from github import Github

from outcome_tracker import compute_systemic_score, compute_detection_stats


SCHEMA_VERSION = "1.0"


def _parse_pct(s) -> Optional[float]:
    if s is None or s in ('--', ''):
        return None
    try:
        return float(str(s).rstrip('%').strip())
    except (ValueError, TypeError):
        return None


def _parse_float(s) -> Optional[float]:
    if s is None or s in ('--', ''):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_elev_days(s):
    """Parse '7d*' or '5d' or '--'. Returns (days_int, threshold_marker)."""
    if not s or s == '--':
        return None, None
    s = str(s).strip()
    marker = 'p90' if s.endswith('*') else 'p75'
    s = s.rstrip('*').rstrip('d')
    try:
        return int(s), marker
    except ValueError:
        return None, None


def build_latest_payload(results: List[Dict]) -> Dict:
    """Compose signals/latest.json payload from today's results list."""
    n_crit = sum(1 for r in results if 'CRITICAL' in r.get('regime', ''))
    n_elev = sum(1 for r in results if 'ELEVATED' in r.get('regime', ''))
    n_norm = sum(1 for r in results if 'Normal'   in r.get('regime', ''))
    n_q4 = sum(1 for r in results if r.get('quadrant') == 'Q4')
    n_q3 = sum(1 for r in results if r.get('quadrant') in ('Q3', 'Q3*'))
    n_q2 = sum(1 for r in results if r.get('quadrant') == 'Q2')
    n_q1 = sum(1 for r in results if r.get('quadrant') in ('Q1', 'Q1*'))

    sys_score = compute_systemic_score(results)
    stats = compute_detection_stats()

    markets = []
    for r in results:
        elev_days, elev_marker = _parse_elev_days(r.get('lambda_days'))
        # Strip markdown bold and source tag (L/C/LC) for clean machine consumption
        regime_clean = r.get('regime', '').replace('**', '').strip()
        if ' (' in regime_clean:
            regime_label, _, src = regime_clean.partition(' (')
            regime_source = src.rstrip(')')
        else:
            regime_label, regime_source = regime_clean, None
        markets.append({
            'market': r.get('market'),
            'lambda_value': _parse_float(r.get('lambda_val')),
            'lambda_pct': _parse_pct(r.get('lambda_pct')),
            'elevated_days': elev_days,
            'elevated_threshold': elev_marker,
            'correlation': _parse_float(r.get('corr_val')),
            'correlation_pct': _parse_pct(r.get('corr_pct')),
            'reflexivity': r.get('reflexivity'),
            'quadrant': r.get('quadrant'),
            'regime': regime_label,
            'regime_source': regime_source,
            'action': r.get('action'),
            'changed_today': bool(r.get('changed_today')),
            'since': r.get('since'),
        })

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'headline': {
            'regime_counts': {
                'CRITICAL': n_crit, 'ELEVATED': n_elev, 'NORMAL': n_norm,
            },
            'quadrant_counts': {
                'Q4': n_q4, 'Q3': n_q3, 'Q2': n_q2, 'Q1': n_q1,
            },
            'systemic_score': {
                'score': sys_score['score'],
                'max': sys_score['max_score'],
                'pct': round(sys_score['pct'], 1),
                'label': sys_score['label'],
            },
            'live_forward_detection': {
                'true_positives': stats['true_positives'],
                'false_positives': stats['false_positives'],
                'pending': stats['pending'],
                'rate_pct': (round(stats['detection_rate'], 1)
                              if stats['detection_rate'] is not None else None),
            },
        },
        'markets': markets,
    }


def append_to_history(latest_payload: Dict, history_path: str,
                       max_days: int = 365) -> Dict:
    """Append today's compact summary to history.json (rolling 365 days)."""
    history = {'schema_version': SCHEMA_VERSION, 'history': []}
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    today = latest_payload['date']
    rows = [r for r in history.get('history', []) if r.get('date') != today]

    today_compact = {
        'date': today,
        'systemic_score': latest_payload['headline']['systemic_score']['score'],
        'systemic_label': latest_payload['headline']['systemic_score']['label'],
        'n_q4': latest_payload['headline']['quadrant_counts']['Q4'],
        'n_q3': latest_payload['headline']['quadrant_counts']['Q3'],
        'n_critical': latest_payload['headline']['regime_counts']['CRITICAL'],
        'markets': {
            m['market']: {
                'lambda_pct': m['lambda_pct'],
                'reflexivity': m['reflexivity'],
                'quadrant': m['quadrant'],
                'regime': m['regime'],
            }
            for m in latest_payload['markets']
        },
    }
    rows.append(today_compact)
    rows.sort(key=lambda r: r['date'], reverse=True)
    rows = rows[:max_days]

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at': latest_payload['generated_at'],
        'count': len(rows),
        'history': rows,
    }


def write_signals_files(results: List[Dict]) -> tuple:
    """
    Write signals/latest.json + signals/history.json under engine dir.
    Returns (latest_path, history_path).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    signals_dir = os.path.join(script_dir, 'signals')
    os.makedirs(signals_dir, exist_ok=True)

    latest = build_latest_payload(results)
    latest_path = os.path.join(signals_dir, 'latest.json')
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(latest, f, indent=2)

    history_path = os.path.join(signals_dir, 'history.json')
    history = append_to_history(latest, history_path)
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    return latest_path, history_path


def push_signals_to_github() -> bool:
    """Upload signals/latest.json + history.json to the dashboard repo."""
    token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPO')
    if not token or not repo_name:
        print("  signals_api: GITHUB_TOKEN/GITHUB_REPO not set; skipping push")
        return False

    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = [
        ('signals/latest.json',  os.path.join(script_dir, 'signals', 'latest.json')),
        ('signals/history.json', os.path.join(script_dir, 'signals', 'history.json')),
    ]

    g = Github(token)
    repo = g.get_repo(repo_name)

    for repo_path, local_path in files:
        if not os.path.exists(local_path):
            continue
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                existing = repo.get_contents(repo_path)
                repo.update_file(
                    repo_path,
                    f'Update {repo_path} {datetime.now().strftime("%Y-%m-%d")}',
                    content,
                    existing.sha,
                )
            except Exception:
                repo.create_file(
                    repo_path,
                    f'Create {repo_path} {datetime.now().strftime("%Y-%m-%d")}',
                    content,
                )
            print(f"  signals_api: pushed {repo_path}")
        except Exception as e:
            print(f"  signals_api: push failed for {repo_path}: {e}")
    return True
