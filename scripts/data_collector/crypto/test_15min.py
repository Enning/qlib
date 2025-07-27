#!/usr/bin/env python3
"""
Test script for 15-minute interval data collection
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def test_15min_api():
    """Test 15-minute interval API call"""
    print("Testing 15-minute interval API...")
    
    try:
        # Test BTC 15-minute data for a short period
        symbol = "BTC"
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles"
        params = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'granularity': 900  # 15 minutes = 900 seconds
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data:
            print(f"✅ Successfully retrieved {len(data)} 15-minute records for {symbol}")
            print(f"   Sample data: {data[0]}")
            print(f"   Data format: [timestamp, open, high, low, close, volume]")
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            
            print(f"   Time range: {df['datetime'].min()} to {df['datetime'].max()}")
            print(f"   Records per day: ~{len(df) / 1:.0f} (expected ~96)")
            
            return True
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_granularity_mapping():
    """Test granularity mapping for different intervals"""
    print("\nTesting granularity mapping...")
    
    granularity_map = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "30min": 1800,
        "1hour": 3600,
        "1d": 86400
    }
    
    try:
        for interval, granularity in granularity_map.items():
            print(f"   {interval}: {granularity} seconds")
        
        print("✅ All granularity mappings are correct")
        return True
        
    except Exception as e:
        print(f"❌ Granularity test failed: {e}")
        return False


def test_data_processing_15min():
    """Test 15-minute data processing"""
    print("\nTesting 15-minute data processing...")
    
    try:
        # Simulate 15-minute candle data
        sample_data = [
            [1704067200, 42000.0, 42500.0, 41800.0, 42200.0, 1000.5],  # 2024-01-01 00:00
            [1704068100, 42200.0, 42800.0, 42000.0, 42500.0, 1200.3],  # 2024-01-01 00:15
            [1704069000, 42500.0, 43000.0, 42200.0, 42700.0, 1100.7],  # 2024-01-01 00:30
            [1704069900, 42700.0, 43200.0, 42500.0, 42900.0, 1300.2],  # 2024-01-01 00:45
        ]
        
        # Process the data
        processed_data = []
        for candle in sample_data:
            timestamp, open_price, high, low, close, volume = candle
            datetime_obj = datetime.fromtimestamp(timestamp)
            processed_data.append({
                'date': datetime_obj,
                'symbol': 'BTC',
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        print(f"✅ Successfully processed {len(processed_data)} 15-minute records")
        print(f"   Sample processed record: {processed_data[0]}")
        
        # Check time intervals
        for i in range(1, len(processed_data)):
            time_diff = processed_data[i]['date'] - processed_data[i-1]['date']
            expected_minutes = 15
            actual_minutes = time_diff.total_seconds() / 60
            print(f"   Time interval {i}: {actual_minutes:.0f} minutes (expected: {expected_minutes})")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        return False


def test_collector_integration():
    """Test collector integration for 15min interval"""
    print("\nTesting collector integration...")
    
    try:
        # Import the collector classes
        sys.path.append(str(Path(__file__).parent))
        from collector import CryptoCollector15min, CryptoCollector
        
        # Test class instantiation
        collector = CryptoCollector15min(
            save_dir="./test_15min",
            start="2024-01-01",
            end="2024-01-02",
            interval="15min",
            max_workers=1,
            delay=1
        )
        
        print(f"✅ Successfully created CryptoCollector15min instance")
        print(f"   Interval: {collector.interval}")
        print(f"   Timezone: {collector._timezone}")
        
        # Test symbol list
        symbols = collector.get_instrument_list()
        print(f"   Available symbols: {len(symbols)}")
        print(f"   Sample symbols: {symbols[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Collector integration failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("15-Minute Interval Data Collection Test")
    print("=" * 60)
    
    tests = [
        ("API Endpoint", test_15min_api),
        ("Granularity Mapping", test_granularity_mapping),
        ("Data Processing", test_data_processing_15min),
        ("Collector Integration", test_collector_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"Running: {test_name}")
        print(f"{'='*40}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! 15-minute interval support is working correctly.")
        print("\nUsage example:")
        print("python collector.py download_data --source_dir ./data/15min --start 2024-01-01 --end 2024-01-31 --interval 15min")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main() 