#!/usr/bin/env python3
"""
Simple demonstration of the Coinbase real-time crypto data collector

This script shows a quick example of how to use the real-time collector
to fetch ETH data with 1-minute intervals.
"""

import time
from coinbase_realtime_data import CoinbaseRealtimeCollector


def simple_callback(df):
    """Simple callback to print latest data"""
    latest = df.iloc[-1]
    print(f"[{latest['date'].strftime('%H:%M:%S')}] "
          f"{latest['symbol']}: "
          f"O:{latest['open']:.4f} H:{latest['high']:.4f} "
          f"L:{latest['low']:.4f} C:{latest['close']:.4f} V:{latest['volume']:.2f}")


def main():
    print("Coinbase Real-time Crypto Data Collector Demo")
    print("=" * 50)
    print("This demo will collect ETH data for 2 minutes with 1-minute intervals")
    print("Press Ctrl+C to stop early")
    print()
    
    # Create collector
    collector = CoinbaseRealtimeCollector(
        symbol='ETH',
        interval='1m',
        callback=simple_callback
    )
    
    try:
        # Start collection
        print("Starting data collection...")
        collector.start()
        
        # Collect data for 2 minutes
        print("Collecting data for 2 minutes...")
        time.sleep(120)  # 2 minutes
        
        # Get collected data
        all_data = collector.get_all_data()
        print(f"\nCollection completed!")
        print(f"Total data points collected: {len(all_data)}")
        
        if not all_data.empty:
            print(f"Data range: {all_data['date'].min()} to {all_data['date'].max()}")
            print(f"Price range: ${all_data['low'].min():.4f} - ${all_data['high'].max():.4f}")
            print(f"Latest price: ${all_data.iloc[-1]['close']:.4f}")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error during demo: {e}")
    finally:
        collector.stop()
        print("Demo completed!")


if __name__ == "__main__":
    main() 