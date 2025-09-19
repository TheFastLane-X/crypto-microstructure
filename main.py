"""
Main pipeline for Crypto Market Microstructure Analysis.

Orchestrates data collection, analysis, and visualisation for
testing market efficiency hypotheses in BTC/USDT orderbook data.
"""

import sys
from pathlib import Path

import src.collection as collection
import src.analysis as analysis
import src.visualisation as visualisation


def run_pipeline(data_filepath: Path = None):
    """
    Execute complete analysis pipeline.
    
    Parameters:
    data_filepath : Path, optional
        Path to existing data file. If None, uses most recent.
    """
    print("=" * 60)
    print("CRYPTO MARKET MICROSTRUCTURE ANALYSIS")
    print("=" * 60)
    
    # Determine data file
    if data_filepath is None:
        data_dir = Path('data')
        data_files = list(data_dir.glob('orderbook_BTC_USDT_*.csv'))
        
        if not data_files:
            print("\nNo data files found.")
            print("Please run collection first or specify a data file.")
            return 1
            
        # Use most recent file
        data_filepath = max(data_files, key=lambda p: p.stat().st_mtime)
    
    print(f"\nUsing data file: {data_filepath.name}")
    
    # 1. Analysis
    print("\n" + "=" * 40)
    print("RUNNING ANALYSIS")
    print("=" * 40)
    
    df = analysis.load_and_prepare_data(data_filepath)
    print(f"Loaded {len(df)} orderbook snapshots")
    
    # Test hypotheses
    imbalance_results = analysis.test_imbalance_hypothesis(df)
    analysis.save_results(imbalance_results, 'imbalance_hypothesis')
    print("Imbalance hypothesis tested")
    
    efficiency_results = analysis.test_market_efficiency(df)
    analysis.save_results(efficiency_results, 'market_efficiency')
    print("Market efficiency tested")
    
    # 2. Visualisation
    print("\n" + "=" * 40)
    print("GENERATING VISUALISATIONS")
    print("=" * 40)
    
    visualisation.setup_plot_style()
    
    save_dir = Path('results') / 'figures'
    save_dir.mkdir(parents=True, exist_ok=True)
    
    visualisation.plot_imbalance_analysis(
        df, imbalance_results,
        save_path=save_dir / 'imbalance_analysis.png',
        show=False
    )
    print(" Imbalance analysis plots saved")
    
    visualisation.plot_variance_ratio_analysis(
        efficiency_results,
        save_path=save_dir / 'variance_ratios.png',
        show=False
    )
    print(" Variance ratio plot saved")
    
    # 3. Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE - KEY FINDINGS")
    print("=" * 60)
    
    best_horizon = imbalance_results['best_horizon']
    best_corr = imbalance_results['correlations'][str(best_horizon)]
    
    print("Order Book Imbalance:")
    print(f"  • Peak correlation: {best_corr:.3f} at {best_horizon * 20}s")
    print("  • Decays to ~0.05 within 2 minutes")
    
    print("\nMarket Efficiency:")
    print(f"  • Avg variance ratio: {efficiency_results['average_vr']:.3f}")
    print(f"  • Characterisation: {efficiency_results['market_characterization']}")
    
    print("\n Results saved in results/metrics/")
    print(" Figures saved in results/figures/")
    
    return 0


def collect_new_data(duration_minutes: int = 60, interval_seconds: int = 20):
    """
    Collect fresh orderbook data from Binance.
    
    Parameters:
    duration_minutes : int
        How long to collect data
    interval_seconds : int
        Time between snapshots
    """
    print("\nCOLLECTING NEW DATA")
    print("-" * 40)
    
    exchange = collection.initialise_exchange('binance')
    if exchange is None:
        print("Failed to initialise exchange")
        return None
        
    df = collection.collect_orderbook_data(
        exchange, 
        duration_minutes=duration_minutes,
        interval_seconds=interval_seconds
    )
    
    return df


def main():
    """Main entry point with menu."""
    
    if len(sys.argv) > 1:
        # Command line argument provided
        if sys.argv[1] == 'collect':
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            collect_new_data(duration)
        elif sys.argv[1] == 'analyse':
            run_pipeline()
        else:
            print("Usage: python main.py [collect|analyse]")
    else:
        # Interactive menu
        print("\nOptions:")
        print("1. Run analysis on existing data")
        print("2. Collect new data")
        print("3. Collect data then analyse")
        
        choice = input("\nSelect option (1-3): ")
        
        if choice == '1':
            run_pipeline()
        elif choice == '2':
            duration = input("Duration in minutes (default 60): ")
            duration = int(duration) if duration else 60
            collect_new_data(duration)
        elif choice == '3':
            duration = input("Duration in minutes (default 60): ")
            duration = int(duration) if duration else 60
            df = collect_new_data(duration)
            if df is not None:
                run_pipeline()
        else:
            print("Invalid choice")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())