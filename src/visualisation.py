"""
Visualisation module for crypto market microstructure analysis.

Creates professional plots to illustrate key findings from order book
imbalance and market efficiency analyses.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict
import json


def load_data_and_results(data_filepath: Path) -> tuple[pd.DataFrame, dict, dict]:
    """
    Load orderbook data and analysis results
    
    Parameters:
    data_filepath : Path
        Path to the orderbook CSV file
        
    Returns:
    tuple containing:
        - df: DataFrame with orderbook data
        - imbalance_results: Dictionary with imbalance hypothesis results
        - efficiency_results: Dictionary with efficiency results
    """
    # Load CSV data
    df = pd.read_csv(data_filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    # Load JSON results
    results_dir = Path('results') / 'metrics'
    
    with open(results_dir / 'imbalance_hypothesis_results.json', 'r') as f:
        imbalance_results = json.load(f)
    
    with open(results_dir / 'market_efficiency_results.json', 'r') as f:
        efficiency_results = json.load(f)
    
    return df, imbalance_results, efficiency_results


def setup_plot_style() -> None:
    """
    Configure matplotlib settings for consistent plots
    """
    plt.style.use('seaborn-v0_8-dark')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10

    # make gridlines more pronounced globally
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.color'] = '#666666'        # slightly darker gray
    plt.rcParams['grid.linewidth'] = 1.2         # thicker lines
    plt.rcParams['grid.alpha'] = 0.8             # more visible
    plt.rcParams['grid.linestyle'] = '-'         


def plot_imbalance_analysis(df: pd.DataFrame, imbalance_results: Dict, save_path: Path = None, show: bool = True) -> plt.Figure:
    """
    Visualise imbalance hypothesis results with scatter and correlation decay
    
    Parameters:
    df : pd.DataFrame
        Orderbook data with 'imbalance_5' and 'mid_price' columns
    imbalance_results : Dict
        Results from test_imbalance_hypothesis() containing correlations and best_horizon
    save_path : Path, optional
        If provided, saves figure to this location
        
    Returns:
    plt.Figure
        Figure with two subplots showing imbalance analysis
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Left: Scatter plot of imbalance vs returns at best horizon
    # Right: Correlation decay over different horizons
    best_horizon = imbalance_results['best_horizon']
    returns = df['mid_price'].pct_change(periods=best_horizon).shift(-best_horizon)

    imbalance, pct_returns = df['imbalance_5'], returns * 100 

    # First plot
    ax1.scatter(imbalance, pct_returns)
    ax1.set_title(f'Imbalance vs Percentage Returns at Best Horizon ({best_horizon})')
    ax1.set_xlabel('Imbalance')
    ax1.set_ylabel('Returns (%)')

    # Fit a linear model
    valid_mask = imbalance.notna() & pct_returns.notna()
    if valid_mask.sum() >= 2:
        imbalance_clean = imbalance[valid_mask].to_numpy()
        returns_clean = pct_returns[valid_mask].to_numpy()
        coeffs = np.polyfit(imbalance_clean, returns_clean, 1)
    
        # Create smooth line for plotting
        imbalance_range = np.linspace(imbalance_clean.min(), imbalance_clean.max(), 200)
        fitted_returns = np.polyval(coeffs, imbalance_range)
        
        correlation = imbalance_results['correlations'][str(best_horizon)]
        ax1.plot(imbalance_range, fitted_returns, color='red', linewidth=2,
                label=f'Correlation: {correlation:.3f}')
        ax1.legend()

    # Get percentiles to set limits
    y_lower = np.percentile(pct_returns.dropna(), 1)  # 1st percentile
    y_upper = np.percentile(pct_returns.dropna(), 99)  # 99th percentile
    padding = (y_upper - y_lower) * 0.1
    ax1.set_ylim(y_lower - padding, y_upper + padding)
    ax1.grid(True, alpha=0.3)

    # Second plot - Correlation decay
    correlations = imbalance_results['correlations']
    horizons = list(map(int, correlations.keys()))  # Convert string keys to int
    corr_values = list(correlations.values())

    # Convert horizons to minutes for better interpretability
    horizons_minutes = [h * 20 / 60 for h in horizons]  # 20-second snapshots

    ax2.plot(horizons_minutes, corr_values, 'o-', markersize=5, linewidth=2)
    ax2.set_xlabel('Time Horizon (minutes)')
    ax2.set_ylabel('Correlation')
    ax2.set_title('Correlation Decay Over Time')
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)  # Reference line at 0
    ax2.set_ylim(-0.05, 0.2)  # Focus on relevant range

    # Third Plot - Directional Accuracy
    accuracies = imbalance_results['directional_accuracy']
    thresholds = list(map(float, accuracies.keys()))
    accuracy_values = list(accuracies.values())

    # Convert to percentages
    accuracy_pct = [acc * 100 for acc in accuracy_values]
    
    # Bar chart
    bars = ax3.bar(range(len(thresholds)), accuracy_pct, tick_label=[f'{t:.1f}' for t in thresholds])
    ax3.axhline(y=50, color='black', linestyle='--', alpha=0.5, label='Random (50%)')
    ax3.set_xlabel('Imbalance Threshold')
    ax3.set_ylabel('Directional Accuracy (%)')
    ax3.set_title('Prediction Accuracy at Different Thresholds')
    ax3.set_ylim(40, 60)  # Focus on relevant range around 50%
    ax3.legend()
    
    # Colour bars based on whether they beat random
    for bar, acc in zip(bars, accuracy_pct):
        bar.set_color('green' if acc > 50 else 'red')

    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    
    if show:
        plt.show()
    return fig


def plot_variance_ratio_analysis(efficiency_results: Dict, save_path: Path = None, show: bool = True) -> plt.Figure:
    """
    Visualise variance ratio test results
    
    Parameters:
    efficiency_results : Dict
        Results from test_market_efficiency() containing variance_ratios
    save_path : Path, optional
        If provided, saves figure to this location
        
    Returns:
    plt.Figure
        Bar chart showing variance ratios at different lags
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    variance_ratios = efficiency_results['variance_ratios']
    lags = list(map(int, variance_ratios.keys()))
    vr_values = list(variance_ratios.values())
    
    # Create bar chart
    bars = ax.bar(range(len(lags)), vr_values, tick_label=lags)
    
    # Reference line at VR=1 (random walk)
    ax.axhline(y=1.0, color='black', linestyle='--', linewidth=2, alpha=0.5, label='Random Walk (VR=1)')
    
    # Colour bars based on VR value
    for bar, vr in zip(bars, vr_values):
        if vr < 1:
            bar.set_color('red')  # Mean reverting
        else:
            bar.set_color('green')  # Trending
    
    # Labels and formatting
    ax.set_xlabel('Lag (periods)')
    ax.set_ylabel('Variance Ratio')
    ax.set_title('Market Efficiency Test: Variance Ratios')
    ax.set_ylim(0.5, 1.2)  # Focus on relevant range
    ax.legend()
    
    # Add text with interpretation
    ax.text(0.02, 0.98, f"Avg VR: {efficiency_results['average_vr']:.3f}\n{efficiency_results['market_characterization']}", 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    if show:
        plt.show()


    return fig
