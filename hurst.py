from binance.client import Client
from itertools import combinations
from tqdm import tqdm
import pandas as pd
import numpy as np
import json
import csv

# Replace with your Binance API key and secret
API_KEY = "8FBVQV0BXPml3EK9OoQwrjDwBSSgg1bgAP9dp92EGUUpxmfeWpBfXYIND8admXL5"
API_SECRET = "CkPE5A6NkVLZnThHJmZFDIN84erSuF2RwLG6abUYCNrGcNfdypCHAN08dQD5RtcO"

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)


def fetch_historical_data(symbol, interval, start_date, end_date=None):
	"""
	Fetch historical candlestick data for a specific ticker.

	:param symbol: Trading pair symbol (e.g., "BTCUSDT").
	:param interval: Time interval (e.g., "1d", "1h", "15m").
	:param start_date: Start date in "YYYY-MM-DD" format.
	:param end_date: End date in "YYYY-MM-DD" format (optional).
	:return: Pandas DataFrame with historical data.
	"""
	klines = client.get_historical_klines(symbol, interval, start_date, end_date)

	# Create a DataFrame
	df = pd.DataFrame(klines, columns=[
		"Open time", "Open", "High", "Low", "Close", "Volume",
		"Close time", "Quote asset volume", "Number of trades",
		"Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
	])

	# Convert timestamp columns to datetime
	df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
	df["Close time"] = pd.to_datetime(df["Close time"], unit="ms")

	# Convert numeric columns to float for easier analysis
	numeric_columns = ["Open", "High", "Low", "Close", "Volume"]
	df[numeric_columns] = df[numeric_columns].astype(float)

	return df


def hurst_exponent(ts, max_lag=20):
	"""
	Calculate the Hurst Exponent of a time series.

	:param ts: Time series data (e.g., closing prices).
	:param max_lag: Maximum lag to consider.
	:return: Hurst Exponent.
	"""
	lags = range(2, max_lag)
	tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
	poly = np.polyfit(np.log(lags), np.log(tau), 1)
	return poly[0] * 2.0


def calculate_liquidity(client, ticker, depth_limit=10):
	"""
	Calculate the liquidity of a ticker based on order book depth and 24-hour trading volume.

	Args:
		client (Client): An instance of Binance's Client class.
		ticker (str): The ticker symbol (e.g., 'BTCUSDT').
		depth_limit (int): Number of levels to consider in the order book (default is 10).

	Returns:
		dict: A dictionary with liquidity metrics, including bid liquidity, ask liquidity, and 24h volume.
	"""
	try:
		# Fetch order book data
		order_book = client.get_order_book(symbol=ticker, limit=depth_limit)
		bids = order_book['bids']  # List of [price, quantity]
		asks = order_book['asks']  # List of [price, quantity]

		# Calculate bid and ask liquidity (total quantity within the specified depth limit)
		bid_liquidity = sum(float(bid[1]) for bid in bids)
		ask_liquidity = sum(float(ask[1]) for ask in asks)

		# Fetch 24-hour ticker information
		ticker_info = client.get_ticker(symbol=ticker)
		quote_volume = float(ticker_info['quoteVolume'])  # Total traded value in quote currency

		best_bid = float(order_book['bids'][0][0])  # Best bid price
		best_ask = float(order_book['asks'][0][0])  # Best ask price

		# Calculate the bid-ask spread
		spread = best_ask - best_bid
		mid_price = (best_ask + best_bid) / 2
		relative_spread = spread / mid_price

		# Combine results into a dictionary
		liquidity = {
			'ticker': ticker,
			'bid_liquidity': bid_liquidity,
			'ask_liquidity': ask_liquidity,
			'24h_quote_volume': quote_volume,
			'relative_spread': relative_spread
		}

		return liquidity

	except Exception as e:
		return None


def liquidity_analysis(client):
	out = {}
	exchange_info = client.get_exchange_info()

	for s in tqdm(exchange_info['symbols']):
		liquidity_score = calculate_liquidity(client, s['symbol'])

		if not liquidity_score:
			# If we got an empty or None result, skip
			continue

		# If any of the values in liquidity_score are zero, skip
		if any(value == 0 for value in liquidity_score.values()):
			continue

		# Otherwise, store this symbol's liquidity metrics
		out[s['symbol']] = {
			'bid_liquidity': liquidity_score['bid_liquidity'],
			'ask_liquidity': liquidity_score['ask_liquidity'],
			'24h_quote_volume': liquidity_score['24h_quote_volume'],
			'relative_spread': liquidity_score['relative_spread'],
			'liquidity_score': (liquidity_score['bid_liquidity'] + liquidity_score['ask_liquidity']) / (liquidity_score['24h_quote_volume']*liquidity_score['relative_spread'])
		}

	# Write results to file
	with open("liquidity_analysis.json", "w") as json_file:
		json.dump(out, json_file)

def json_to_csv(json_file_path, csv_file_path):
	# Read the JSON file
	with open(json_file_path, "r") as json_file:
		data = json.load(json_file)

	# Open or create a CSV file in write mode
	with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
		writer = csv.writer(csv_file)

		# Write the header row
		writer.writerow(["symbol", "bid_liquidity", "ask_liquidity", "24h_quote_volume", "relative_spread", "liquidity_score"])

		# For each symbol in the JSON, write a row in the CSV file
		for symbol, metrics in data.items():
			writer.writerow([
				symbol,
				metrics["bid_liquidity"],
				metrics["ask_liquidity"],
				metrics["24h_quote_volume"],
				metrics["relative_spread"],
				metrics["liquidity_score"]
			])

def main():
	hurst_dict = {}
	ticker_list = []
	with open('liquidity_analysis.json', 'r') as file:
		tickers_data = json.load(file)

	for ticker in tickers_data:
		if 50 < float(tickers_data[ticker]['liquidity_score']) < 100:
			ticker_list.append(ticker)

	pairs = list(combinations(ticker_list, 2))
	interval = "1d"  # Change to your desired interval (e.g., "1h", "15m")
	start_date = "2023-01-01"  # Specify the start date
	end_date = "2023-12-31"  # Optional: Specify the end date

	for pair in tqdm(pairs):
		# Fetch historical data
		historical_data_ticker_1 = fetch_historical_data(pair[0], interval, start_date, end_date)
		historical_data_ticker_2 = fetch_historical_data(pair[1], interval, start_date, end_date)

		# Calculate the Hurst Exponent
		closing_prices_ticker_1 = historical_data_ticker_1["Close"].values
		closing_prices_ticker_2 = historical_data_ticker_2["Close"].values

		if len(closing_prices_ticker_1) != len(closing_prices_ticker_2):
			min_len = min(len(closing_prices_ticker_1), len(closing_prices_ticker_2))
			closing_prices_ticker_1 = closing_prices_ticker_1[len(closing_prices_ticker_1) - min_len:]
			closing_prices_ticker_2 = closing_prices_ticker_2[len(closing_prices_ticker_2) - min_len:]

		hurst = hurst_exponent(closing_prices_ticker_1 - closing_prices_ticker_2)

		print(f"Hurst Exponent for the spread between {pair[0]} and {pair[1]}: {hurst}")

	# Save data with Hurst Exponent to CSV
	hurst_dict[f"{pair[0]}_{pair[1]}"] = hurst

	with open("hurst_dict.json", "w") as json_file:
		json.dump(hurst_dict, json_file)


if __name__ == "__main__":
	main()

