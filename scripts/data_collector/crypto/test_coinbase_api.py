#!/usr/bin/env python3
"""
Test script for Coinbase API integration
"""

import sys
from pathlib import Path
import pandas as pd
from loguru import logger

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR))

from collector import get_cb_crypto_symbols, CryptoCollector1d


def test_get_symbols():
    """Test getting cryptocurrency symbols from Coinbase"""
    logger.info("Testing symbol retrieval...")
    try:
        symbols = get_cb_crypto_symbols()
        logger.info(f"Successfully retrieved {len(symbols)} symbols")
        logger.info(f"First 10 symbols: {symbols[:10]}")
        return True
    except Exception as e:
        logger.error(f"Failed to get symbols: {e}")
        return False


def test_get_data():
    """Test getting data for a specific cryptocurrency"""
    logger.info("Testing data retrieval...")
    try:
        # Create a test collector
        collector = CryptoCollector1d(
            save_dir="./test_data",
            start="2024-01-01",
            end="2024-01-10",
            interval="1d",
            max_workers=1,
            delay=1
        )
        
        # Test getting data for BTC
        df = collector.get_data("BTC", "1d", 
                               pd.Timestamp("2024-01-01"), 
                               pd.Timestamp("2024-01-10"))
        
        if df is not None and not df.empty:
            logger.info(f"Successfully retrieved data for BTC")
            logger.info(f"Data shape: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"First few rows:\n{df.head()}")
            return True
        else:
            logger.error("No data retrieved")
            return False
            
    except Exception as e:
        logger.error(f"Failed to get data: {e}")
        return False


def test_remote_data():
    """Test the remote data fetching function directly"""
    logger.info("Testing remote data fetching...")
    try:
        from collector import CryptoCollector
        
        # Test getting BTC data for a short period
        df = CryptoCollector.get_data_from_remote(
            symbol="BTC",
            interval="1d",
            start="2024-01-01",
            end="2024-01-05"
        )
        
        if df is not None and not df.empty:
            logger.info(f"Successfully retrieved remote data for BTC")
            logger.info(f"Data shape: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            return True
        else:
            logger.error("No remote data retrieved")
            return False
            
    except Exception as e:
        logger.error(f"Failed to get remote data: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting Coinbase API tests...")
    
    tests = [
        ("Symbol Retrieval", test_get_symbols),
        ("Remote Data Fetching", test_remote_data),
        ("Data Retrieval", test_get_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Coinbase API integration is working correctly.")
    else:
        logger.error("⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main() 