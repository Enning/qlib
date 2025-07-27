# Coinbase API Migration Summary

## Overview

This document summarizes the migration from CoinGecko API to Coinbase Exchange API for the Qlib crypto data collector, including the new multi-timeframe support.

## Key Improvements

### 1. Complete OHLCV Data
- **Before**: Only prices, total_volumes, market_caps
- **After**: Full OHLCV (Open, High, Low, Close, Volume) data
- **Impact**: Enables proper backtesting and technical analysis

### 2. Multiple Timeframes
- **Before**: Only daily (1d) data
- **After**: 6 timeframes: 1min, 5min, 15min, 30min, 1hour, 1d
- **Impact**: Supports various trading strategies from high-frequency to long-term

### 3. Better Data Quality
- **Before**: CoinGecko free API with rate limits and data quality issues
- **After**: Direct Coinbase Exchange API with higher reliability
- **Impact**: More accurate and consistent data

### 4. Enhanced Features
- **Before**: Limited to major cryptocurrencies
- **After**: Access to 300+ USD trading pairs
- **Impact**: Broader market coverage

## Supported Time Intervals

The collector now supports the following time intervals:

| Interval | Granularity (seconds) | Records/Day | Use Case |
|----------|----------------------|-------------|----------|
| 1min     | 60                   | ~1440       | High-frequency trading |
| 5min     | 300                  | ~288        | Short-term analysis |
| 15min    | 900                  | ~96         | Intraday trading |
| 30min    | 1800                 | ~48         | Medium-term analysis |
| 1hour    | 3600                 | ~24         | Swing trading |
| 1d       | 86400                | 1           | Long-term analysis |

## Technical Changes

### API Integration
```python
# Old: CoinGecko API
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
data = cg.get_coin_market_chart_by_id(id=symbol, vs_currency="usd", days="max")

# New: Coinbase API with multiple granularities
url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles"
params = {
    'start': start_dt.isoformat(),
    'end': end_dt.isoformat(),
    'granularity': granularity  # 60, 300, 900, 1800, 3600, 86400
}
resp = requests.get(url, params=params, headers=headers)
```

### Data Structure
```python
# Old: Limited fields
{
    'date': date,
    'prices': price,
    'total_volumes': volume,
    'market_caps': market_cap
}

# New: Complete OHLCV with datetime support
{
    'date': datetime,  # Full datetime for intraday, date for daily
    'symbol': symbol,
    'open': open_price,
    'high': high_price,
    'low': low_price,
    'close': close_price,
    'volume': volume
}
```

### Timezone Handling
- **Before**: Asia/Shanghai timezone
- **After**: UTC timezone (Coinbase standard)
- **Impact**: Consistent with international standards

## Usage Examples

### Daily Data Collection
```bash
# Download daily data
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source/1d \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --delay 1 \
    --interval 1d

# Normalize data
python collector.py normalize_data \
    --source_dir ~/.qlib/crypto_data/source/1d \
    --normalize_dir ~/.qlib/crypto_data/source/1d_nor \
    --interval 1d
```

### 15-Minute Data Collection
```bash
# Download 15-minute data
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source/15min \
    --start 2024-01-01 \
    --end 2024-01-31 \
    --delay 1 \
    --interval 15min

# Normalize data
python collector.py normalize_data \
    --source_dir ~/.qlib/crypto_data/source/15min \
    --normalize_dir ~/.qlib/crypto_data/source/15min_nor \
    --interval 15min
```

### Other Intervals
```bash
# 1-minute data
python collector.py download_data --interval 1min --start 2024-01-01 --end 2024-01-02

# 5-minute data
python collector.py download_data --interval 5min --start 2024-01-01 --end 2024-01-07

# 30-minute data
python collector.py download_data --interval 30min --start 2024-01-01 --end 2024-01-15

# 1-hour data
python collector.py download_data --interval 1hour --start 2024-01-01 --end 2024-01-31
```

### Data Usage in Qlib
```python
import qlib
from qlib.data import D

# Initialize with daily data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data")
df = D.features(D.instruments(market="all"), 
                ["$open", "$high", "$low", "$close", "$volume"], 
                freq="day")

# Initialize with 15-minute data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data_15min")
df = D.features(D.instruments(market="all"), 
                ["$open", "$high", "$low", "$close", "$volume"], 
                freq="15min")

# Initialize with 1-hour data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data_1hour")
df = D.features(D.instruments(market="all"), 
                ["$open", "$high", "$low", "$close", "$volume"], 
                freq="1hour")
```

