# Portfolio Optimization Project

A modern web application for portfolio optimization using Modern Portfolio Theory (MPT). This project helps investors build optimal investment portfolios by maximizing returns for a given level of risk.

## Features

- Interactive portfolio optimization using Modern Portfolio Theory
- Real-time stock data fetching from Yahoo Finance
- Efficient frontier visualization
- Sharpe Ratio analysis
- Risk-return metrics calculation
- Responsive web interface

## Technologies Used

- Frontend: HTML, CSS, JavaScript, Chart.js
- Backend: Python (Flask)
- Data Analysis: NumPy, pandas
- Optimization: cvxpy
- Data Visualization: Matplotlib, Chart.js
- Stock Data: yfinance

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Sanskar121543/Portfolio-optimization/edit/main/README.md.git
cd portfolio-optimization
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter the stock symbols you want to analyze (comma-separated)
2. Select the time period for historical data
3. Choose your risk tolerance
4. Click "Optimize Portfolio" to generate the optimal portfolio allocation
5. View the efficient frontier and portfolio metrics

## Project Structure

```
portfolio-optimization/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── portfolio/            # Portfolio optimization module
│   ├── __init__.py
│   ├── optimizer.py      # Portfolio optimization logic
│   └── data_fetcher.py   # Stock data fetching
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. #   P o r t f o l i o - o p t i m i z a t i o n 
 
 
