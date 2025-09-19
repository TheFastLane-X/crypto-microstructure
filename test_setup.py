
"""
Environment setup verification for Crypto Microstructure Project.

Checks that all required packages are installed and verifies
connectivity to the Binance exchange for orderbook data access.
"""

import sys
from typing import Tuple


def check_package(package_name: str) -> Tuple[bool, str]:
    """
    Check if a package is installed and get its version.
    
    Parameters:
    package_name : str
        Name of package to check
        
    Returns:
    Tuple[bool, str]
        (is_installed, version_string or error message)
    """
    try:
        package = __import__(package_name)
        version = getattr(package, '__version__', 'version unknown')
        return True, f"{package_name} version: {version}"
    except ImportError:
        return False, f"{package_name} not installed"


def test_exchange_connection() -> bool:
    """
    Test connection to Binance exchange and fetch sample orderbook.
    
    Returns:
    bool
        True if connection successful, False otherwise
    """
    try:
        import ccxt
        
        print("\nTesting Exchange Connection:")
        print("-" * 30)
        
        exchange = ccxt.binance()
        exchange.load_markets()
        print(f"Connected to Binance")
        print(f"Loaded {len(exchange.symbols)} trading pairs")
        
        # Test orderbook fetch
        orderbook = exchange.fetch_order_book('BTC/USDT', limit=5)
        if orderbook['bids'] and orderbook['asks']:
            spread = orderbook['asks'][0][0] - orderbook['bids'][0][0]
            mid_price = (orderbook['asks'][0][0] + orderbook['bids'][0][0]) / 2
            spread_bps = (spread / mid_price) * 10000
            
            print(f"Successfully fetched BTC/USDT orderbook")
            print(f"  - Best Bid: ${orderbook['bids'][0][0]:,.2f}")
            print(f"  - Best Ask: ${orderbook['asks'][0][0]:,.2f}")
            print(f"  - Spread: ${spread:.2f} ({spread_bps:.2f} bps)")
            return True
    except Exception as e:
        print(f"Exchange connection failed: {e}")
        return False
    
    return False


def main():
    """Run environment check for the project."""
    print("=" * 50)
    print("CRYPTO MICROSTRUCTURE PROJECT - ENVIRONMENT CHECK")
    print("=" * 50)
    print(f"\nPython version: {sys.version}")
    
    # Required packages
    required_packages = ['ccxt', 'pandas', 'numpy', 'matplotlib']
    package_status = {}
    
    print("\nPackage Status:")
    print("-" * 30)
    
    for package in required_packages:
        installed, message = check_package(package)
        package_status[package] = installed
        print(message)
    
    # Test exchange connection if ccxt is installed
    if package_status.get('ccxt', False):
        connection_success = test_exchange_connection()
    else:
        print("\nSkipping exchange test (ccxt not installed)")
        connection_success = False
    
    # Summary
    all_packages_installed = all(package_status.values())
    
    print("\n" + "=" * 50)
    if all_packages_installed and connection_success:
        print("All checks passed - ready to run project!")
        return 0
    elif all_packages_installed:
        print("Packages installed but exchange connection failed")
        return 1
    else:
        print("Missing packages - run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())