## API Rate Limits

### Coinbase Exchange API
- **Public endpoints**: 3 requests per second
- **Recommended delay**: 1 second between requests
- **Granularity options**: 60, 300, 900, 1800, 3600, 86400 seconds

### Best Practices
```python
# Use appropriate delays
delay = 1  # 1 second between requests

# Limit concurrent workers
max_workers = 1  # Recommended for API compliance

# Handle rate limiting
if resp.status_code == 429:
    time.sleep(60)  # Wait 1 minute before retry
```

## Supported Cryptocurrencies by Interval

### Daily Data (1d)
- All available USD trading pairs (300+ cryptocurrencies)

### Intraday Data (1min, 5min, 15min, 30min, 1hour)
- **1min**: 10 major cryptocurrencies (BTC, ETH, USDC, USDT, SOL, ADA, DOT, AVAX, MATIC, LINK)
- **5min**: 12 major cryptocurrencies (+ UNI, ATOM)
- **15min**: 14 major cryptocurrencies (+ LTC, BCH)
- **30min**: 15 major cryptocurrencies (+ XLM)
- **1hour**: 16 major cryptocurrencies (+ ETC)

The intraday data is limited to major cryptocurrencies to manage data volume and API limits effectively.

## Data Volume Considerations

When collecting intraday data, consider the following:

| Interval | Records/Day | Records/Month (30 days) | Records/Year |
|----------|-------------|-------------------------|--------------|
| 1min     | ~1440       | ~43,200                 | ~525,600     |
| 5min     | ~288        | ~8,640                  | ~105,120     |
| 15min    | ~96         | ~2,880                  | ~35,040      |
| 30min    | ~48         | ~1,440                  | ~17,520      |
| 1hour    | ~24         | ~720                    | ~8,760       |
| 1d       | 1           | 30                      | 365          |

**Example**: Collecting 1 month of 15min data for 14 symbols = ~40,320 records

## Testing

### Run Tests
```bash
# Basic API test
python simple_test.py

# 15-minute interval test
python test_15min.py

# Full functionality test
python test_coinbase_api.py

# Demo collection
python demo.py
python demo_15min.py
```

### Expected Output
```
============================================================
15-Minute Interval Data Collection Test
============================================================

API Endpoint: ✅ PASSED
Granularity Mapping: ✅ PASSED
Data Processing: ✅ PASSED
Collector Integration: ✅ PASSED

Overall: 4/4 tests passed

🎉 All tests passed! 15-minute interval support is working correctly.
```

## Migration Checklist

- [x] Replace CoinGecko API with Coinbase API
- [x] Update data structure to include OHLCV
- [x] Add support for multiple timeframes (1min, 5min, 15min, 30min, 1hour, 1d)
- [x] Update timezone handling to UTC
- [x] Implement proper error handling
- [x] Add rate limiting compliance
- [x] Create collector classes for each interval
- [x] Create normalize classes for each interval
- [x] Update documentation
- [x] Create test scripts
- [x] Create usage examples
- [x] Update requirements.txt

## Benefits Summary

1. **Complete Data**: Full OHLCV data enables proper backtesting
2. **Multiple Timeframes**: Support for 6 different intervals
3. **Better Reliability**: Direct API access with higher uptime
4. **Broader Coverage**: Access to 300+ cryptocurrencies
5. **Standards Compliance**: UTC timezone and proper rate limiting
6. **Future Proof**: Scalable architecture for additional features
7. **Flexible Usage**: Choose appropriate timeframe for your strategy

## Next Steps

1. **Deploy**: Use the new collector in production
2. **Monitor**: Track API usage and performance
3. **Optimize**: Fine-tune collection parameters based on usage
4. **Extend**: Add support for additional timeframes if needed
5. **Integrate**: Connect with Qlib backtesting framework

## Support

For issues or questions:
1. Check the test scripts for API connectivity
2. Review the demo scripts for usage examples
3. Consult the README.md for detailed instructions
4. Check Coinbase API documentation for rate limits and endpoints 