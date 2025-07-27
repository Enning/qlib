#!/usr/bin/env python3
"""
Test script for the Coinbase real-time crypto data collector

This script tests the basic functionality of the CoinbaseRealtimeCollector class.
"""

import time
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import datetime
from pathlib import Path

# Import the collector
from coinbase_realtime_data import CoinbaseRealtimeCollector


class TestCoinbaseRealtimeCollector(unittest.TestCase):
    """Test cases for CoinbaseRealtimeCollector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol = 'ETH'
        self.interval = '1m'
        self.collector = CoinbaseRealtimeCollector(
            symbol=self.symbol,
            interval=self.interval
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if self.collector.is_running:
            self.collector.stop()
    
    def test_initialization(self):
        """Test collector initialization"""
        self.assertEqual(self.collector.symbol, 'ETH')
        self.assertEqual(self.collector.interval, '1m')
        self.assertFalse(self.collector.is_running)
        self.assertEqual(len(self.collector.data_buffer), 0)
    
    def test_invalid_interval(self):
        """Test initialization with invalid interval"""
        with self.assertRaises(ValueError):
            CoinbaseRealtimeCollector('ETH', 'invalid_interval')
    
    def test_interval_seconds(self):
        """Test interval to seconds conversion"""
        self.assertEqual(self.collector._get_interval_seconds(), 60)
        
        # Test other intervals
        collector_5m = CoinbaseRealtimeCollector('ETH', '5m')
        self.assertEqual(collector_5m._get_interval_seconds(), 300)
        
        collector_1h = CoinbaseRealtimeCollector('ETH', '1h')
        self.assertEqual(collector_1h._get_interval_seconds(), 3600)
    
    def test_calculate_next_fetch_time(self):
        """Test next fetch time calculation"""
        next_fetch = self.collector._calculate_next_fetch_time()
        now = datetime.datetime.now()
        
        # Next fetch should be in the future
        self.assertGreater(next_fetch, now)
        
        # Should be aligned to interval boundaries
        interval_seconds = self.collector._get_interval_seconds()
        timestamp = int(next_fetch.timestamp())
        self.assertEqual(timestamp % interval_seconds, 0)
    
    @patch('requests.get')
    def test_fetch_candle_data_success(self, mock_get):
        """Test successful candle data fetching"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [1640995200, 46000.0, 46500.0, 45500.0, 46200.0, 100.5],  # timestamp, open, high, low, close, volume
            [1640995260, 46200.0, 46800.0, 46100.0, 46600.0, 150.2]
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test fetching data
        start_time = "2022-01-01T00:00:00"
        end_time = "2022-01-01T00:10:00"
        
        df = self.collector._fetch_candle_data(start_time, end_time)
        
        # Verify the result
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(df.iloc[0]['symbol'], 'ETH')
        self.assertEqual(df.iloc[0]['close'], 46200.0)
    
    @patch('requests.get')
    def test_fetch_candle_data_failure(self, mock_get):
        """Test candle data fetching failure"""
        # Mock failed API response
        mock_get.side_effect = Exception("API Error")
        
        start_time = "2022-01-01T00:00:00"
        end_time = "2022-01-01T00:10:00"
        
        df = self.collector._fetch_candle_data(start_time, end_time)
        
        # Should return None on failure
        self.assertIsNone(df)
    
    def test_data_buffer_operations(self):
        """Test data buffer operations"""
        # Create sample data
        sample_data = pd.DataFrame({
            'date': [datetime.datetime.now()],
            'symbol': ['ETH'],
            'open': [100.0],
            'high': [110.0],
            'low': [90.0],
            'close': [105.0],
            'volume': [1000.0]
        })
        
        # Test adding data to buffer
        with self.collector.lock:
            self.collector.data_buffer.append(sample_data)
        
        self.assertEqual(len(self.collector.data_buffer), 1)
        
        # Test getting latest data
        latest = self.collector.get_latest_data()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.iloc[0]['close'], 105.0)
        
        # Test getting all data
        all_data = self.collector.get_all_data()
        self.assertEqual(len(all_data), 1)
        
        # Test clearing buffer
        self.collector.clear_buffer()
        self.assertEqual(len(self.collector.data_buffer), 0)
    
    def test_buffer_size_limit(self):
        """Test that buffer size is limited"""
        # Add more than 1000 records to test buffer limit
        sample_data = pd.DataFrame({
            'date': [datetime.datetime.now()],
            'symbol': ['ETH'],
            'open': [100.0],
            'high': [110.0],
            'low': [90.0],
            'close': [105.0],
            'volume': [1000.0]
        })
        
        # Add 1100 records
        with self.collector.lock:
            for _ in range(1100):
                self.collector.data_buffer.append(sample_data)
        
        # Should be limited to 1000
        self.assertEqual(len(self.collector.data_buffer), 1000)
    
    def test_save_directory_creation(self):
        """Test save directory creation"""
        save_dir = Path('./test_save_dir')
        
        # Remove directory if it exists
        if save_dir.exists():
            import shutil
            shutil.rmtree(save_dir)
        
        # Create collector with save directory
        collector = CoinbaseRealtimeCollector(
            symbol='ETH',
            interval='1m',
            save_dir=str(save_dir)
        )
        
        # Directory should be created
        self.assertTrue(save_dir.exists())
        
        # Clean up
        import shutil
        shutil.rmtree(save_dir)
    
    def test_callback_function(self):
        """Test callback function execution"""
        callback_called = False
        callback_data = None
        
        def test_callback(df):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = df
        
        # Create collector with callback
        collector = CoinbaseRealtimeCollector(
            symbol='ETH',
            interval='1m',
            callback=test_callback
        )
        
        # Simulate data arrival
        sample_data = pd.DataFrame({
            'date': [datetime.datetime.now()],
            'symbol': ['ETH'],
            'open': [100.0],
            'high': [110.0],
            'low': [90.0],
            'close': [105.0],
            'volume': [1000.0]
        })
        
        # Call the callback manually
        collector.callback(sample_data)
        
        # Verify callback was called
        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_data)
        self.assertEqual(callback_data.iloc[0]['close'], 105.0)


def run_basic_functionality_test():
    """Run a basic functionality test with real API calls"""
    print("Running basic functionality test...")
    
    # Create collector
    collector = CoinbaseRealtimeCollector(
        symbol='ETH',
        interval='1m'
    )
    
    try:
        # Test fetching latest data
        print("Testing data fetching...")
        df = collector._fetch_latest_data()
        
        if df is not None and not df.empty:
            print(f"✓ Successfully fetched data for ETH")
            print(f"  Latest price: ${df.iloc[-1]['close']:.4f}")
            print(f"  Data points: {len(df)}")
            print(f"  Time range: {df['date'].min()} to {df['date'].max()}")
        else:
            print("✗ Failed to fetch data")
            return False
        
        # Test data structure
        expected_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        if list(df.columns) == expected_columns:
            print("✓ Data structure is correct")
        else:
            print(f"✗ Data structure mismatch. Expected: {expected_columns}, Got: {list(df.columns)}")
            return False
        
        # Test data types
        if df['close'].dtype in ['float64', 'float32']:
            print("✓ Price data types are correct")
        else:
            print(f"✗ Price data type mismatch. Expected float, Got: {df['close'].dtype}")
            return False
        
        print("✓ All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    finally:
        collector.stop()


if __name__ == "__main__":
    print("Coinbase Real-time Collector Tests")
    print("=" * 50)
    
    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run basic functionality test
    print("\n" + "=" * 50)
    success = run_basic_functionality_test()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!") 