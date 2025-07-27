import sys
import time
import datetime
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import signal
import atexit

import requests
import pandas as pd
from loguru import logger
from dateutil.tz import tzlocal

CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

# Simple retry decorator to avoid yahooquery dependency
def deco_retry(retry: int = 5, retry_sleep: int = 3):
    def deco_func(func):
        import functools
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _i in range(retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if _i == retry - 1:
                        raise e
                    logger.warning(f"{func.__name__} failed, retry {_i + 1}/{retry}: {e}")
                    time.sleep(retry_sleep)
            return None
        return wrapper
    return deco_func


class CoinbaseRealtimeCollector:
    """
    Real-time crypto data collector for Coinbase
    
    This class provides real-time OHLCV data collection from Coinbase API
    with configurable symbols and intervals.
    """
    
    # Supported intervals and their granularity in seconds
    INTERVALS = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '1d': 86400
    }
    
    def __init__(
        self,
        symbol: str,
        interval: str = '1m',
        save_dir: Optional[str] = None,
        callback: Optional[Callable] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize the real-time collector
        
        Parameters
        ----------
        symbol: str
            Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'ADA')
        interval: str
            Time interval ('1m', '5m', '15m', '30m', '1h', '1d')
        save_dir: str, optional
            Directory to save data files
        callback: callable, optional
            Callback function to handle new data
        max_retries: int
            Maximum number of retries for API calls
        timeout: int
            Request timeout in seconds
        """
        self.symbol = symbol.upper()
        self.interval = interval.lower()
        self.save_dir = Path(save_dir) if save_dir else None
        self.callback = callback
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Validate interval
        if self.interval not in self.INTERVALS:
            raise ValueError(f"Unsupported interval: {interval}. Supported intervals: {list(self.INTERVALS.keys())}")
        
        # Initialize data storage
        self.data_buffer = []
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Create save directory if specified
        if self.save_dir:
            self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.stop)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _fetch_candle_data(self, start_time: str, end_time: str) -> Optional[pd.DataFrame]:
        """
        Fetch candle data from Coinbase API
        
        Parameters
        ----------
        start_time: str
            Start time in ISO format
        end_time: str
            End time in ISO format
            
        Returns
        -------
        pd.DataFrame or None
            DataFrame with OHLCV data or None if error
        """
        for attempt in range(self.max_retries):
            try:
                # Coinbase API endpoint for candles
                url = f"https://api.exchange.coinbase.com/products/{self.symbol}-USD/candles"
                
                params = {
                    'start': start_time,
                    'end': end_time,
                    'granularity': self.INTERVALS[self.interval]
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                
                data = resp.json()
                
                if not data:
                    logger.warning(f"No data returned for {self.symbol}")
                    return None
                
                # Coinbase candle format: [timestamp, open, high, low, close, volume]
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Convert timestamp to datetime
                df['date'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Add symbol column
                df['symbol'] = self.symbol
                
                # Reorder columns
                df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
                
                return df.reset_index(drop=True)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Error fetching data for {self.symbol} after {self.max_retries} attempts: {e}")
                    return None
                else:
                    logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {self.symbol}: {e}")
                    time.sleep(3)  # Wait before retry
        
        return None
    
    def _get_interval_seconds(self) -> int:
        """Get interval duration in seconds"""
        return self.INTERVALS[self.interval]
    
    def _calculate_next_fetch_time(self) -> datetime.datetime:
        """Calculate the next fetch time based on interval"""
        now = datetime.datetime.now()
        interval_seconds = self._get_interval_seconds()
        
        # Round down to the nearest interval boundary
        timestamp = int(now.timestamp())
        rounded_timestamp = (timestamp // interval_seconds) * interval_seconds
        
        return datetime.datetime.fromtimestamp(rounded_timestamp + interval_seconds)
    
    def _fetch_latest_data(self) -> Optional[pd.DataFrame]:
        """Fetch the latest candle data"""
        try:
            # Calculate time range for the latest candle
            now = datetime.datetime.now()
            interval_seconds = self._get_interval_seconds()
            
            # Round down to the nearest interval boundary
            timestamp = int(now.timestamp())
            start_timestamp = (timestamp // interval_seconds) * interval_seconds
            
            start_time = datetime.datetime.fromtimestamp(start_timestamp).isoformat()
            end_time = now.isoformat()
            
            return self._fetch_candle_data(start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error fetching latest data: {e}")
            return None
    
    def _save_data(self, df: pd.DataFrame):
        """Save data to file if save_dir is specified"""
        if self.save_dir is None:
            return
        
        try:
            # Create filename with date
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            filename = f"{self.symbol}_{self.interval}_{today}.csv"
            filepath = self.save_dir / filename
            
            # Append to existing file or create new one
            if filepath.exists():
                df.to_csv(filepath, mode='a', header=False, index=False)
            else:
                df.to_csv(filepath, index=False)
                
            logger.debug(f"Data saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def _data_collection_loop(self):
        """Main data collection loop"""
        logger.info(f"Starting real-time data collection for {self.symbol} with {self.interval} interval")
        
        while self.is_running:
            try:
                # Calculate next fetch time
                next_fetch = self._calculate_next_fetch_time()
                now = datetime.datetime.now()
                
                # Wait until next fetch time
                wait_seconds = (next_fetch - now).total_seconds()
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                
                # Fetch latest data
                df = self._fetch_latest_data()
                
                if df is not None and not df.empty:
                    with self.lock:
                        self.data_buffer.append(df)
                        
                        # Keep only last 1000 records in memory
                        if len(self.data_buffer) > 1000:
                            self.data_buffer = self.data_buffer[-1000:]
                    
                    # Save data if directory is specified
                    self._save_data(df)
                    
                    # Call callback if provided
                    if self.callback:
                        try:
                            self.callback(df)
                        except Exception as e:
                            logger.error(f"Error in callback: {e}")
                    
                    # log ohlcv
                    latest = df.iloc[-1]
                    logger.debug(f"Fetched new data for {self.symbol}: "
                               f"O:{latest['open']:.4f} H:{latest['high']:.4f} "
                               f"L:{latest['low']:.4f} C:{latest['close']:.4f} V:{latest['volume']:.2f}")
                else:
                    logger.warning(f"No data received for {self.symbol}")
                
                # Small delay to prevent excessive API calls
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def start(self):
        """Start real-time data collection"""
        if self.is_running:
            logger.warning("Data collection is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started real-time data collection for {self.symbol}")
    
    def stop(self):
        """Stop real-time data collection"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info(f"Stopped real-time data collection for {self.symbol}")
    
    def get_latest_data(self) -> Optional[pd.DataFrame]:
        """Get the latest data point"""
        with self.lock:
            if self.data_buffer:
                return self.data_buffer[-1].copy()
        return None
    
    def get_recent_data(self, num_points: int = 100) -> pd.DataFrame:
        """Get recent data points"""
        with self.lock:
            if self.data_buffer:
                # Combine all data and get the last num_points
                all_data = pd.concat(self.data_buffer, ignore_index=True)
                return all_data.tail(num_points).copy()
        return pd.DataFrame()
    
    def get_all_data(self) -> pd.DataFrame:
        """Get all collected data"""
        with self.lock:
            if self.data_buffer:
                return pd.concat(self.data_buffer, ignore_index=True).copy()
        return pd.DataFrame()
    
    def clear_buffer(self):
        """Clear the data buffer"""
        with self.lock:
            self.data_buffer.clear()
        logger.info("Data buffer cleared")


def main():
    """Example usage of the real-time collector"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Coinbase Real-time Crypto Data Collector')
    parser.add_argument('symbol', help='Cryptocurrency symbol (e.g., BTC, ETH)')
    parser.add_argument('interval', help='Time interval (1m, 5m, 15m, 30m, 1h, 1d)')
    parser.add_argument('--save-dir', help='Directory to save data files')
    parser.add_argument('--callback', action='store_true', help='Enable callback logging')
    
    args = parser.parse_args()
    
    def data_callback(df):
        """Example callback function"""
        latest = df.iloc[-1]
        print(f"[{latest['date']}] {latest['symbol']}: "
              f"O:{latest['open']:.4f} H:{latest['high']:.4f} "
              f"L:{latest['low']:.4f} C:{latest['close']:.4f} V:{latest['volume']:.2f}")
    
    # Create collector
    collector = CoinbaseRealtimeCollector(
        symbol=args.symbol,
        interval=args.interval,
        save_dir=args.save_dir,
        callback=data_callback if args.callback else None
    )
    
    try:
        # Start collection
        collector.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    finally:
        collector.stop()


if __name__ == "__main__":
    main()
