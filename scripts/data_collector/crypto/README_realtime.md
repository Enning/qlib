# Coinbase Real-time Crypto Data Collector

This module provides real-time cryptocurrency OHLCV data collection from Coinbase API. It allows you to continuously fetch and monitor cryptocurrency prices with configurable intervals.

## Features

- **Real-time data collection**: Continuously fetch OHLCV data from Coinbase API
- **Multiple intervals**: Support for 1m, 5m, 15m, 30m, 1h, and 1d intervals
- **Multiple symbols**: Collect data for any cryptocurrency available on Coinbase
- **Data persistence**: Optional file saving with automatic CSV generation
- **Callback support**: Custom callback functions for real-time data processing
- **Thread-safe**: Thread-safe data buffer with automatic memory management
- **Graceful shutdown**: Proper signal handling and cleanup

## Installation

The collector uses the same dependencies as the existing crypto collector:

```bash
pip install -r requirement.txt
```

## Quick Start

### Basic Usage

```python
from coinbase_realtime_data import CoinbaseRealtimeCollector

# Create a collector for ETH with 1-minute intervals
collector = CoinbaseRealtimeCollector(
    symbol='ETH',
    interval='1m'
)

# Start collecting data
collector.start()

# Wait for some data
import time
time.sleep(60)  # Collect for 1 minute

# Get the latest data
latest_data = collector.get_latest_data()
print(f"Latest ETH price: ${latest_data.iloc[-1]['close']:.4f}")

# Stop collecting
collector.stop()
```

### Command Line Usage

```bash
# Basic usage
python coinbase_realtime_data.py ETH 1m

# With data saving
python coinbase_realtime_data.py BTC 5m --save-dir ./data

# With callback logging
python coinbase_realtime_data.py ADA 1m --callback
```

## API Reference

### CoinbaseRealtimeCollector

#### Constructor

```python
CoinbaseRealtimeCollector(
    symbol: str,
    interval: str = '1m',
    save_dir: Optional[str] = None,
    callback: Optional[Callable] = None,
    max_retries: int = 3,
    timeout: int = 30
)
```

**Parameters:**
- `symbol` (str): Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'ADA')
- `interval` (str): Time interval ('1m', '5m', '15m', '30m', '1h', '1d')
- `save_dir` (str, optional): Directory to save data files
- `callback` (callable, optional): Function called when new data arrives
- `max_retries` (int): Maximum number of retries for API calls
- `timeout` (int): Request timeout in seconds

#### Methods

##### `start()`
Start real-time data collection in a background thread.

##### `stop()`
Stop data collection and clean up resources.

##### `get_latest_data() -> Optional[pd.DataFrame]`
Get the most recent data point.

##### `get_recent_data(num_points: int = 100) -> pd.DataFrame`
Get the last N data points.

##### `get_all_data() -> pd.DataFrame`
Get all collected data.

##### `clear_buffer()`
Clear the data buffer.

## Examples

### Example 1: Single Symbol Collection

```python
from coinbase_realtime_data import CoinbaseRealtimeCollector
import time

def print_price(df):
    latest = df.iloc[-1]
    print(f"{latest['symbol']}: ${latest['close']:.4f}")

# Create collector
collector = CoinbaseRealtimeCollector(
    symbol='ETH',
    interval='1m',
    callback=print_price
)

# Start collection
collector.start()

# Run for 5 minutes
time.sleep(300)

# Get all collected data
all_data = collector.get_all_data()
print(f"Collected {len(all_data)} data points")

collector.stop()
```

### Example 2: Multiple Symbols

```python
from coinbase_realtime_data import CoinbaseRealtimeCollector
import time

# Create collectors for multiple symbols
collectors = {
    'BTC': CoinbaseRealtimeCollector('BTC', '5m'),
    'ETH': CoinbaseRealtimeCollector('ETH', '5m'),
    'ADA': CoinbaseRealtimeCollector('ADA', '5m')
}

# Start all collectors
for symbol, collector in collectors.items():
    collector.start()
    print(f"Started collection for {symbol}")

# Collect data for 10 minutes
time.sleep(600)

# Get latest prices
for symbol, collector in collectors.items():
    latest = collector.get_latest_data()
    if latest is not None:
        price = latest.iloc[-1]['close']
        print(f"{symbol}: ${price:.4f}")

# Stop all collectors
for collector in collectors.values():
    collector.stop()
```

### Example 3: Data Analysis

```python
from coinbase_realtime_data import CoinbaseRealtimeCollector
import time
import pandas as pd

collector = CoinbaseRealtimeCollector('BTC', '1m')

collector.start()
time.sleep(300)  # Collect for 5 minutes

# Perform analysis
data = collector.get_all_data()
if not data.empty:
    print(f"Data Analysis for BTC:")
    print(f"Total data points: {len(data)}")
    print(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
    print(f"Average volume: {data['volume'].mean():.2f}")
    print(f"Price volatility: {data['close'].std():.2f}")
    
    # Calculate price change
    first_price = data.iloc[0]['close']
    last_price = data.iloc[-1]['close']
    change_pct = ((last_price - first_price) / first_price) * 100
    print(f"Price change: {change_pct:+.2f}%")

collector.stop()
```

### Example 4: Save Data to Files

```python
from coinbase_realtime_data import CoinbaseRealtimeCollector
import time
from pathlib import Path

# Create save directory
save_dir = Path('./crypto_data')
save_dir.mkdir(exist_ok=True)

# Create collector with file saving
collector = CoinbaseRealtimeCollector(
    symbol='ETH',
    interval='1m',
    save_dir=str(save_dir)
)

collector.start()
time.sleep(3600)  # Collect for 1 hour

# Check saved files
saved_files = list(save_dir.glob('*.csv'))
print(f"Saved {len(saved_files)} files:")
for file in saved_files:
    print(f"  - {file.name}")

collector.stop()
```

## Data Format

The collector returns pandas DataFrames with the following columns:

- `date`: Timestamp of the data point
- `symbol`: Cryptocurrency symbol
- `open`: Opening price
- `high`: Highest price during the interval
- `low`: Lowest price during the interval
- `close`: Closing price
- `volume`: Trading volume

## Supported Intervals

| Interval | Description | Granularity (seconds) |
|----------|-------------|----------------------|
| 1m       | 1 minute    | 60                   |
| 5m       | 5 minutes   | 300                  |
| 15m      | 15 minutes  | 900                  |
| 30m      | 30 minutes  | 1800                 |
| 1h       | 1 hour      | 3600                 |
| 1d       | 1 day       | 86400                |

## Error Handling

The collector includes robust error handling:

- **API failures**: Automatic retries with exponential backoff
- **Network issues**: Graceful handling of connection problems
- **Rate limiting**: Built-in delays to respect API limits
- **Data validation**: Checks for valid data before processing

## Performance Considerations

- **Memory management**: Data buffer is limited to 1000 records by default
- **API rate limits**: Built-in delays prevent excessive API calls
- **Thread safety**: All data operations are thread-safe
- **Resource cleanup**: Automatic cleanup on shutdown

## Troubleshooting

### Common Issues

1. **No data received**: Check if the symbol is available on Coinbase
2. **API errors**: Verify internet connection and Coinbase API status
3. **Memory issues**: Reduce buffer size or clear buffer periodically
4. **File permission errors**: Ensure write permissions for save directory

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

Run the test suite to verify functionality:

```bash
python test_realtime_collector.py
```

## License

This module is part of the qlib project and follows the same license terms. 