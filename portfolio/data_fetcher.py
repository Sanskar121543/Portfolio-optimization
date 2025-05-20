import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class DataFetcher:
    def __init__(self):
        self.cache = {}
        self.logger = logging.getLogger(__name__)
    
    def get_historical_data(self, symbols, time_period='1y'):
        """
        Fetch historical stock data for the given symbols
        
        Args:
            symbols (list): List of stock symbols
            time_period (str): Time period for historical data (e.g., '1y', '5y')
            
        Returns:
            dict: Dictionary containing stock data and metadata
        """
        try:
            # Convert symbols to list if string
            if isinstance(symbols, str):
                symbols = [s.strip() for s in symbols.split(',')]
            
            if not symbols:
                return {
                    'status': 'error',
                    'message': 'No symbols provided'
                }
            
            # Calculate start date based on time period
            end_date = datetime.now()
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            if time_period == '1y':
                start_date = end_date - timedelta(days=365)
            elif time_period == '5y':
                start_date = end_date - timedelta(days=5*365)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year
            
            self.logger.info(f"Fetching data from {start_date} to {end_date} for symbols: {symbols}")
            
            # Fetch data for all symbols
            data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    if hist.empty:
                        self.logger.warning(f"No data found for symbol {symbol}")
                        continue
                        
                    if len(hist) < 30:  # Require at least 30 days of data
                        self.logger.warning(f"Insufficient data for symbol {symbol}")
                        continue
                    
                    # Calculate daily returns
                    returns = hist['Close'].pct_change().dropna()
                    
                    if len(returns) < 30:  # Require at least 30 days of returns
                        self.logger.warning(f"Insufficient returns data for symbol {symbol}")
                        continue
                    
                    data[symbol] = {
                        'returns': returns.tolist(),
                        'dates': returns.index.strftime('%Y-%m-%d').tolist(),
                        'mean_return': float(returns.mean()),
                        'volatility': float(returns.std() * np.sqrt(252)),  # Annualized volatility
                        'last_price': float(hist['Close'].iloc[-1])
                    }
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    continue
            
            if not data:
                return {
                    'status': 'error',
                    'message': 'No valid data found for any of the provided symbols'
                }
            
            return {
                'status': 'success',
                'data': data,
                'metadata': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'symbols': symbols
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_historical_data: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to fetch stock data: {str(e)}'
            } 