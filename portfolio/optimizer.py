import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.optimize import minimize
import logging

class PortfolioOptimizer:
    def __init__(self, stock_data, risk_free_rate=0.02):
        """
        Initialize the portfolio optimizer
        
        Args:
            stock_data (dict): Dictionary containing stock data from DataFetcher
            risk_free_rate (float): Risk-free rate for Sharpe ratio calculation
        """
        self.logger = logging.getLogger(__name__)
        
        if not isinstance(stock_data, dict) or 'data' not in stock_data:
            raise ValueError("Invalid stock data format")
            
        self.stock_data = stock_data['data']
        if not self.stock_data:
            raise ValueError("No stock data provided")
            
        self.risk_free_rate = float(risk_free_rate)
        self.returns_matrix = self._prepare_returns_matrix()
        
        if self.returns_matrix.empty:
            raise ValueError("No valid returns data available")
            
        if self.returns_matrix.shape[1] < 2:
            raise ValueError("At least 2 stocks are required for portfolio optimization")
            
        self.mean_returns = self.returns_matrix.mean().values
        self.cov_matrix = self.returns_matrix.cov().values

        # Debug prints
        print("\n[DEBUG] Returns Matrix:\n", self.returns_matrix.head(10))
        print("[DEBUG] Covariance Matrix:\n", self.cov_matrix)

        # Check for all-zero covariance matrix
        if np.allclose(self.cov_matrix, 0):
            raise ValueError("Covariance matrix is all zeros. Check your data alignment and returns calculation.")

        # Validate covariance matrix
        if not np.all(np.linalg.eigvals(self.cov_matrix) > 0):
            self.logger.warning("Covariance matrix is not positive definite, adding small regularization")
            self.cov_matrix = self.cov_matrix + np.eye(self.cov_matrix.shape[0]) * 1e-6
        
    def _prepare_returns_matrix(self):
        """Convert stock data to returns matrix, aligning by date."""
        try:
            returns_dfs = []
            for symbol, data in self.stock_data.items():
                if 'returns' not in data or 'dates' not in data:
                    self.logger.warning(f"No returns or dates data for {symbol}")
                    continue
                df = pd.DataFrame({symbol: data['returns']}, index=pd.to_datetime(data['dates']))
                returns_dfs.append(df)
            if not returns_dfs:
                return pd.DataFrame()
            # Join on date index (inner join to keep only dates present for all stocks)
            returns_matrix = pd.concat(returns_dfs, axis=1, join='inner')
            # Drop any rows with NaNs (shouldn't be any with inner join, but just in case)
            returns_matrix = returns_matrix.dropna()
            if returns_matrix.empty:
                self.logger.error("Aligned returns matrix is empty after joining and dropping NaNs.")
            return returns_matrix
        except Exception as e:
            self.logger.error(f"Error preparing aligned returns matrix: {str(e)}")
            return pd.DataFrame()
    
    def get_optimal_portfolio(self):
        """
        Calculate the optimal portfolio weights using Modern Portfolio Theory (maximize Sharpe ratio) using scipy.optimize
        Returns:
            dict: Dictionary containing optimal portfolio weights and metrics
        """
        try:
            n_assets = len(self.stock_data)
            mean_returns = self.mean_returns
            cov_matrix = self.cov_matrix
            risk_free_rate = self.risk_free_rate

            def neg_sharpe(weights):
                # Ensure weights are numpy array for calculations
                weights = np.array(weights)
                port_return = np.dot(weights, mean_returns)
                port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                # Add a small epsilon to volatility to avoid division by zero
                epsilon = 1e-9
                if port_vol < epsilon:
                     return 1e10 # Return a large value to penalize near-zero volatility
                return -(port_return - risk_free_rate) / port_vol

            # Constraints and bounds
            # Weights sum to 1
            constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
            # Weights are between 0 and 1 (no short selling)
            bounds = tuple((0, 1) for _ in range(n_assets))
            # Initial guess for weights (equal distribution)
            initial_guess = np.array([1.0 / n_assets] * n_assets)

            self.logger.info(f"Starting optimization with scipy.optimize...")
            self.logger.info(f"Initial Guess: {initial_guess}")
            self.logger.info(f"Bounds: {bounds}")
            self.logger.info(f"Constraints: {constraints}")

            # Perform optimization
            result = minimize(neg_sharpe, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)

            self.logger.info(f"Optimization Result: {result}")

            if not result.success:
                self.logger.error(f'Optimization failed: {result.message}')
                # Attempt to return a default or indicative value instead of None if optimization fails
                # This can prevent a subsequent error when trying to access attributes of None
                return {
                    'weights': {symbol: 0.0 for symbol in self.stock_data.keys()},
                    'metrics': {
                        'expected_return': 0.0,
                        'volatility': 0.0,
                        'sharpe_ratio': 0.0
                    },
                    'message': f'Optimization failed: {result.message}'
                }

            optimal_weights = result.x
            # Ensure optimal_weights are non-negative due to potential small negative results from optimizer
            optimal_weights[optimal_weights < 0] = 0
            # Re-normalize weights after setting small negatives to zero
            optimal_weights = optimal_weights / np.sum(optimal_weights)


            port_return = np.dot(optimal_weights, mean_returns)
            port_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
            # Handle potential division by zero for Sharpe ratio if volatility is zero after re-normalization
            sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0.0

            weights_dict = {
                symbol: float(weight)
                for symbol, weight in zip(self.stock_data.keys(), optimal_weights)
            }

            return {
                'weights': weights_dict,
                'metrics': {
                    'expected_return': float(port_return),
                    'volatility': float(port_vol),
                    'sharpe_ratio': float(sharpe)
                }
            }

        except Exception as e:
            self.logger.error(f"Error in get_optimal_portfolio: {str(e)}")
            return {
                'weights': {},
                'metrics': {},
                'message': f'An error occurred during optimization: {str(e)}'
            }
    
    def get_efficient_frontier(self, num_portfolios=100):
        """
        Calculate the efficient frontier
        
        Args:
            num_portfolios (int): Number of portfolios to generate
            
        Returns:
            dict: Dictionary containing efficient frontier data
        """
        try:
            returns = []
            volatilities = []
            weights_list = []
            
            # Generate random portfolios
            for _ in range(num_portfolios):
                weights = np.random.random(len(self.stock_data))
                weights = weights / np.sum(weights)
                
                portfolio_return = np.sum(self.mean_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
                
                returns.append(portfolio_return)
                volatilities.append(portfolio_volatility)
                weights_list.append(weights)
            
            if not returns or not volatilities:
                self.logger.error("Failed to generate efficient frontier points")
                return None
            
            # Find minimum volatility portfolio
            min_vol_idx = np.argmin(volatilities)
            min_vol_portfolio = {
                'weights': {
                    symbol: float(weight)
                    for symbol, weight in zip(self.stock_data.keys(), weights_list[min_vol_idx])
                },
                'return': float(returns[min_vol_idx]),
                'volatility': float(volatilities[min_vol_idx])
            }
            
            return {
                'returns': [float(r) for r in returns],
                'volatilities': [float(v) for v in volatilities],
                'min_vol_portfolio': min_vol_portfolio
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_efficient_frontier: {str(e)}")
            return None 