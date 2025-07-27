#!/usr/bin/env python3
"""
Example usage of the Coinbase real-time crypto data collector

This script demonstrates how to use the CoinbaseRealtimeCollector class
to fetch real-time OHLCV data for different cryptocurrencies.
"""

import time
import datetime
from pathlib import Path
from coinbase_realtime_data import CoinbaseRealtimeCollector


def simple_callback(df):
    """Simple callback function to print latest data"""
    latest = df.iloc[-1]
    print(f"[{latest['date'].strftime('%Y-%m-%d %H:%M:%S')}] "
          f"{latest['symbol']}: "
          f"O:{latest['open']:.4f} H:{latest['high']:.4f} "
          f"L:{latest['low']:.4f} C:{latest['close']:.4f} V:{latest['volume']:.2f}")


def detailed_callback(df):
    """Detailed callback function with more information"""
    latest = df.iloc[-1]
    change = latest['close'] - latest['open']
    change_pct = (change / latest['open']) * 100
    
    print(f"\n{'='*60}")
    print(f"Symbol: {latest['symbol']}")
    print(f"Time: {latest['date'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Price: ${latest['close']:.4f}")
    print(f"Change: ${change:+.4f} ({change_pct:+.2f}%)")
    print(f"OHLC: ${latest['open']:.4f} / ${latest['high']:.4f} / "
          f"${latest['low']:.4f} / ${latest['close']:.4f}")
    print(f"Volume: {latest['volume']:.2f}")
    print(f"{'='*60}")


def example_single_symbol():
    """Example: Collect data for a single symbol"""
    print("Example 1: Single symbol collection (ETH, 1-minute intervals)")
    print("-" * 60)
    
    # Create collector for ETH with 1-minute intervals
    collector = CoinbaseRealtimeCollector(
        symbol='ETH',
        interval='1m',
        save_dir='./data/eth_realtime',
        callback=simple_callback
    )
    
    try:
        # Start collection
        collector.start()
        
        # Collect data for 5 minutes
        print("Collecting ETH data for 5 minutes...")
        time.sleep(300)  # 5 minutes
        
        # Get collected data
        all_data = collector.get_all_data()
        print(f"\nCollected {len(all_data)} data points")
        print(f"Data range: {all_data['date'].min()} to {all_data['date'].max()}")
        
    finally:
        collector.stop()


def example_multiple_symbols():
    """Example: Collect data for multiple symbols simultaneously"""
    print("\nExample 2: Multiple symbols collection")
    print("-" * 60)
    
    # Create collectors for different symbols
    collectors = {
        'BTC': CoinbaseRealtimeCollector('BTC', '5m', callback=simple_callback),
        'ETH': CoinbaseRealtimeCollector('ETH', '5m', callback=simple_callback),
        'ADA': CoinbaseRealtimeCollector('ADA', '5m', callback=simple_callback)
    }
    
    try:
        # Start all collectors
        for symbol, collector in collectors.items():
            collector.start()
            print(f"Started collection for {symbol}")
        
        # Collect data for 3 minutes
        print("Collecting data for 3 minutes...")
        time.sleep(180)  # 3 minutes
        
        # Get data from each collector
        for symbol, collector in collectors.items():
            data = collector.get_all_data()
            print(f"\n{symbol}: Collected {len(data)} data points")
            if not data.empty:
                latest = data.iloc[-1]
                print(f"Latest {symbol} price: ${latest['close']:.4f}")
        
    finally:
        # Stop all collectors
        for collector in collectors.values():
            collector.stop()


def example_different_intervals():
    """Example: Collect data with different intervals"""
    print("\nExample 3: Different intervals collection")
    print("-" * 60)
    
    # Create collectors with different intervals
    collectors = {
        '1m': CoinbaseRealtimeCollector('BTC', '1m', callback=simple_callback),
        '5m': CoinbaseRealtimeCollector('BTC', '5m', callback=simple_callback),
        '15m': CoinbaseRealtimeCollector('BTC', '15m', callback=simple_callback)
    }
    
    try:
        # Start all collectors
        for interval, collector in collectors.items():
            collector.start()
            print(f"Started BTC collection with {interval} interval")
        
        # Collect data for 10 minutes
        print("Collecting data for 10 minutes...")
        time.sleep(600)  # 10 minutes
        
        # Compare data collection frequency
        for interval, collector in collectors.items():
            data = collector.get_all_data()
            print(f"\n{interval} interval: Collected {len(data)} data points")
        
    finally:
        # Stop all collectors
        for collector in collectors.values():
            collector.stop()


def example_data_analysis():
    """Example: Basic data analysis on collected data"""
    print("\nExample 4: Data analysis on collected data")
    print("-" * 60)
    
    # Create collector with detailed callback
    collector = CoinbaseRealtimeCollector(
        symbol='ETH',
        interval='1m',
        callback=detailed_callback
    )
    
    try:
        # Start collection
        collector.start()
        
        # Collect data for 2 minutes
        print("Collecting ETH data for 2 minutes...")
        time.sleep(120)  # 2 minutes
        
        # Perform basic analysis
        data = collector.get_all_data()
        if not data.empty:
            print(f"\nData Analysis for ETH:")
            print(f"Total data points: {len(data)}")
            print(f"Price range: ${data['low'].min():.4f} - ${data['high'].max():.4f}")
            print(f"Average volume: {data['volume'].mean():.2f}")
            print(f"Price volatility: {data['close'].std():.4f}")
            
            # Calculate price change
            first_price = data.iloc[0]['close']
            last_price = data.iloc[-1]['close']
            total_change = ((last_price - first_price) / first_price) * 100
            print(f"Total price change: {total_change:+.2f}%")
        
    finally:
        collector.stop()


def example_save_to_file():
    """Example: Save data to files"""
    print("\nExample 5: Save data to files")
    print("-" * 60)
    
    # Create save directory
    save_dir = Path('./data/saved_realtime')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Create collector with file saving
    collector = CoinbaseRealtimeCollector(
        symbol='BTC',
        interval='1m',
        save_dir=str(save_dir),
        callback=simple_callback
    )
    
    try:
        # Start collection
        collector.start()
        
        # Collect data for 3 minutes
        print("Collecting BTC data for 3 minutes...")
        time.sleep(180)  # 3 minutes
        
        # Check saved files
        saved_files = list(save_dir.glob('*.csv'))
        print(f"\nSaved files: {len(saved_files)}")
        for file in saved_files:
            print(f"  - {file.name}")
        
    finally:
        collector.stop()


if __name__ == "__main__":
    print("Coinbase Real-time Crypto Data Collector Examples")
    print("=" * 60)
    
    # Run examples
    try:
        example_single_symbol()
        example_multiple_symbols()
        example_different_intervals()
        example_data_analysis()
        example_save_to_file()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
    
    print("\nAll examples completed!") 