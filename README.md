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

## Adding your favorite indicators
You can easily extend the `enrich_ohlv` function plugging in new indicators from the extensive [TA-Lib library](https://ta-lib.github.io/ta-lib-python/). 
Each indicator is calculated according the time windows contained in the `periods` list. In this example I'm computing the Moving Average (MA) with a 14, 21, 30, 60 minutes and 12 hours window. You can easily extend the list with your favorite periods just keeping the format `[<int>,<string:label>]`. 

As here we're enriching the `ohlcv` data from Kraken you have access to `open, high, low, close` prices and `volume` of your trading pair at 1-minute granularity. 

```python
def enrich_ohlv(df):
    ## df is expected to be an "ohlcv" dataframe similar to get_ohlc_data's output. 
    ## TA-Lib assumes that this dataframe is in ascending order by time to calculate your indexes

    ## add you preferred period in this list and give it a label that will be used as suffix 
    ## TODO: how to nicely handle indexes that require fast and slow periods?
    periods = [[14,'14m'],
               [21,'21m'],
               [30,'30m'],
               [60,'60m'],
               [60*12,'12h']]
    max_periods_available = df.shape[0]
    for period in periods:
        ## kraken OHLC data doesn't go beyond 720 periods (12h in 1-minute grain) and the last 
        ## is always the current, partial period, so we need to cap to the max number of available periods.
        new_period = max_periods_available-1 if period[0] > max_periods_available-1 else period[0]
        df['ma'+period[1]] = ta.MA(df['close'],timeperiod=new_period)
    return df
```

## Implementing your strategy
Once you have your indicators you can then work on your trading strategy. What you have to do is expand the `enter_rule` function, which ingest your enriched dataframe and handles your rules or your prediction model.

If you have deterministic rules you can easily build your logic here, provided that the output is an binary array, where `1` means "enter the market" of the same size of the dataframe.

If you have statistical model you can easily load here your pickle and just do `df[enter_rule] = model.predict(df)`. Again, assuming you're trained the model on a similar dataframe and your `y`s are 0/1 as said before. 

```python
def enter_rule(df,force_order=False):
    ## this runs the market enter logic: you can place here your logic that consumes the enriched (with your indexes) ohlcv dataframe
    ## and attaches an "enter_rule" column with values 0/1. It's 1 when you want to trigger an order

    ## You can set as many sub-conditions/rules as you want...
    condition_1 = (df['ma14m'] > df['ma12h'])
    #condition_2 = (df['mfi14m'].gt(90))
    #condition_3 = <...>

    # ... and then combine those conditions here
    enter_rule_condition = condition_1 #& condition_2 & condition_3

    # Here we create the enter_rule column based on the conditions
    df['enter_rule'] = enter_rule_condition.astype(int)

    ### useful during debugging if you want to force an entry in the market
    if force_order: log_message("#### FORCING ORDER!!! ####",COLOR_RED)
    if force_order: df['enter_rule'] = 1
    return df
```

## You're ready to go!
Now you only have to launch it from your favorite shell and see the magic happen! :D 

```console
mirko@laptop:~$ python intraday_trading_bot.py
```
