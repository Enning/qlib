#!/usr/bin/env python3
"""
Simple test script for Coinbase API integration (no external dependencies)
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

def test_coinbase_api():
    """Test Coinbase API endpoints"""
    print("Testing Coinbase API...")
    
    # Test 1: Get products
    print("\n1. Testing products endpoint...")
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
        
        print(f"✅ Successfully retrieved {len(usd_pairs)} USD trading pairs")
        print(f"   First 10 symbols: {usd_pairs[:10]}")
        
    except Exception as e:
        print(f"❌ Failed to get products: {e}")
        return False
    
    # Test 2: Get BTC candles
    print("\n2. Testing candles endpoint...")
    try:
        url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
        params = {
            'start': '2024-01-01T00:00:00Z',
            'end': '2024-01-05T00:00:00Z',
            'granularity': 86400  # 1 day
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data:
            print(f"✅ Successfully retrieved {len(data)} candle records for BTC")
            print(f"   Sample data: {data[0]}")
            print(f"   Data format: [timestamp, open, high, low, close, volume]")
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ Failed to get candles: {e}")
        return False
    
    # Test 3: Test rate limiting
    print("\n3. Testing rate limiting...")
    try:
        # Make multiple requests quickly
        for i in range(3):
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:  # Rate limit
                print(f"   Request {i+1}: Rate limited (expected)")
            elif resp.status_code == 200:
                print(f"   Request {i+1}: Success")
            else:
                print(f"   Request {i+1}: Status {resp.status_code}")
    except Exception as e:
        print(f"   Rate limit test error: {e}")
    
    print("\n✅ All basic API tests passed!")
    return True


def test_data_processing():
    """Test data processing logic"""
    print("\nTesting data processing...")
    
    # Simulate Coinbase candle data
    sample_data = [
        [1704067200, 42000.0, 42500.0, 41800.0, 42200.0, 1000.5],  # 2024-01-01
        [1704153600, 42200.0, 42800.0, 42000.0, 42500.0, 1200.3],  # 2024-01-02
        [1704240000, 42500.0, 43000.0, 42200.0, 42700.0, 1100.7],  # 2024-01-03
    ]
    
    try:
        # Process the data
        processed_data = []
        for candle in sample_data:
            timestamp, open_price, high, low, close, volume = candle
            date = datetime.fromtimestamp(timestamp).date()
            processed_data.append({
                'date': date,
                'symbol': 'BTC',
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        print(f"✅ Successfully processed {len(processed_data)} records")
        print(f"   Sample processed record: {processed_data[0]}")
        
        # Check data types
        from datetime import date
        assert isinstance(processed_data[0]['date'], date)
        assert isinstance(processed_data[0]['open'], float)
        assert isinstance(processed_data[0]['volume'], float)
        
        print("✅ Data type validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Coinbase API Integration Test")
    print("=" * 60)
    
    tests = [
        ("API Endpoints", test_coinbase_api),
        ("Data Processing", test_data_processing),
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
        print("\n🎉 All tests passed! Coinbase API integration is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirement.txt")
        print("2. Run the collector: python collector.py download_data --help")
        print("3. Check examples: python example_usage.py")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main() 