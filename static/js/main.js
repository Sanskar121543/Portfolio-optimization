document.addEventListener('DOMContentLoaded', function() {
    const portfolioForm = document.getElementById('portfolioForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const results = document.getElementById('results');
    let efficientFrontierChart = null;

    portfolioForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading spinner
        loadingSpinner.classList.remove('d-none');
        results.style.display = 'none';
        
        // Get form data
        const symbols = document.getElementById('symbols').value;
        const timePeriod = document.getElementById('timePeriod').value;
        const riskFreeRate = document.getElementById('riskFreeRate').value / 100;
        
        try {
            // Optimize portfolio
            const response = await fetch('/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    symbols,
                    time_period: timePeriod,
                    risk_free_rate: riskFreeRate
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                displayResults(data);
            } else {
                throw new Error(data.message || 'Failed to optimize portfolio');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error: ' + error.message + '\nPlease make sure the server is running and try again.');
        } finally {
            loadingSpinner.classList.add('d-none');
            results.style.display = 'block';
        }
    });

    function displayResults(data) {
        // Display portfolio weights
        const weightsContainer = document.getElementById('portfolioWeights');
        weightsContainer.innerHTML = '';
        
        Object.entries(data.optimal_portfolio.weights).forEach(([symbol, weight]) => {
            const weightElement = document.createElement('div');
            weightElement.className = 'portfolio-weight';
            weightElement.innerHTML = `
                <span>${symbol}</span>
                <span class="metric-value">${(weight * 100).toFixed(2)}%</span>
            `;
            weightsContainer.appendChild(weightElement);
        });
        
        // Display portfolio metrics
        const metricsContainer = document.getElementById('portfolioMetrics');
        metricsContainer.innerHTML = '';
        
        const metrics = [
            ['Expected Return', (data.optimal_portfolio.metrics.expected_return * 100).toFixed(2) + '%'],
            ['Volatility', (data.optimal_portfolio.metrics.volatility * 100).toFixed(2) + '%'],
            ['Sharpe Ratio', data.optimal_portfolio.metrics.sharpe_ratio.toFixed(2)]
        ];
        
        metrics.forEach(([label, value]) => {
            const metricElement = document.createElement('div');
            metricElement.className = 'portfolio-metric';
            metricElement.innerHTML = `
                <span>${label}</span>
                <span class="metric-value">${value}</span>
            `;
            metricsContainer.appendChild(metricElement);
        });
        
        // Display efficient frontier
        displayEfficientFrontier(data.efficient_frontier);
    }

    function displayEfficientFrontier(frontierData) {
        const ctx = document.getElementById('efficientFrontierChart').getContext('2d');

        // Destroy existing chart if it exists
        if (efficientFrontierChart) {
            efficientFrontierChart.destroy();
        }

        // Prepare datasets
        const datasets = [];

        // Add Efficient Frontier data
        if (frontierData && frontierData.returns && frontierData.volatilities) {
             if (frontierData.returns.length === frontierData.volatilities.length) {
                datasets.push({
                    label: 'Efficient Frontier',
                    data: frontierData.returns.map((r, i) => ({
                        x: frontierData.volatilities[i] * 100,
                        y: r * 100
                    })),
                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 1
                });
            } else {
                console.error("Efficient frontier data mismatch: returns and volatilities length differ.");
            }
        } else {
             console.error("Efficient frontier data is missing or incomplete.", frontierData);
        }

        // Add Minimum Volatility Portfolio data
        if (frontierData && frontierData.min_vol_portfolio) {
             datasets.push({
                label: 'Minimum Volatility Portfolio',
                data: [{
                    x: frontierData.min_vol_portfolio.volatility * 100,
                    y: frontierData.min_vol_portfolio.return * 100
                }],
                backgroundColor: 'rgba(220, 53, 69, 0.8)',
                borderColor: 'rgba(220, 53, 69, 1)',
                borderWidth: 1,
                pointRadius: 6
            });
        } else {
             console.warn("Minimum Volatility Portfolio data is missing.");
        }

        // Create new chart only if there's data to plot
        if (datasets.length > 0) {
            efficientFrontierChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Volatility (%)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Expected Return (%)'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Return: ${context.parsed.y.toFixed(2)}%, Volatility: ${context.parsed.x.toFixed(2)}%`;
                                }
                            }
                        }
                    }
                }
            });
        } else {
            console.warn("No datasets to plot for the efficient frontier.");
             // Optionally display a message to the user that the chart cannot be rendered
             if (ctx) { // Clear the canvas if possible
                 ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
             }
        }
    }
}); 