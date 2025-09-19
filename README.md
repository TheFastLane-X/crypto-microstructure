# Crypto Market Microstructure Analysis

Analysis of BTC/USDT orderbook data to test market efficiency hypotheses through order flow imbalance and variance ratio tests.

## Project Overview

This project examines whether orderbook imbalance can predict short-term price movements in cryptocurrency markets and tests market efficiency using variance ratio analysis. Using 12 hours of orderbook data from Binance (2,161 snapshots at 20-second intervals), the analysis confirms that the BTC/USDT market exhibits strong efficiency with minimal predictable patterns.

## Key Findings

### Order Book Imbalance
- Correlation between imbalance and forward returns: 0.177 at 20 seconds
- Correlation decays to ~0.05 within 2 minutes
- Directional accuracy: 52-56% (marginally better than random)

### Market Efficiency
- Average variance ratio: 0.758 (indicating mean reversion)
- Pattern consistent with bid-ask bounce rather than exploitable inefficiency
- Variance ratios decline from 0.91 (lag 2 snapshots) to 0.68 (lag 30 snapshots)

## Project Structure

    crypto-microstructure/
    ├── src/
    │   ├── __init__.py
    │   ├── collection.py       # Orderbook data collection via CCXT
    │   ├── analysis.py         # Statistical tests and hypothesis testing
    │   └── visualisation.py    # Generate analysis plots
    ├── data/                   # CSV files with orderbook snapshots
    ├── results/
    │   ├── figures/           # PNG visualisations
    │   └── metrics/           # JSON test results
    ├── main.py                # Pipeline orchestration
    ├── test_setup.py          # Environment verification
    └── requirements.txt       # Package dependencies

## Installation

Clone repository:
```bash
git clone git@github.com:TheFastLane-X/crypto-microstructure.git
cd crypto-microstructure
```

Install dependencies:
```bash
pip install -r requirements.txt 
```
Verify environment:
```bash
python test_setup.py
```

## Usage

### Run complete pipeline
- Interactive menu:
```bash
python main.py
```
- Command line options:
```bash
python main.py analyse      # Analyse existing data
python main.py collect 720  # Collect 12 hours of new data
```

### Module-specific usage
```python
from src import collection, analysis, visualisation

# Collect data
exchange = collection.initialise_exchange('binance')
df = collection.collect_orderbook_data(exchange, duration_minutes=60)

# Run analysis
imbalance_results = analysis.test_imbalance_hypothesis(df)
efficiency_results = analysis.test_market_efficiency(df)

# Generate plots
visualisation.plot_imbalance_analysis(df, imbalance_results)
```

## Methodology

### Data Collection
- **Source**: Binance spot market via CCXT
- **Pair**: BTC/USDT (most liquid crypto pair)
- **Frequency**: 20-second snapshots
- **Depth**: 20 orderbook levels
- **Features**: Mid price, spread, bid/ask depths, order flow imbalance

### Hypothesis Tests

**H1: Order Flow Imbalance → Price Direction**
- Tested correlation between normalised volume imbalance and forward returns
- Evaluated at multiple horizons (20 seconds to 10 minutes)
- Measured directional accuracy at different imbalance thresholds

**H2: Market Efficiency (Variance Ratio Test)**
- VR(k) = Var(k-period return) / (k × Var(1-period return))
- VR = 1 indicates random walk (efficient market)
- VR < 1 indicates mean reversion
- VR > 1 indicates trending/momentum

## Results Interpretation

The analysis demonstrates that while orderbook imbalance has a weak positive correlation with immediate price movements, this information is rapidly incorporated by the market. The correlation of 0.177 at 20 seconds decays exponentially, reaching near-zero within 2 minutes.

Variance ratios below 1.0 initially suggest mean reversion, but the declining pattern with increasing lag indicates this is microstructure noise (bid-ask bounce) rather than an exploitable trading opportunity. After accounting for transaction costs, no profitable strategy emerges.

These findings align with market efficiency theory: the BTC/USDT market quickly processes orderbook information, leaving minimal predictable patterns for systematic trading strategies.

## Technologies Used
- Python 3.13
- CCXT for exchange connectivity
- Pandas/NumPy for data analysis
- Matplotlib for visualisation

## Future Improvements
- Extend analysis to multiple cryptocurrency pairs (ETH/USDT, SOL/USDT)
- Collect data over longer time periods (multiple days/weeks)
- Implement websocket streaming for real-time data collection
- Test stability of patterns across different market conditions

## Author
Gurpal Bains - [GitHub](https://github.com/TheFastLane-X)