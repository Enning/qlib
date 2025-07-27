import abc
import sys
import datetime
from abc import ABC
from pathlib import Path

import fire
import pandas as pd
from loguru import logger
from dateutil.tz import tzlocal

CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))
from data_collector.base import BaseCollector, BaseNormalize, BaseRun
from data_collector.utils import deco_retry

import requests
import time
from datetime import datetime as dt
from typing import Optional, Dict, Any


_CB_CRYPTO_SYMBOLS = None


def get_cb_crypto_symbols(qlib_data_path: [str, Path] = None) -> list:
    """get crypto symbols from Coinbase

    Returns
    -------
        crypto symbols available on Coinbase
    """
    global _CB_CRYPTO_SYMBOLS  # pylint: disable=W0603

    @deco_retry
    def _get_coinbase_products():
        try:
            # Coinbase API endpoint for products
            url = "https://api.exchange.coinbase.com/products"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            products = resp.json()
            
            # Filter for USD pairs and extract base currency
            usd_pairs = [product['base_currency'] for product in products 
                        if product['quote_currency'] == 'USD' and product['status'] == 'online']
            
            # Remove duplicates and sort
            _symbols = sorted(set(usd_pairs))
            
            if len(_symbols) < 10:
                raise ValueError("Too few symbols returned from Coinbase API")
                
            return _symbols
            
        except Exception as e:
            logger.warning(f"Coinbase API request error: {e}")
            raise ValueError("request error") from e

    if _CB_CRYPTO_SYMBOLS is None:
        _all_symbols = _get_coinbase_products()
        _CB_CRYPTO_SYMBOLS = sorted(set(_all_symbols))

    return _CB_CRYPTO_SYMBOLS


