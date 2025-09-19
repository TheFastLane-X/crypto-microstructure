"""
Crypto Market Microstructure Analysis

This module analyzes orderbook data collected from cryptocurrency exchanges
to test two hypotheses about market behavior:
1. Order flow imbalance predicts future price direction
2. Market efficiency via variance ratio test
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


# Data preparation functions
def load_and_prepare_data(filepath: Path) -> pd.DataFrame:
    """
    Load CSV and perform basic cleaning

    Parameters:
    filepath: Path  
        filepath of raw data csv made by collection to be cleaned
    
    Returns:
    df: pd.DataFrame
        Cleaned DataFrame ready for analysis
    """

    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')

    # columns to keep for testing my specific hypotheses
    columns_to_keep = ['spread_bps', 'mid_price', 'imbalance_5', 'spread', 'best_bid', 'best_ask']
    df = df[columns_to_keep].apply(pd.to_numeric, errors = 'coerce')

    return df


def test_imbalance_hypothesis(df, horizons: list[int] = list(range(1,31)), thresholds: list[float] = [0.3, 0.5, 0.7]) -> dict:
    """
    Test relationship between order book imbalance and future price movements
    
    Analyzes whether order flow imbalance correlates with and predicts
    price direction across multiple time horizons and imbalance thresholds
    
    Parameters:
    df : pd.DataFrame
        Orderbook data with 'mid_price' and 'imbalance_5' columns
        Index should be timestamp.
    horizons : list[int], default=[3, 10, 30]
        Forward-looking periods to test (in snapshot intervals)
        Default represents 1min, 3.3min, 10min at 20-second intervals
    thresholds : list[float], default=[0.3, 0.5, 0.7]
        Absolute imbalance thresholds for directional accuracy test
        Tests only periods where |imbalance| exceeds threshold
        Values should be between 0 and 1 inclusive
    
    Returns:
    dict
        Results dictionary containing:
        - 'correlations' : dict[int, float]
            Correlation between imbalance and returns for each horizon
        - 'best_horizon' : int
            Horizon with highest absolute correlation
        - 'directional_accuracy' : dict[float, float]
            Accuracy of directional prediction for each threshold
            (whether sign(imbalance) matches sign(return))
    
    Notes:
    Uses the best-correlated horizon for directional accuracy testing
    Positive imbalance indicates more bid volume 
    """

    if 'mid_price' not in df.columns or 'imbalance_5' not in df.columns:
        raise ValueError("Required columns missing from DataFrame")

    results = {}
    
    # Test correlation at different horizons
    correlations = {}
    for horizon in horizons:
        returns = df['mid_price'].pct_change(periods=horizon).shift(-horizon)
        corr = float(df['imbalance_5'].corr(returns))
        correlations[horizon] = corr
    
    results['correlations'] = correlations
    results['best_horizon'] = max(correlations, key=correlations.get)
    
    # Test directional accuracy (using best horizon)
    best_h = results['best_horizon']
    df['returns'] = df['mid_price'].pct_change(periods=best_h).shift(-best_h)
    
    accuracies = {}
    for threshold in thresholds:
        strong_imbalance = abs(df['imbalance_5']) > threshold
        subset = df[strong_imbalance].dropna()
        
        if len(subset) > 0:
            correct = (np.sign(subset['imbalance_5']) == np.sign(subset['returns'])).sum()
            accuracy = float(correct / len(subset))
            accuracies[threshold] = accuracy
    
    results['directional_accuracy'] = accuracies
    
    return results
 

def test_market_efficiency(df: pd.DataFrame, lags: list[int] = [2, 5, 7, 10, 15, 20, 25, 30]) -> dict:
    """
    Variance ratio test for market efficiency 
    
    Tests whether price follows random walk by comparing variance 
    at different time scales. Under random walk, variance should
    scale linearly with time.
    
    Parameters:
    df : pd.DataFrame
        Data with 'mid_price' column
    lags : list, default=[2, 5, 10, 20]
        Periods to test (k-period returns vs 1-period)
        
    Returns:
    dict
        'variance_ratios': dict of lag:ratio pairs
        'market_characterization': str description
        'test_statistics': dict with z-scores for significance
        
    Notes:
    VR(k) = Var(k-period return) / (k * Var(1-period return))
    VR = 1: Random walk (efficient)
    VR < 1: Mean reversion
    VR > 1: Trending/momentum
    """
    
    # initialise results dictionary
    variance_ratios = {}

    # Calculating 1 period log returns. removing NaNs
    log_returns = np.log(df['mid_price'] / df['mid_price'].shift(1))
    log_returns = log_returns.dropna()

    variance = log_returns.var()

    # For each lag, calculate k-period returns and variance ratio
    for k in lags:
        # Calculate k-period returns (NOT summing)
        log_returns_k = np.log(df['mid_price'] / df['mid_price'].shift(k))
        log_returns_k = log_returns_k.dropna()
        
        # Calculate variance of k-period returns
        var_k = log_returns_k.var()
        
        # Calculate variance ratio
        var_ratio = float(var_k / (k * variance))
        variance_ratios[k] = var_ratio

    
    avg_vr = np.mean(list(variance_ratios.values()))
    
    if avg_vr > 1.1:
        characterization = "Trending/Momentum"
    elif avg_vr < 0.9:
        characterization = "Mean-reverting"
    else:
        characterization = "Approximately efficient (random walk)"
    
    vr_results = {
        'variance_ratios': variance_ratios,
        'average_vr': avg_vr,
        'market_characterization': characterization,
    }
    
    return vr_results
    

def save_results(results: dict, analysis_name: str):
    """
    Save analysis results to json file.
    
    """

    results_dir = Path('results') / 'metrics'
    # Creates dirs if needed
    results_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = results_dir / f'{analysis_name}_results.json'
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filepath}")

  



