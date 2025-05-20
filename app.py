from flask import Flask, render_template, request, jsonify, send_from_directory
from portfolio.optimizer import PortfolioOptimizer
from portfolio.data_fetcher import DataFetcher
import json
import os
import logging
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/optimize', methods=['POST'])
def optimize_portfolio():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        symbols = [s.strip() for s in data.get('symbols', '').split(',') if s.strip()]
        if not symbols or symbols[0] == '':
            return jsonify({
                'status': 'error',
                'message': 'No stock symbols provided'
            }), 400

        # Normalize and validate time period
        period_map = {
            '1y': '1y',
            '1 year': '1y',
            '5y': '5y',
            '5 years': '5y'
        }
        time_period_raw = str(data.get('time_period', '1y')).strip().lower()
        time_period = period_map.get(time_period_raw)
        if not time_period:
            return jsonify({
                'status': 'error',
                'message': 'Invalid time period. Please use 1 Year or 5 Years.'
            }), 400

        try:
            risk_free_rate = float(data.get('risk_free_rate', 0.02))
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid risk-free rate. Please provide a valid number.'
            }), 400
        
        # Fetch data
        data_fetcher = DataFetcher()
        stock_data = data_fetcher.get_historical_data(symbols, time_period)
        
        if stock_data.get('status') == 'error':
            logger.error(f"Data fetcher error: {stock_data.get('message')}")
            return jsonify({
                'status': 'error',
                'message': stock_data.get('message', 'Failed to fetch stock data')
            }), 400
        
        # Filter out symbols with no or too-short data
        valid_data = {k: v for k, v in stock_data['data'].items() if v.get('returns') and len(v['returns']) > 2}
        if not valid_data or len(valid_data) < 2:
            logger.error(f"No valid stock data found. Data fetched: {stock_data['data']}")
            return jsonify({
                'status': 'error',
                'message': 'Not enough valid stock data found. Please check your symbols and try again.'
            }), 400
            
        logger.info(f"Passing data to optimizer: {valid_data}")
        # Prepare stock_data dict in the same format as before
        stock_data['data'] = valid_data
        
        try:
            # Optimize portfolio
            optimizer = PortfolioOptimizer(stock_data, risk_free_rate)
            optimal_portfolio = optimizer.get_optimal_portfolio()
            
            if optimal_portfolio is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to optimize portfolio. Please try different symbols.'
                }), 500
                
            efficient_frontier = optimizer.get_efficient_frontier()
            
            if efficient_frontier is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to calculate efficient frontier. Please try different symbols.'
                }), 500
            
            return jsonify({
                'status': 'success',
                'optimal_portfolio': optimal_portfolio,
                'efficient_frontier': efficient_frontier
            })
            
        except ValueError as ve:
            logger.error(f"Optimization error: {str(ve)}")
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
            
    except Exception as e:
        logger.error(f"Error in optimize_portfolio: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/stock-data', methods=['POST'])
def get_stock_data():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        symbols = [s.strip() for s in data.get('symbols', '').split(',') if s.strip()]
        if not symbols or symbols[0] == '':
            return jsonify({
                'status': 'error',
                'message': 'No stock symbols provided'
            }), 400

        time_period = data.get('time_period', '1y')
        
        data_fetcher = DataFetcher()
        stock_data = data_fetcher.get_historical_data(symbols, time_period)
        
        if stock_data.get('status') == 'error':
            logger.error(f"Data fetcher error: {stock_data.get('message')}")
            return jsonify({
                'status': 'error',
                'message': stock_data.get('message', 'Failed to fetch stock data')
            }), 400
        
        return jsonify({
            'status': 'success',
            'data': stock_data
        })
    except Exception as e:
        logger.error(f"Error in get_stock_data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 