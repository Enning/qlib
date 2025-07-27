#!/usr/bin/env python3
"""
Example usage of the Coinbase crypto data collector
"""

import sys
from pathlib import Path
import pandas as pd
from loguru import logger

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR))

from collector import Run


def example_daily_data_collection():
    """Example: Collect daily crypto data"""
    logger.info("Example: Collecting daily crypto data...")
    
    # Create Run instance for daily data
    runner = Run(
        source_dir="./example_data/daily/source",
        normalize_dir="./example_data/daily/normalize",
        max_workers=1,
        interval="1d"
    )
    
    # Download data for a short period
    runner.download_data(
        max_collector_count=1,
        delay=1,
        start="2024-01-01",
        end="2024-01-31",
        limit_nums=5  # Limit to 5 cryptocurrencies for testing
    )
    
    # Normalize the data
    runner.normalize_data(
        date_field_name="date",
        symbol_field_name="symbol"
    )
    
    logger.info("Daily data collection completed!")


def example_minute_data_collection():
    """Example: Collect minute-level crypto data"""
    logger.info("Example: Collecting minute-level crypto data...")
    
    # Create Run instance for minute data
    runner = Run(
        source_dir="./example_data/minute/source",
        normalize_dir="./example_data/minute/normalize",
        max_workers=1,
        interval="1min"
    )
    
    # Download data for a short period (minute data can be large)
    runner.download_data(
        max_collector_count=1,
        delay=1,
        start="2024-01-01",
        end="2024-01-02",  # Just one day for minute data
        limit_nums=3  # Limit to 3 major cryptocurrencies
    )
    
    # Normalize the data
    runner.normalize_data(
        date_field_name="date",
        symbol_field_name="symbol"
    )
    
    logger.info("Minute data collection completed!")


def example_custom_collection():
    """Example: Custom collection with specific parameters"""
    logger.info("Example: Custom collection...")
    
    # Create Run instance
    runner = Run(
        source_dir="./example_data/custom/source",
        normalize_dir="./example_data/custom/normalize",
        max_workers=1,
        interval="1d"
    )
    
    # Download data with custom parameters
    runner.download_data(
        max_collector_count=2,  # Retry failed symbols
        delay=2,  # Longer delay to be more conservative
        start="2023-01-01",
        end="2023-12-31",
        check_data_length=300,  # Ensure at least 300 days of data
        limit_nums=10  # Limit to 10 cryptocurrencies
    )
    
    # Normalize the data
    runner.normalize_data(
        date_field_name="date",
        symbol_field_name="symbol"
    )
    
    logger.info("Custom collection completed!")


def analyze_collected_data():
    """Example: Analyze the collected data"""
    logger.info("Example: Analyzing collected data...")
    
    # Read a sample CSV file
    sample_file = Path("./example_data/daily/source/BTC.csv")
    
    if sample_file.exists():
        df = pd.read_csv(sample_file)
        logger.info(f"Sample data shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Sample data:\n{df.head()}")
        
        # Basic statistics
        logger.info(f"Price statistics:")
        logger.info(f"  Open:  min={df['open'].min():.2f}, max={df['open'].max():.2f}, mean={df['open'].mean():.2f}")
        logger.info(f"  High:  min={df['high'].min():.2f}, max={df['high'].max():.2f}, mean={df['high'].mean():.2f}")
        logger.info(f"  Low:   min={df['low'].min():.2f}, max={df['low'].max():.2f}, mean={df['low'].mean():.2f}")
        logger.info(f"  Close: min={df['close'].min():.2f}, max={df['close'].max():.2f}, mean={df['close'].mean():.2f}")
        logger.info(f"  Volume: min={df['volume'].min():.2f}, max={df['volume'].max():.2f}, mean={df['volume'].mean():.2f}")
    else:
        logger.warning("No sample data file found. Run data collection first.")


def main():
    """Run examples"""
    logger.info("Starting Coinbase crypto data collector examples...")
    
    # Create directories
    for dir_path in [
        "./example_data/daily/source",
        "./example_data/daily/normalize",
        "./example_data/minute/source", 
        "./example_data/minute/normalize",
        "./example_data/custom/source",
        "./example_data/custom/normalize"
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    examples = [
        ("Daily Data Collection", example_daily_data_collection),
        ("Minute Data Collection", example_minute_data_collection),
        ("Custom Collection", example_custom_collection),
        ("Data Analysis", analyze_collected_data),
    ]
    
    for example_name, example_func in examples:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running example: {example_name}")
        logger.info(f"{'='*60}")
        
        try:
            example_func()
            logger.info(f"✅ {example_name} completed successfully")
        except Exception as e:
            logger.error(f"❌ {example_name} failed: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info("Examples completed!")
    logger.info("Check the ./example_data/ directory for collected data")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main() 