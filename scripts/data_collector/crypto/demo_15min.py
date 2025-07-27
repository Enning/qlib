#!/usr/bin/env python3
"""
Demo script for 15-minute crypto data collection
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def get_15min_data(symbol, days=1):
    """Get 15-minute data for a specific symbol"""
    print(f"Fetching {days} days of 15-minute data for {symbol}...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles"
        params = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'granularity': 900  # 15 minutes
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            print(f"❌ No data returned for {symbol}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['symbol'] = symbol
        
        # Reorder columns
        df = df[['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        
        print(f"✅ Retrieved {len(df)} 15-minute records for {symbol}")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        return None


def analyze_15min_data(df):
    """Analyze the 15-minute data"""
    if df is None or df.empty:
        print("❌ No data to analyze")
        return
    
    print(f"\n📊 15-Minute Data Analysis for {df['symbol'].iloc[0]}:")
    print(f"   Records: {len(df)}")
    print(f"   Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print(f"   Average volume: {df['volume'].mean():.2f}")
    
    # Calculate returns
    df['return'] = df['close'].pct_change()
    print(f"   Average 15-min return: {df['return'].mean():.2%}")
    print(f"   Volatility (std): {df['return'].std():.2%}")
    
    # Check time intervals
    time_diffs = df['datetime'].diff().dropna()
    avg_interval = time_diffs.mean().total_seconds() / 60
    print(f"   Average time interval: {avg_interval:.1f} minutes")
    
    # Records per day
    days_covered = (df['datetime'].max() - df['datetime'].min()).total_seconds() / (24 * 3600)
    records_per_day = len(df) / days_covered
    print(f"   Records per day: {records_per_day:.0f} (expected: ~96)")


def save_15min_data(df, filename):
    """Save 15-minute data to CSV file"""
    try:
        df.to_csv(filename, index=False)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")


def main():
    """Main demo function"""
    print("=" * 60)
    print("15-Minute Crypto Data Collection Demo")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("./demo_15min_output")
    output_dir.mkdir(exist_ok=True)
    
    # Test symbols
    symbols = ['BTC', 'ETH', 'SOL']
    
    # Collect data for each symbol
    all_data = []
    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f"Processing: {symbol}")
        print(f"{'='*40}")
        
        df = get_15min_data(symbol, days=1)
        if df is not None:
            # Analyze the data
            analyze_15min_data(df)
            
            # Save individual file
            save_15min_data(df, output_dir / f"{symbol}_15min_data.csv")
            
            all_data.append(df)
        
        # Small delay to be respectful to API
        import time
        time.sleep(1)
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        save_15min_data(combined_df, output_dir / "combined_15min_data.csv")
        
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successfully collected 15-minute data for {len(all_data)} cryptocurrencies")
        print(f"✅ Total records: {len(combined_df)}")
        print(f"✅ Data saved to: {output_dir}")
        print(f"✅ Files created:")
        for file in output_dir.glob("*.csv"):
            print(f"   - {file.name}")
        
        print(f"\n📈 Sample 15-minute data:")
        print(combined_df.head(10))
        
        # Show time distribution
        print(f"\n⏰ Time distribution:")
        time_counts = combined_df['datetime'].dt.hour.value_counts().sort_index()
        for hour, count in time_counts.items():
            print(f"   {hour:02d}:00 - {hour:02d}:59: {count} records")
        
    else:
        print("❌ No data was collected successfully")


if __name__ == "__main__":
    main() 