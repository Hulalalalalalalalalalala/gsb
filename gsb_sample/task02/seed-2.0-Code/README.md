# ETH-USD Analysis Dashboard

A comprehensive Streamlit dashboard for analyzing ETH-USD daily price data, including distribution analysis, Monte Carlo simulation, and historical VaR.

## Installation

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Offline Mode (Recommended)

To run the dashboard with the provided offline CSV fixture:

```bash
ETH_BASELINE_DATA=fixtures/eth_usd_daily_fixture.csv streamlit run app.py
```

### Online Mode (Requires Internet Connection)

To fetch data directly from Yahoo Finance:

```bash
streamlit run app.py
```

## Running Tests

To run the test suite:

```bash
pytest -q
```

## Features

1. **Data & Market Chart**: K-line chart with volume and Bollinger Bands
2. **Distribution Analysis**: Returns histogram, Q-Q plot, and statistical summary
3. **Monte Carlo Simulation**: GBM-based price path simulation with substeps
4. **Historical VaR**: 95% confidence VaR calculation and violation analysis

## Jarque-Bera Test Justification

We use the Jarque-Bera test for normality because it is specifically designed to test whether a sample comes from a normal distribution by combining tests for skewness and kurtosis. It is well-suited for large sample sizes, which we typically have with daily price data.
