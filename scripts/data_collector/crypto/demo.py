#!/usr/bin/env python3
"""
Demo script for Coinbase crypto data collector
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def get_coinbase_symbols():
    """Get available cryptocurrency symbols from Coinbase"""
    print("Fetching available cryptocurrencies from Coinbase...")
    
    try:
        url = "https://api.exchange.coinbase.com/products"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        products = resp.json()
        
        # Filter for USD pairs
        usd_pairs = [product['base_currency'] for product in products 
                    if product['quote_currency'] == 'USD' and product['status'] == 'online']
        
        print(f"✅ Found {len(usd_pairs)} USD trading pairs")
        return usd_pairs[:10]  # Return first 10 for demo
        
    except Exception as e:
        print(f"❌ Error fetching symbols: {e}")
        return ['BTC', 'ETH', 'SOL']  # Fallback


def get_crypto_data(symbol, days=7):
    """Get crypto data for a specific symbol"""
    print(f"Fetching {days} days of data for {symbol}...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles"
        params = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'granularity': 86400  # 1 day
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
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        df['symbol'] = symbol
        
        # Reorder columns
        df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        
        print(f"✅ Retrieved {len(df)} records for {symbol}")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        return None


def save_data(df, filename):
    """Save data to CSV file"""
    try:
        df.to_csv(filename, index=False)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")


def analyze_data(df):
    """Analyze the collected data"""
    if df is None or df.empty:
        print("❌ No data to analyze")
        return
    
    print(f"\n📊 Data Analysis for {df['symbol'].iloc[0]}:")
    print(f"   Records: {len(df)}")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print(f"   Average volume: {df['volume'].mean():.2f}")
    
    # Calculate returns
    df['return'] = df['close'].pct_change()
    print(f"   Average daily return: {df['return'].mean():.2%}")
    print(f"   Volatility (std): {df['return'].std():.2%}")


def main():
    """Main demo function"""
    print("=" * 60)
    print("Coinbase Crypto Data Collector Demo")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("./demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # Get available symbols
    symbols = get_coinbase_symbols()
    print(f"Demo symbols: {symbols}")
    
    # Collect data for each symbol
    all_data = []
    for symbol in symbols[:3]:  # Limit to 3 for demo
        print(f"\n{'='*40}")
        print(f"Processing: {symbol}")
        print(f"{'='*40}")
        
        df = get_crypto_data(symbol, days=30)
        if df is not None:
            # Analyze the data
            analyze_data(df)
            
            # Save individual file
            save_data(df, output_dir / f"{symbol}_data.csv")
            
            all_data.append(df)
        
        # Small delay to be respectful to API
        import time
        time.sleep(1)
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        save_data(combined_df, output_dir / "combined_data.csv")
        
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successfully collected data for {len(all_data)} cryptocurrencies")
        print(f"✅ Total records: {len(combined_df)}")
        print(f"✅ Data saved to: {output_dir}")
        print(f"✅ Files created:")
        for file in output_dir.glob("*.csv"):
            print(f"   - {file.name}")
        
        print(f"\n📈 Sample data:")
        print(combined_df.head())
        
    else:
        print("❌ No data was collected successfully")


if __name__ == "__main__":
    main() 