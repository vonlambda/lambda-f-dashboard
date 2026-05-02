"""
Generate the Λ × R 4-quadrant matrix visualization for the dashboard.

Renders each tracked market as a labeled point on a 2D plot:
  x-axis: Reflexivity score R_t (0-100)
  y-axis: Lambda-F percentile Λ% (0-100)

Background shading shows quadrant boundaries:
  Q1 STABLE   (Λ<P75, R<60)  - green
  Q2 FRAGILE  (Λ<P75, R>=60) - yellow
  Q3 ROTATING (Λ>=P75, R<60) - orange
  Q4 CRITICAL (Λ>=P75, R>=60) - red

Pushes assets/quadrant_matrix.png to the dashboard repo.

Patent reference: claims 2, 3 (4-quadrant classification).
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from github import Github

# Quadrant cuts per patent §6.5
LAMBDA_THRESHOLD = 75   # P75
REFLEX_THRESHOLD = 60   # R >= 60 for "high"


def _parse_percent(s):
    """Convert '87%' -> 87.0, '--' -> None."""
    if s is None or s == '--':
        return None
    s = str(s).rstrip('%').strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def generate_quadrant_matrix(results, output_path='assets/quadrant_matrix.png'):
    """Render the 2x2 quadrant matrix from results list.

    Args:
        results: list of dicts (output of compute_all_markets).
                 Each must have 'market', 'lambda_pct', 'reflexivity'.
        output_path: where to save PNG (relative to script dir).
    """
    # Filter to markets with both signals available
    plottable = []
    for r in results:
        lam_pct = _parse_percent(r.get('lambda_pct'))
        reflex = r.get('reflexivity')
        if lam_pct is None or reflex is None:
            continue
        plottable.append({
            'market': r['market'],
            'lambda_pct': lam_pct,
            'reflexivity': float(reflex),
            'quadrant': r.get('quadrant', '?'),
        })

    if not plottable:
        print("Quadrant matrix: no markets with both signals available; skipping.")
        return False

    # Build figure
    fig, ax = plt.subplots(figsize=(10, 8), dpi=120)

    # Quadrant background shading
    ax.add_patch(patches.Rectangle((0, 0), REFLEX_THRESHOLD, LAMBDA_THRESHOLD,
                                    facecolor='#d4edda', alpha=0.5, zorder=0))   # Q1 green
    ax.add_patch(patches.Rectangle((REFLEX_THRESHOLD, 0), 100 - REFLEX_THRESHOLD, LAMBDA_THRESHOLD,
                                    facecolor='#fff3cd', alpha=0.5, zorder=0))   # Q2 yellow
    ax.add_patch(patches.Rectangle((0, LAMBDA_THRESHOLD), REFLEX_THRESHOLD, 100 - LAMBDA_THRESHOLD,
                                    facecolor='#ffe5b4', alpha=0.6, zorder=0))   # Q3 orange
    ax.add_patch(patches.Rectangle((REFLEX_THRESHOLD, LAMBDA_THRESHOLD),
                                    100 - REFLEX_THRESHOLD, 100 - LAMBDA_THRESHOLD,
                                    facecolor='#f8d7da', alpha=0.6, zorder=0))   # Q4 red

    # Threshold lines
    ax.axvline(x=REFLEX_THRESHOLD, color='gray', linestyle='--', linewidth=1.2, alpha=0.7, zorder=1)
    ax.axhline(y=LAMBDA_THRESHOLD, color='gray', linestyle='--', linewidth=1.2, alpha=0.7, zorder=1)

    # Quadrant labels in corners
    ax.text(REFLEX_THRESHOLD * 0.5, LAMBDA_THRESHOLD * 0.5,
            'Q1\nSTABLE', ha='center', va='center',
            fontsize=14, color='#2d6a4f', alpha=0.55, fontweight='bold', zorder=1)
    ax.text(REFLEX_THRESHOLD + (100 - REFLEX_THRESHOLD) * 0.5, LAMBDA_THRESHOLD * 0.5,
            'Q2\nFRAGILE', ha='center', va='center',
            fontsize=14, color='#856404', alpha=0.55, fontweight='bold', zorder=1)
    ax.text(REFLEX_THRESHOLD * 0.5, LAMBDA_THRESHOLD + (100 - LAMBDA_THRESHOLD) * 0.5,
            'Q3\nROTATING', ha='center', va='center',
            fontsize=14, color='#b45309', alpha=0.55, fontweight='bold', zorder=1)
    ax.text(REFLEX_THRESHOLD + (100 - REFLEX_THRESHOLD) * 0.5,
            LAMBDA_THRESHOLD + (100 - LAMBDA_THRESHOLD) * 0.5,
            'Q4\nCRITICAL', ha='center', va='center',
            fontsize=14, color='#991b1b', alpha=0.55, fontweight='bold', zorder=1)

    # Plot each market as labeled point
    # Slight jitter on overlapping points
    seen = {}
    for p in plottable:
        x, y = p['reflexivity'], p['lambda_pct']
        key = (round(x), round(y))
        if key in seen:
            seen[key] += 1
            x += seen[key] * 1.5  # nudge horizontally
        else:
            seen[key] = 0

        ax.plot(x, y, 'o', color='#0f172a', markersize=11, zorder=3,
                markeredgecolor='white', markeredgewidth=1.5)
        ax.annotate(p['market'], (x, y), xytext=(8, 6), textcoords='offset points',
                    fontsize=10, fontweight='bold', color='#0f172a', zorder=4,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor='none', alpha=0.85))

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel('Reflexivity Score R (0-100)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Λ-F Percentile (0-100)', fontsize=12, fontweight='bold')
    ax.set_title('Λ × R Quadrant State — Live Markets',
                 fontsize=14, fontweight='bold', pad=12)
    ax.grid(True, alpha=0.2, zorder=0)
    ax.set_aspect('equal')

    # Legend / footer
    fig.text(0.5, 0.02,
             'Q4 CRITICAL = high Λ + high R (geometric instability + behavioral cascade conditions). '
             'Q3 ROTATING = high Λ + low R (structure shifting without crash conditions).',
             ha='center', fontsize=9, color='#475569', style='italic')

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(script_dir, output_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Quadrant matrix saved to: {out}")
    return True


def push_quadrant_matrix_to_github(local_path='assets/quadrant_matrix.png',
                                    repo_path='assets/quadrant_matrix.png'):
    """Push the rendered quadrant matrix PNG to the dashboard repo."""
    token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPO')
    if not token or not repo_name:
        print("Quadrant matrix: GITHUB_TOKEN/GITHUB_REPO not set; skipping push.")
        return False

    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_local = os.path.join(script_dir, local_path)
    if not os.path.exists(full_local):
        print(f"Quadrant matrix: local file {full_local} not found; skipping push.")
        return False

    try:
        with open(full_local, 'rb') as f:
            content_bytes = f.read()

        g = Github(token)
        repo = g.get_repo(repo_name)
        try:
            existing = repo.get_contents(repo_path)
            repo.update_file(
                repo_path,
                f'Update quadrant matrix {os.path.basename(repo_path)}',
                content_bytes,
                existing.sha,
            )
        except Exception:
            repo.create_file(
                repo_path,
                f'Create quadrant matrix {os.path.basename(repo_path)}',
                content_bytes,
            )
        print("Quadrant matrix uploaded to GitHub")
        return True
    except Exception as e:
        print(f"Quadrant matrix push failed: {e}")
        return False
