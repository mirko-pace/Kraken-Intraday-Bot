# An Intraday Trading Bot in less than 200 lines of code

As a data scientist, I was always fascinated by the challenge of algorithmic intraday trading. Tinkering with cryptocurrencies is easy if you take advantage of the wide range of trading platforms and APIs available.

The ultimate test of my predictive trading models (I'm experimenting with XGBoost at the moment...) is to let it run on real data, and to do so I wrote a little trading bot leveraging Kraken's API.

## My trading strategy
The bot follows this trading logic: it pulls the 1-minute grain OHLCV (open-high-low-close-volume) data live data and lets you evaluate your trading rules based on any indicator of your choice or feed your predictive model.

When an "enter market" signal is predicted, the trade will proceed, and an order limit will be placed to take your profit if it is realized. You can choose the uplift/profit level you expect from your transaction (the limit price) and how long you want to stay exposed in the market. When the order limit expires, the trade exits at market price. 

## What you need
Just a few libraries to start:
```
pip install pandas krakenex pykrakenapi ta-lib
```
Of course you need a Kraken account and a valid API Key: check [Kraken's documentation to generate yours](https://support.kraken.com/hc/en-us/articles/360000919966-How-to-create-an-API-key).

Once you have your key and secret create a file name `kraken.key`, place it in the same directory as the script and save key and secret like this:
```
keykeykeykeykeykeykeykeykeykeykeykeykeykeykey
secretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecret
```

## Setting up the bot
All the configuration is done at the top of the script. Use Kraken's docs to [check the right currencies codes and supported pairs](https://support.kraken.com/hc/en-us/articles/201893658-Currency-pairs-available-for-trading-on-Kraken)

```python
## your baseline currency when you're off the market
wallet_curr = "USDT"
## which market/currency you want to trade
trade_curr = "XBTC"
## the Kraken pair to trade
pair = "BTCUSDT"

## In some cases you want to trade with a stable coint (i.e. USDT) but follow the fiat ticker
ticker_pair = pair
#ticker_pair = "BTCUSD"


## When set a limit order as a take-profit, how much profit you want to take? (0.01 = 1%)
expected_uplift_for_limit_order = 0.005

## It's your market time window in seconds, in other words how long you want to stay on the market
## with your limit order. 30 minutes = "+1800"
gtd_expiration_for_limit_order = "+1800"

## What's the minimum balance of your baseline currency to enter the market
minimum_funds_threshold = 100

```
