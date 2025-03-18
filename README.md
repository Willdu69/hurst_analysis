# Hurst Exponent and Liquidity Analysis for Crypto Pairs

This script analyzes cryptocurrency pairs on Binance, focusing on liquidity and the Hurst exponent. It aims to identify pairs exhibiting specific statistical behaviors, potentially useful for trading strategies.

## Core Functionality

1.  **Liquidity Assessment (`liquidity_analysis`):**

    This section retrieves real-time order book data and 24-hour trading volume from Binance for all available trading pairs.

    It calculates key liquidity metrics:

    -   **Bid and Ask Liquidity:** The total quantity of buy and sell orders in the order book's top levels.
    -   **24h Quote Volume:** The total traded value of the asset within the last 24 hours, providing a measure of trading activity.
    -   **Relative Spread:** The difference between the best ask and bid prices, normalized by the mid-price, indicating the cost of immediate order execution.
    -   **Liquidity Score:** A combined metric derived from bid/ask liquidity, 24h quote volume, and relative spread. This score attempts to create a single number representing the overall liquidity of a pair.

    The results are stored in `liquidity_analysis.json` and converted to `liquidity_analysis.csv` for easier analysis.

    Essentially, this part of the code answers the question of "how easily can I buy or sell this asset?".

2.  **Hurst Exponent Calculation (`main`):**

    This section focuses on analyzing the statistical properties of the price spreads between pairs of cryptocurrencies.

    It begins by filtering the trading pairs based on their liquidity scores, selecting only those within a defined range. This ensures that the subsequent analysis is performed on relatively liquid pairs.

    For each pair, it fetches historical closing price data from Binance.

    It then calculates the Hurst exponent of the spread between the closing prices of the two assets. The Hurst exponent is a statistical measure that quantifies the long-term memory of a time series.

    -   A Hurst exponent close to 0.5 indicates a random walk (no long-term memory).
    -   A Hurst exponent below 0.5 suggests mean reversion (prices tend to revert to the mean).
    -   A Hurst exponent above 0.5 indicates trending behavior (prices tend to continue in their current direction).

    The calculated Hurst exponents are stored in `hurst_dict.json`, providing a basis for identifying pairs with potential mean-reverting or trending characteristics.

    This part of the code answers the question of "does the price of this pair of assets have a tendency to revert to the mean, or trend?".

3.  **Supporting Functions:**

    -   `fetch_historical_data`: Retrieves historical candlestick data from the Binance API, providing the price data required for the Hurst exponent calculation.
    -   `hurst_exponent`: Implements the Rescaled Range (R/S) analysis to calculate the Hurst exponent of a given time series.
    -   `calculate_liquidity`: Calculates the various liquidity metrics based on the order book and 24-hour volume data.
    -   `json_to_csv`: converts json output to csv format.

## Purpose

The primary purpose of this script is to provide tools for identifying cryptocurrency pairs that exhibit specific liquidity and statistical properties. Traders and analysts can use these insights to:

-   Identify liquid pairs for trading.
-   Explore potential mean-reverting or trending pairs for developing trading strategies.
-   Gain a deeper understanding of the statistical behavior of cryptocurrency markets.
