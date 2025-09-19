"""
Collection of data functions for cryptocurrency orderbook snapshots.

Functions for connecting to exchanges via CCXT, fetching orderbook data,
and collecting time series of market microstructure data.
"""

import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta


def initialise_exchange(exchange_id: str = 'binance') -> ccxt.Exchange:
    """
    Initialize and return exchange object

    Args:
        exchange_id: Name of exchange (default 'binance')

    Returns:
        ccxt.Exchange object
    """

    try:

        exchange_class = getattr(ccxt, exchange_id)
        exchange: ccxt.Exchange = exchange_class()
        exchange.load_markets()
        exchange.enableRateLimit = True
        return exchange

    except Exception as e:
        print(f"Error: {e}")
        return None


def fetch_orderbook_snapshot(exchange: ccxt.Exchange, symbol: str = 'BTC/USDT', depth: int = 20) -> dict:
    """
    Fetch a single orderbook snapshot with error handling

    Args:
        exchange (str): exchange str to be converted to ccxt object
        symbol (str, optional): symbol for orderbook snapshot. Defaults to 'BTC/USDT'.
        depth (int, optional): how deep to go in orderbook. Defaults to 20.
    """
    try: 
        orderbook = exchange.fetch_order_book(symbol, limit = depth)

        snapshot_time = datetime.now()

        snapshot: dict =  {
            'timestamp': int(snapshot_time.timestamp() * 1000),
            'datetime' : snapshot_time.isoformat(),
            'symbol': symbol,

            'best_bid': orderbook['bids'][0][0] if orderbook['bids'] else None,
            'best_ask': orderbook['asks'][0][0] if orderbook['asks'] else None,
            'best_bid_size': orderbook['bids'][0][1] if orderbook['bids'] else None,
            'best_ask_size': orderbook['asks'][0][1] if orderbook['asks'] else None,

            # Store full orderbook depth (for later analysis)
            'bids': orderbook['bids'][:depth],  # List of [price, size] pairs
            'asks': orderbook['asks'][:depth],

            # Calculate aggregate metrics
            'bid_depth_5': sum([bid[1] for bid in orderbook['bids'][:5]]) if len(orderbook['bids']) >= 5 else None,
            'ask_depth_5': sum([ask[1] for ask in orderbook['asks'][:5]]) if len(orderbook['asks']) >= 5 else None,
            'bid_depth_10': sum([bid[1] for bid in orderbook['bids'][:10]]) if len(orderbook['bids']) >= 10 else None,
            'ask_depth_10': sum([ask[1] for ask in orderbook['asks'][:10]]) if len(orderbook['asks']) >= 10 else None,
        }
       
       # Calculate derived metrics
        if snapshot['best_bid'] and snapshot['best_ask']:
            snapshot['spread'] = snapshot['best_ask'] - snapshot['best_bid']
            snapshot['spread_bps'] = (snapshot['spread'] / snapshot['best_bid']) * 10000  # Basis points
            snapshot['mid_price'] = (snapshot['best_bid'] + snapshot['best_ask']) / 2

            # Order book imbalance
            if snapshot['bid_depth_5'] and snapshot['ask_depth_5']:
                total_depth = snapshot['bid_depth_5'] + snapshot['ask_depth_5']
                snapshot['imbalance_5'] = (snapshot['bid_depth_5'] - snapshot['ask_depth_5']) / total_depth


        return snapshot

    except Exception as e:
        print(f"Error fetching orderbook: {e}")
        return None


def collect_orderbook_data(exchange: ccxt.Exchange, duration_minutes = 5, interval_seconds = 10, symbol = 'BTC/USDT') -> pd.DataFrame:
    """
    Collect orderbook snapshots over specified duration

    Args:
        exchange (ccxt.Exchange): exchange object
        duration_minutes (int, optional): Duration for taking snapshots. Defaults to 5.
        interval_seconds (int, optional): time interval between snapshots. Defaults to 10.
        symbol (str): trading pair for snapshots
    """

    print("\n" + "=" * 50)
    print("STARTING DATA COLLECTION")
    print("=" * 50)
    print(f"Symbol: {symbol}")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Interval: {interval_seconds} seconds")
    print(f"Expected snapshots: ~{duration_minutes * 60 // interval_seconds}")
    print("=" * 50 + "\n")

    # Storage for snapshots
    snapshots = []

    # Calculate end time
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes = duration_minutes)

    # Collection Loop
    snapshot_count = 0
    errors = 0

    # set first target time
    next_target = time.time()

    while datetime.now() < end_time:
        # Track when iteration starts
        now = time.time()
        wait_time = next_target - now

        if wait_time > 0:
            time.sleep(wait_time)
        elif wait_time < -1:
            print(f"[WARNING] Running {-wait_time:.1f}s behind schedule")
        # Fetch snapshot
        snapshot = fetch_orderbook_snapshot(exchange, symbol=symbol)

        if snapshot:
            snapshots.append(snapshot)
            snapshot_count += 1
            
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = (end_time - datetime.now()).total_seconds()

            print(f"[{snapshot_count:4d}] {datetime.now().strftime('%H:%M:%S')} | "
                  f"Spread: {snapshot.get('spread_bps', 0):5f} bps | "
                  f"Mid: ${snapshot.get('mid_price', 0):5f} | "
                  f"Imbalance: {snapshot.get('imbalance_5', 0):+.3f} | "
                  f"Elapsed: {elapsed: 0f}s | "
                  f"Remaining: {remaining:.0f}s")
        

        else:
            errors += 1
            print(f"[ERROR] Failed to fetch snapshot (total errors: {errors})")

        next_target += interval_seconds
        

    # Save collected data
    if snapshots:
        df = pd.DataFrame(snapshots)

        # Drop the nested lists (as not needed for the analysis)
        df = df.drop(columns=['bids', 'asks'], errors='ignore')
        #set timestamp as index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit = 'ms')
        df = df.set_index('timestamp')

        # Save to CSV
        timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"data/orderbook_{symbol.replace('/', '_')}_{timestamp_str}.csv"
        df.to_csv(filename)


        print("\n" + "=" * 50)
        print("COLLECTION COMPLETE")
        print("=" * 50)
        print(f"Total snapshots: {snapshot_count}")
        print(f"Errors: {errors}")
        print(f"Success rate: {(snapshot_count/(snapshot_count+errors)*100 if snapshot_count+errors > 0 else 0):.1f}%")
        print(f"Data saved to: {filename}")
        print(f"Data shape: {df.shape}")
        print("=" * 50)

        return df
        
    else:
        print("No snapshots collected!")
        return None

