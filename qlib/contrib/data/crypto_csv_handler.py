# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pandas as pd
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.dataset.loader import StaticDataLoader


class CryptoCSVHandler(DataHandlerLP):
    """
    A data handler for crypto CSV files.
    
    This handler loads crypto data from CSV files and converts them to the format
    expected by Qlib's DataHandlerLP.
    """
    
    def __init__(self, csv_path, **kwargs):
        """
        Initialize the crypto CSV handler.
        
        Parameters
        ----------
        csv_path : str
            Path to the CSV file containing crypto data
        **kwargs : dict
            Additional arguments passed to DataHandlerLP
        """
        # Load the CSV file
        df = pd.read_csv(csv_path, parse_dates=["datetime"])
        
        # Ensure the datetime column is properly formatted
        df["datetime"] = pd.to_datetime(df["datetime"])
        
        # Add instrument column (using filename as instrument name)
        instrument_name = "ETHUSD"  # Default, can be customized
        df["instrument"] = instrument_name
        
        # Set multi-index with datetime and instrument
        df = df.set_index(["datetime", "instrument"])
        
        # Sort by datetime
        df = df.sort_index()
        
        # Create features from OHLCV data
        df = self._create_features(df)
        
        # Create labels (next period return)
        df = self._create_labels(df)
        
        # Organize columns into MultiIndex: ('feature', ...) and ('label', ...)
        feature_cols = [col for col in df.columns if col.startswith('$')]
        label_cols = [col for col in df.columns if col.startswith('LABEL')]
        df = df[feature_cols + label_cols]
        df.columns = pd.MultiIndex.from_tuples(
            [('feature', col) if col in feature_cols else ('label', col) for col in df.columns]
        )
        
        # Create a static data loader with the processed DataFrame
        data_loader = StaticDataLoader(df)
        
        # Initialize the parent class
        super().__init__(data_loader=data_loader, **kwargs)
    
    def _create_features(self, df):
        """Create features from OHLCV data"""
        # Basic price features
        df['$close'] = df['close']
        df['$open'] = df['open']
        df['$high'] = df['high']
        df['$low'] = df['low']
        df['$volume'] = df['volume']
        
        # Price changes
        df['$close_1'] = df['$close'].shift(1)
        df['$open_1'] = df['$open'].shift(1)
        df['$high_1'] = df['$high'].shift(1)
        df['$low_1'] = df['$low'].shift(1)
        
        # Returns
        df['$close_ret_1'] = df['$close'] / df['$close_1'] - 1
        df['$open_ret_1'] = df['$open'] / df['$open_1'] - 1
        
        # Price ranges
        df['$high_low_ratio'] = df['$high'] / df['$low']
        df['$close_open_ratio'] = df['$close'] / df['$open']
        
        # Volume features
        df['$volume_1'] = df['$volume'].shift(1)
        df['$volume_ratio'] = df['$volume'] / df['$volume_1']
        
        # Moving averages
        df['$close_ma_5'] = df['$close'].rolling(5).mean()
        df['$close_ma_10'] = df['$close'].rolling(10).mean()
        df['$volume_ma_5'] = df['$volume'].rolling(5).mean()
        
        # Volatility
        df['$close_std_5'] = df['$close'].rolling(5).std()
        df['$close_std_10'] = df['$close'].rolling(10).std()
        
        # Drop NaN values
        df = df.dropna()
        
        return df
    
    def _create_labels(self, df):
        """Create labels (next period return)"""
        # Create label column - next period return
        df['LABEL0'] = df['$close'].shift(-1) / df['$close'] - 1
        
        # Drop the last row since we don't have next period data
        df = df.dropna()
        
        return df 