"""
Generate live Lambda-F signal visualization for CRITICAL markets only.
Uses the same data as update_lambda.py for consistency.
White background, distinct color per asset.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Import from update_lambda to ensure consistency
from update_lambda import (
    MARKETS as DASHBOARD_MARKETS,
    fetch_data,
    compute_returns,
    compute_factors,
    compute_lambda_f,
    get_combined_regime,
    compute_rolling_correlation,
)

# Colors for each market
MARKET_COLORS = {
    'Commodities': '#e63946',      # Red
    'Gold': '#f4a261',             # Orange/Gold
    'Crypto (BTC)': '#2a9d8f',     # Teal
    'US Equity (SPY)': '#264653',  # Dark blue
    'UK Equity (EWU)': '#457b9d',  # Steel blue
    'Germany (EWG)': '#1d3557',    # Navy
    'Bonds': '#6d597a',            # Purple
    'Emerging Markets': '#b56576', # Mauve
}

def generate_live_chart():
    """Generate live signal chart for CRITICAL markets only.
    Uses the same calculation as update_lambda.py for consistency.
    """
    print("="*60)
    print("Generating Live Signal Visualization")
    print("="*60)
    
    # Collect data for all markets using same method as dashboard
    market_data = {}
    critical_markets = []
    
    for market_name, config in DASHBOARD_MARKETS.items():
        print(f"\nProcessing {market_name}...")
        
        try:
            # Use same fetch as dashboard
            prices = fetch_data(config['tickers'], days=1200)
            if prices is None or len(prices) < 200:
                print(f"  Skipping {market_name} - insufficient price data")
                continue
            
            # Compute returns and factors same as dashboard
            returns = compute_returns(prices)
            factors = compute_factors(returns, prices)
            
            if factors is None or len(factors) < 200:
                print(f"  Skipping {market_name} - insufficient factor data")
                continue
            
            # Compute Lambda-F same as dashboard
            current_lambda, current_pct, lambda_series = compute_lambda_f(factors)
            
            if lambda_series is None or len(lambda_series) < 30:
                print(f"  Skipping {market_name} - insufficient Lambda-F data")
                continue
            
            # Get regime using same logic as dashboard
            regime, signal = get_combined_regime(lambda_series, None)
            is_critical = "CRITICAL" in regime
            
            # Count days above P90 in last 30 days (for display)
            last_30 = lambda_series.iloc[-30:]
            historical = lambda_series.iloc[:-1]
            p90 = historical.quantile(0.90)
            days_above_90 = (last_30 > p90).sum()
            
            # Build percentile series for plotting
            lambda_pct_series = lambda_series.expanding(min_periods=60).rank(pct=True) * 100
            
            # Get color
            color = MARKET_COLORS.get(market_name, '#888888')
            
            market_data[market_name] = {
                'percentile': lambda_pct_series,
                'color': color,
                'current': current_pct if current_pct else 0,
                'is_critical': is_critical,
                'days_above_90': days_above_90,
                'regime': regime,
            }
            
            print(f"  {market_name}: {current_pct:.1f}% ({regime}, {days_above_90}d above P90 in last 30d)")
            
            if is_critical:
                critical_markets.append(market_name)
                
        except Exception as e:
            print(f"  Error processing {market_name}: {e}")
    
    if not market_data:
        print("ERROR: No market data available")
        return None
    
    # Filter to only CRITICAL markets
    critical_data = {k: v for k, v in market_data.items() if v['is_critical']}
    
    print(f"\n{'='*60}")
    print(f"CRITICAL MARKETS: {len(critical_data)}")
    print(f"{'='*60}")
    for name in critical_data:
        print(f"  - {name}: {critical_data[name]['current']:.1f}%")
    
    # Visualization window: last 90 days
    viz_days = 90
    end_date = datetime.now()
    start_date = end_date - timedelta(days=viz_days)
    
    # Create figure with white background
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    
    if not critical_data:
        # No critical markets - show "all clear" message
        ax.text(0.5, 0.55, 'No Critical Markets', 
               transform=ax.transAxes, fontsize=28, 
               color='#22c55e', fontweight='bold',
               ha='center', va='center')
        ax.text(0.5, 0.42, 'All markets below P90 threshold', 
               transform=ax.transAxes, fontsize=14, 
               color='#6b7280',
               ha='center', va='center')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        ax.text(0.5, 0.30, f'Updated: {timestamp}', 
               transform=ax.transAxes, fontsize=10, 
               color='#9ca3af',
               ha='center', va='center')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Simple title
        ax.set_title('Critical Market Alerts', 
                    fontsize=16, color='#1f2937', fontweight='bold', pad=15)
    else:
        # Plot only critical markets
        for market_name, data in critical_data.items():
            pct = data['percentile']
            # Filter to visualization window
            pct_viz = pct[pct.index >= start_date.strftime('%Y-%m-%d')]
            
            if len(pct_viz) > 0:
                ax.plot(pct_viz.index, pct_viz.values, 
                       color=data['color'], linewidth=2.5, 
                       label=f"{market_name} ({data['current']:.0f}%)",
                       alpha=0.9)
        
        # Threshold lines
        ax.axhline(y=90, color='#dc2626', linestyle='--', linewidth=2, alpha=0.6, label='P90 (Critical)')
        ax.axhline(y=75, color='#f59e0b', linestyle='--', linewidth=2, alpha=0.6, label='P75 (Elevated)')
        
        # Shade zones
        ax.fill_between([start_date, end_date], 90, 100, alpha=0.08, color='#dc2626')
        ax.fill_between([start_date, end_date], 75, 90, alpha=0.05, color='#f59e0b')
        ax.set_xlim(start_date, end_date)
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, color='#1f2937')
        ax.set_ylabel('Lambda-F Percentile', fontsize=12, color='#1f2937')
        ax.set_title(f'Critical Market Alerts — Last {viz_days} Days', 
                    fontsize=16, color='#1f2937', fontweight='bold', pad=15)
        
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, color='#d1d5db')
        
        # Legend - sorted by current value (descending)
        handles, labels = ax.get_legend_handles_labels()
        # Separate threshold lines from market lines
        market_handles = handles[:-2] if len(handles) > 2 else handles
        market_labels = labels[:-2] if len(labels) > 2 else labels
        threshold_handles = handles[-2:] if len(handles) > 2 else []
        threshold_labels = labels[-2:] if len(labels) > 2 else []
        
        # Sort markets by current percentile
        # Use rsplit so market names containing parens (e.g. "US Equity (SPY) (53%)")
        # parse correctly — we want the LAST "(...)" group, the percentile.
        if market_labels:
            sorted_indices = sorted(range(len(market_labels)),
                                   key=lambda i: float(market_labels[i].rsplit('(', 1)[1].rstrip('%)')) if '(' in market_labels[i] else 0,
                                   reverse=True)
            sorted_handles = [market_handles[i] for i in sorted_indices] + threshold_handles
            sorted_labels = [market_labels[i] for i in sorted_indices] + threshold_labels
        else:
            sorted_handles = threshold_handles
            sorted_labels = threshold_labels
        
        legend = ax.legend(sorted_handles, sorted_labels, 
                          loc='lower left', fontsize=10,
                          facecolor='#ffffff', edgecolor='#e5e7eb',
                          framealpha=0.95)
        
        # Axis styling
        ax.tick_params(colors='#4b5563')
        ax.spines['bottom'].set_color('#d1d5db')
        ax.spines['top'].set_color('#d1d5db')
        ax.spines['left'].set_color('#d1d5db')
        ax.spines['right'].set_color('#d1d5db')
        
        # Date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha='right')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        ax.annotate(f'Updated: {timestamp}', 
                   xy=(0.99, 0.01), xycoords='axes fraction',
                   fontsize=9, color='#9ca3af',
                   ha='right', va='bottom')
    
    plt.tight_layout()
    
    # Save
    output_path = 'live_signals.png'
    plt.savefig(output_path, dpi=150, facecolor='#ffffff', edgecolor='none')
    print(f"\nChart saved to: {output_path}")
    
    plt.close()
    return output_path


def main():
    generate_live_chart()


if __name__ == "__main__":
    main()