class CryptoCollector(BaseCollector):
    # Extended interval constants
    INTERVAL_1min = "1min"
    INTERVAL_5min = "5min"
    INTERVAL_15min = "15min"
    INTERVAL_30min = "30min"
    INTERVAL_1hour = "1hour"
    INTERVAL_1d = "1d"
    
    def __init__(
        self,
        save_dir: [str, Path],
        start=None,
        end=None,
        interval="1d",
        max_workers=1,
        max_collector_count=2,
        delay=1,  # delay need to be one
        check_data_length: int = None,
        limit_nums: int = None,
    ):
        """

        Parameters
        ----------
        save_dir: str
            crypto save dir
        max_workers: int
            workers, default 1
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 1
        interval: str
            freq, value from [1min, 5min, 15min, 30min, 1hour, 1d], default 1d
        start: str
            start datetime, default None
        end: str
            end datetime, default None
        check_data_length: int
            check data length, if not None and greater than 0, each symbol will be considered complete if its data length is greater than or equal to this value, otherwise it will be fetched again, the maximum number of fetches being (max_collector_count). By default None.
        limit_nums: int
            using for debug, by default None
        """
        super(CryptoCollector, self).__init__(
            save_dir=save_dir,
            start=start,
            end=end,
            interval=interval,
            max_workers=max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )

        self.init_datetime()

    def init_datetime(self):
        # Handle different intervals
        if self.interval in [self.INTERVAL_1min, self.INTERVAL_5min, self.INTERVAL_15min, 
                           self.INTERVAL_30min, self.INTERVAL_1hour]:
            # Convert both to pd.Timestamp for comparison
            default_start = pd.Timestamp(self.DEFAULT_START_DATETIME_1MIN)
            # Do not use max, because max will convert the type of start_datetime to datetime.date
            # self.start_datetime = max(self.start_datetime, default_start)
        elif self.interval == self.INTERVAL_1d:
            pass
        else:
            raise ValueError(f"interval error: {self.interval}")

        self.start_datetime = self.convert_datetime(self.start_datetime, self._timezone)
        self.end_datetime = self.convert_datetime(self.end_datetime, self._timezone)

    @staticmethod
    def convert_datetime(dt: [pd.Timestamp, datetime.date, str], timezone):
        try:
            dt = pd.Timestamp(dt, tz=timezone).timestamp()
            dt = pd.Timestamp(dt, tz=tzlocal(), unit="s")
        except ValueError as e:
            pass
        return dt

    @property
    @abc.abstractmethod
    def _timezone(self):
        raise NotImplementedError("rewrite get_timezone")

    @staticmethod
    def get_data_from_remote(symbol: str, interval: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """Get crypto data from Coinbase API
        
        Parameters
        ----------
        symbol: str
            Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        interval: str
            Time interval ('1min', '5min', '15min', '30min', '1hour', '1d')
        start: str
            Start date in YYYY-MM-DD format
        end: str
            End date in YYYY-MM-DD format
            
        Returns
        -------
        pd.DataFrame or None
            DataFrame with OHLCV data or None if error
        """
        error_msg = f"{symbol}-{interval}-{start}-{end}"
        
        try:
            # Convert dates to UTC ISO format for Coinbase API
            start_dt = pd.to_datetime(start).tz_localize(None).tz_localize('UTC')
            end_dt = pd.to_datetime(end).tz_localize(None).tz_localize('UTC')
            
            # Extended Coinbase API granularity mapping
            granularity_map = {
                "1min": 60,
                "5min": 300,
                "15min": 900,
                "30min": 1800,
                "1hour": 3600,
                "1d": 86400
            }
            
            if interval not in granularity_map:
                raise ValueError(f"Unsupported interval: {interval}. Supported intervals: {list(granularity_map.keys())}")
            
            granularity = granularity_map[interval]
            
            # Calculate chunk size based on granularity to stay under 300 data points limit
            # Coinbase API has a limit of 300 data points per request
            max_points = 300
            chunk_duration_map = {
                "1min": pd.Timedelta(hours=5),      # 300 minutes
                "5min": pd.Timedelta(hours=25),     # 300 * 5 minutes
                "15min": pd.Timedelta(hours=75),    # 300 * 15 minutes
                "30min": pd.Timedelta(hours=150),   # 300 * 30 minutes
                "1hour": pd.Timedelta(hours=300),   # 300 hours
                "1d": pd.Timedelta(days=300)        # 300 days
            }
            
            chunk_duration = chunk_duration_map[interval]
            
            # Collect data in chunks
            all_data = []
            current_start = start_dt
            
            while current_start < end_dt:
                current_end = min(current_start + chunk_duration, end_dt)
                
                # Coinbase API endpoint for candles
                url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles"
                
                params = {
                    'start': current_start.isoformat(),
                    'end': current_end.isoformat(),
                    'granularity': granularity
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                resp = requests.get(url, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                
                chunk_data = resp.json()
                
                if chunk_data:
                    all_data.extend(chunk_data)
                
                current_start = current_end
            
            if not all_data:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Coinbase candle format: [timestamp, open, high, low, close, volume]
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # For intraday intervals, keep full datetime
            if interval in ["1min", "5min", "15min", "30min", "1hour"]:
                # Ensure we have datetime objects for intraday intervals
                df['date'] = pd.to_datetime(df['date'])
            else:
                # For daily intervals, convert to date objects
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Filter by date range - ensure consistent datetime types
            if not df.empty:
                if interval in ["1min", "5min", "15min", "30min", "1hour"]:
                    # For intraday intervals, compare datetime with datetime
                    start_dt = pd.to_datetime(start).tz_localize(None)
                    end_dt = pd.to_datetime(end).tz_localize(None)
                    # Convert DataFrame dates to list for comparison
                    date_list = df['date'].tolist()
                    mask = [(d >= start_dt) and (d < end_dt) for d in date_list]
                    df = df[mask]
                else:
                    # For daily intervals, compare date with date
                    start_dt = pd.to_datetime(start).date()
                    end_dt = pd.to_datetime(end).date()
                    df = df[
                        (df['date'] >= start_dt) & 
                        (df['date'] < end_dt)
                    ]
            
            if df.empty:
                logger.warning(f"No data in date range for {symbol}")
                return None
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Reorder columns
            df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            logger.warning(f"{error_msg}: {e}")
            logger.warning(f"DataFrame info: shape={df.shape if 'df' in locals() else 'N/A'}, columns={df.columns.tolist() if 'df' in locals() and not df.empty else 'N/A'}")
            return None

    def get_data(
        self, symbol: str, interval: str, start_datetime: pd.Timestamp, end_datetime: pd.Timestamp
    ) -> Optional[pd.DataFrame]:
        def _get_simple(start_, end_):
            self.sleep()
            _remote_interval = interval
            return self.get_data_from_remote(
                symbol,
                interval=_remote_interval,
                start=start_,
                end=end_,
            )

        # Support all intervals
        supported_intervals = [self.INTERVAL_1min, self.INTERVAL_5min, self.INTERVAL_15min, 
                             self.INTERVAL_30min, self.INTERVAL_1hour, self.INTERVAL_1d]
        
        if interval in supported_intervals:
            _result = _get_simple(start_datetime, end_datetime)
        else:
            raise ValueError(f"cannot support {interval}. Supported intervals: {supported_intervals}")
        return _result


class CryptoCollector1d(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols......")
        symbols = get_cb_crypto_symbols()
        logger.info(f"get {len(symbols)} symbols.")
        return symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"  # Coinbase uses UTC


class CryptoCollector1min(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols for 1min data......")
        symbols = get_cb_crypto_symbols()
        # For 1min data, we might want to limit to major cryptocurrencies
        major_symbols = ['BTC', 'ETH', 'USDC', 'USDT', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK']
        available_symbols = [s for s in major_symbols if s in symbols]
        logger.info(f"get {len(available_symbols)} major symbols for 1min data.")
        return available_symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"  # Coinbase uses UTC


class CryptoCollector5min(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols for 5min data......")
        symbols = get_cb_crypto_symbols()
        # For 5min data, limit to major cryptocurrencies
        major_symbols = ['BTC', 'ETH', 'USDC', 'USDT', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM']
        available_symbols = [s for s in major_symbols if s in symbols]
        logger.info(f"get {len(available_symbols)} major symbols for 5min data.")
        return available_symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"


class CryptoCollector15min(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols for 15min data......")
        symbols = get_cb_crypto_symbols()
        # For 15min data, limit to major cryptocurrencies
        major_symbols = ['BTC', 'ETH', 'USDC', 'USDT', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH']
        available_symbols = [s for s in major_symbols if s in symbols]
        logger.info(f"get {len(available_symbols)} major symbols for 15min data.")
        return available_symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"


class CryptoCollector30min(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols for 30min data......")
        symbols = get_cb_crypto_symbols()
        # For 30min data, limit to major cryptocurrencies
        major_symbols = ['BTC', 'ETH', 'USDC', 'USDT', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM']
        available_symbols = [s for s in major_symbols if s in symbols]
        logger.info(f"get {len(available_symbols)} major symbols for 30min data.")
        return available_symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"


class CryptoCollector1hour(CryptoCollector, ABC):
    def get_instrument_list(self):
        logger.info("get Coinbase crypto symbols for 1hour data......")
        symbols = get_cb_crypto_symbols()
        # For 1hour data, limit to major cryptocurrencies
        major_symbols = ['BTC', 'ETH', 'USDC', 'USDT', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'ETC']
        available_symbols = [s for s in major_symbols if s in symbols]
        logger.info(f"get {len(available_symbols)} major symbols for 1hour data.")
        return available_symbols

    def normalize_symbol(self, symbol):
        return symbol

    @property
    def _timezone(self):
        return "UTC"


class CryptoNormalize(BaseNormalize):
    DAILY_FORMAT = "%Y-%m-%d"

    @staticmethod
    def normalize_crypto(
        df: pd.DataFrame,
        calendar_list: list = None,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
    ):
        if df.empty:
            return df
        df = df.copy()
        df.set_index(date_field_name, inplace=True)
        df.index = pd.to_datetime(df.index)
        df = df[~df.index.duplicated(keep="first")]
        if calendar_list is not None:
            df = df.reindex(
                pd.DataFrame(index=calendar_list)
                .loc[
                    pd.Timestamp(df.index.min()).date() : pd.Timestamp(df.index.max()).date()
                    + pd.Timedelta(hours=23, minutes=59)
                ]
                .index
            )
        df.sort_index(inplace=True)

        df.index.names = [date_field_name]
        return df.reset_index()

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.normalize_crypto(df, self._calendar_list, self._date_field_name, self._symbol_field_name)
        return df


class CryptoNormalize1d(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class CryptoNormalize1min(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class CryptoNormalize5min(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class CryptoNormalize15min(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class CryptoNormalize30min(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class CryptoNormalize1hour(CryptoNormalize):
    def _get_calendar_list(self):
        return None


class Run(BaseRun):
    def __init__(self, source_dir=None, normalize_dir=None, max_workers=1, interval="1d"):
        """

        Parameters
        ----------
        source_dir: str
            The directory where the raw data collected from the Internet is saved, default "Path(__file__).parent/source"
        normalize_dir: str
            Directory for normalize data, default "Path(__file__).parent/normalize"
        max_workers: int
            Concurrent number, default is 1
        interval: str
            freq, value from [1min, 5min, 15min, 30min, 1hour, 1d], default 1d
        """
        super().__init__(source_dir, normalize_dir, max_workers, interval)

    @property
    def collector_class_name(self):
        return f"CryptoCollector{self.interval}"

    @property
    def normalize_class_name(self):
        return f"CryptoNormalize{self.interval}"

    @property
    def default_base_dir(self) -> [Path, str]:
        return CUR_DIR

    def download_data(
        self,
        max_collector_count=2,
        delay=1,
        start=None,
        end=None,
        check_data_length: int = None,
        limit_nums=None,
    ):
        """download data from Coinbase

        Parameters
        ----------
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 1
        interval: str
            freq, value from [1min, 5min, 15min, 30min, 1hour, 1d], default 1d
        start: str
            start datetime, default "2000-01-01"
        end: str
            end datetime, default ``pd.Timestamp(datetime.datetime.now() + pd.Timedelta(days=1))``
        check_data_length: int
            check data length, if not None and greater than 0, each symbol will be considered complete if its data length is greater than or equal to this value, otherwise it will be fetched again, the maximum number of fetches being (max_collector_count). By default None.
        limit_nums: int
            using for debug, by default None

        Examples
        ---------
            # get daily data
            $ python collector.py download_data --source_dir ~/.qlib/crypto_data/source/1d --start 2015-01-01 --end 2021-11-30 --delay 1 --interval 1d
            
            # get 15min data
            $ python collector.py download_data --source_dir ~/.qlib/crypto_data/source/15min --start 2024-01-01 --end 2024-01-31 --delay 1 --interval 15min
            
            # get 1hour data
            $ python collector.py download_data --source_dir ~/.qlib/crypto_data/source/1hour --start 2024-01-01 --end 2024-01-31 --delay 1 --interval 1hour
        """

        super(Run, self).download_data(max_collector_count, delay, start, end, check_data_length, limit_nums)

    def normalize_data(self, date_field_name: str = "date", symbol_field_name: str = "symbol"):
        """normalize data

        Parameters
        ----------
        date_field_name: str
            date field name, default date
        symbol_field_name: str
            symbol field name, default symbol

        Examples
        ---------
            $ python collector.py normalize_data --source_dir ~/.qlib/crypto_data/source/1d --normalize_dir ~/.qlib/crypto_data/source/1d_nor --interval 1d --date_field_name date
        """
        super(Run, self).normalize_data(date_field_name, symbol_field_name)


if __name__ == "__main__":
    fire.Fire(Run)
