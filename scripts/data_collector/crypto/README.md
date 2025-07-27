# Collect Crypto Data

> *This data collector uses [Coinbase Exchange API](https://docs.cloud.coinbase.com/exchange/reference) to collect cryptocurrency data. The data includes complete OHLCV (Open, High, Low, Close, Volume) information and supports multiple timeframes.*

## Requirements

```bash
pip install -r requirement.txt
```

## Usage of the dataset
> *Crypto dataset now supports both Data retrieval and backtest functions with complete OHLCV data.*

## Supported Time Intervals

The collector now supports the following time intervals:

- **1min**: 1-minute data (major cryptocurrencies only)
- **5min**: 5-minute data (major cryptocurrencies only)
- **15min**: 15-minute data (major cryptocurrencies only)
- **30min**: 30-minute data (major cryptocurrencies only)
- **1hour**: 1-hour data (major cryptocurrencies only)
- **1d**: Daily data (all available cryptocurrencies)

## Collector Data

### Crypto Data

#### Daily Data (1d)

```bash

# download daily data from Coinbase API
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/1d --start 2015-01-01 --end 2021-11-30 --delay 1 --interval 1d

# normalize
python collector.py normalize_data --source_dir ~/.qlib/crypto_data/source/1d --normalize_dir ~/.qlib/crypto_data/source/1d_nor --interval 1d --date_field_name date

# dump data
cd qlib/scripts
python dump_bin.py dump_all --csv_path ~/.qlib/crypto_data/source/1d_nor --qlib_dir ~/.qlib/qlib_data/crypto_data --freq day --date_field_name date --include_fields open,high,low,close,volume
```

#### 15-Minute Data (15min)

```bash

# download 15-minute data from Coinbase API
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/15min --start 2024-01-01 --end 2024-01-31 --delay 1 --interval 15min

# normalize
python collector.py normalize_data --source_dir ~/.qlib/crypto_data/source/15min --normalize_dir ~/.qlib/crypto_data/source/15min_nor --interval 15min --date_field_name date

# dump data
cd qlib/scripts
python dump_bin.py dump_all --csv_path ~/.qlib/crypto_data/source/15min_nor --qlib_dir ~/.qlib/qlib_data/crypto_data_15min --freq 15min --date_field_name date --include_fields open,high,low,close,volume
```

#### 1-Hour Data (1hour)

```bash

# download 1-hour data from Coinbase API
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/1hour --start 2024-01-01 --end 2024-01-31 --delay 1 --interval 1hour

# normalize
python collector.py normalize_data --source_dir ~/.qlib/crypto_data/source/1hour --normalize_dir ~/.qlib/crypto_data/source/1hour_nor --interval 1hour --date_field_name date

# dump data
cd qlib/scripts
python dump_bin.py dump_all --csv_path ~/.qlib/crypto_data/source/1hour_nor --qlib_dir ~/.qlib/qlib_data/crypto_data_1hour --freq 1hour --date_field_name date --include_fields open,high,low,close,volume
```

#### Other Intervals

Similar commands can be used for other intervals (1min, 5min, 30min):

```bash
# 1-minute data
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/1min --start 2024-01-01 --end 2024-01-02 --delay 1 --interval 1min

# 5-minute data
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/5min --start 2024-01-01 --end 2024-01-07 --delay 1 --interval 5min

# 30-minute data
python collector.py download_data --source_dir ~/.qlib/crypto_data/source/30min --start 2024-01-01 --end 2024-01-15 --delay 1 --interval 30min
```

### using data

```python
import qlib
from qlib.data import D

# Initialize with daily data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data")
df = D.features(D.instruments(market="all"), ["$open", "$high", "$low", "$close", "$volume"], freq="day")

# Initialize with 15-minute data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data_15min")
df = D.features(D.instruments(market="all"), ["$open", "$high", "$low", "$close", "$volume"], freq="15min")

# Initialize with 1-hour data
qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data_1hour")
df = D.features(D.instruments(market="all"), ["$open", "$high", "$low", "$close", "$volume"], freq="1hour")
```

### Help
```bash
python collector.py --help
```

## Parameters

- interval: 1min, 5min, 15min, 30min, 1hour, or 1d
- delay: 1 (recommended to avoid rate limiting)
- timezone: UTC (Coinbase uses UTC)

## Data Features

The new Coinbase implementation provides:

- **Complete OHLCV data**: Open, High, Low, Close, Volume
- **Multiple timeframes**: 1min, 5min, 15min, 30min, 1hour, 1d
- **Major cryptocurrencies**: BTC, ETH, USDC, USDT, SOL, ADA, DOT, AVAX, MATIC, LINK, UNI, ATOM, LTC, BCH, XLM, ETC
- **High reliability**: Direct API access to Coinbase Exchange
- **Backtest support**: Full OHLCV data enables proper backtesting

## API Rate Limits

Coinbase Exchange API has the following rate limits:
- Public endpoints: 3 requests per second
- Recommended delay: 1 second between requests
- Granularity options: 60, 300, 900, 1800, 3600, 86400 seconds

## Supported Cryptocurrencies by Interval

### Daily Data (1d)
- All available USD trading pairs (300+ cryptocurrencies)

### Intraday Data (1min, 5min, 15min, 30min, 1hour)
- **1min**: 10 major cryptocurrencies
- **5min**: 12 major cryptocurrencies  
- **15min**: 14 major cryptocurrencies
- **30min**: 15 major cryptocurrencies
- **1hour**: 16 major cryptocurrencies

The intraday data is limited to major cryptocurrencies to manage data volume and API limits effectively.

## Data Volume Considerations

When collecting intraday data, consider the following:

- **1min data**: ~1440 records per day per symbol
- **5min data**: ~288 records per day per symbol
- **15min data**: ~96 records per day per symbol
- **30min data**: ~48 records per day per symbol
- **1hour data**: ~24 records per day per symbol
- **1d data**: 1 record per day per symbol

For example, collecting 1 month of 15min data for 14 symbols would result in approximately 40,320 records.
