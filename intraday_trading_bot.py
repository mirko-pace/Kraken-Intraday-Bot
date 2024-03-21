import time
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
import talib as ta
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")


api = krakenex.API()
api.load_key('kraken.key')
k = KrakenAPI(api)

##### DEBUG ##### Switch to False to start trading :)
debug_flag = True #if True now orders are submitted

## your baseline currency when you're off the market
wallet_curr = "ZUSD"
## which market/currency you want to trade
trade_curr = "XBTC"
## the Kraken pair to trade
pair = "BTCUSD"

## When set a limit order as a take-profit, how much profit you want to take? (0.01 = 1%)
expected_uplift_for_limit_order = 0.005

## It's your market time window in seconds, in other words how long you want to stay on the market
## with your limit order. 30 minutes = "+1800"
GTD_expiration_for_limit_order = "+1800"

## What's the minimum balance of your baseline currency to enter the market
minimum_funds_threshold = 100


## colors for the ouput
COLOR_RED = '\033[91m'
COLOR_AMBER = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_END = '\033[0m'  # Reset color to default

# Function to print colored logging messages
def log_message(message, color):
    current_time = time.strftime("[%Y-%m-%d %H:%M:%S] ")  # Get current timestamp
    print(current_time + color + message + COLOR_END)



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


def get_wallet(wallet_curr,util_rate=0.95):
    ## why util_rate? In case you don't want to dry up your account :) 
    balance = k.get_account_balance()
    return round(float(balance[balance.index == wallet_curr]['vol'])*util_rate,2)

  
def get_typical_price(pair):
    ## returns the most up to date typical price of <pair>
    ohlc, last = k.get_ohlc_data(pair,ascending=True)
    last_read = ohlc.tail(1)
    return float((last_read['high']+last_read['low']+last_read['close'])/3)


def make_order(pair,type,ordertype,wallet=get_wallet(wallet_curr),price=None,price2=None
              ,timeinforce="GTD",expiretm="+180",validate=True,prec=2):
    if  price == None:
        price = get_typical_price(pair)
    volume = wallet/price
    res = k.add_standard_order(pair=pair,
                         type=type,
                         ordertype=ordertype,
                         volume=str(volume),
                         price=str(round(price,prec)),
                         price2=price2,
                         timeinforce=timeinforce,
                         expiretm=expiretm,
                         validate=validate)
    return res


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


# Define your algorithm function
def main(k=k,wallet_curr=wallet_curr,pair=pair,debug=True,profit_rate=0.005,expire_limit="+1800",funds_threshold=100):
    log_message(f"### Starting a round! PAIR:{pair} ###", COLOR_GREEN)
    balance = k.get_account_balance() ## get balance of wallet 
    enough_usd = float(balance[balance.index == wallet_curr]['vol']) > funds_threshold ## not enough funds or trade in progress?
    if enough_usd: ## we have enough funds
        log_message(f"Enough balance? Yes", COLOR_BLUE)
        ohlc, last = k.get_ohlc_data(pair,ascending=True) ## retrieve ohlc
        ohlc = enrich_ohlv(ohlc) ## add your indexes
        ohlc = enter_rule(ohlc,force_order=False) ## run the enter rule logic
        if ohlc.iloc[-2]['enter_rule']: ## the last row of ohlc contains the current period/minute so we look at the second last
            log_message(f"Enter rule triggered | {pair} at close: {round(ohlc.iloc[-2]['close'],2)} | (Short MA: {round(ohlc.iloc[-2]['ma14m'],2)}, Long MA: {round(ohlc.iloc[-2]['ma12h'],2)})", COLOR_AMBER)
            order_det = make_order(pair,"buy","market",validate=debug) ## submitting the order! Remember to toggle "validate"
            log_message(f"Order submitted - ID: {order_det['txid'][0]}",COLOR_BLUE)
            log_message(f"Description: {order_det['descr']['order']}",COLOR_END)
            ## Now we prepare the limit order
            buy_price = float(k.query_orders_info(order_det['txid'][0])['price']) ## let's get our buy price/baseline
            limit_order_det = make_order(pair,"sell","limit",price=buy_price*(1+profit_rate),expiretm=expire_limit,validate=debug)
            log_message(f"Limit Order is on!!! - ID: {limit_order_det['txid'][0]}",COLOR_AMBER)
            log_message(f"Description: {limit_order_det['descr']['order']}",COLOR_END)            
        else:
            log_message(f"We stay put | {pair} at close: {round(ohlc.iloc[-2]['close'],2)} | (Short MA: {round(ohlc.iloc[-2]['ma14m'],2)}, Long MA: {round(ohlc.iloc[-2]['ma12h'],2)})", COLOR_END)

    ### so we said we don't have enough funds for a trade, we're likely still in the market with an open
    ### order or an expired order (and we need to exit the market)
    else:
        log_message(f"Enough balance? Nope!", COLOR_RED)
        log_message(f"Balance in {wallet_curr}: {float(balance[balance.index == wallet_curr]['vol'])}", COLOR_END)
        log_message(f"Balance in {trade_curr}: {float(balance[balance.index == trade_curr]['vol'])}", COLOR_END)
        open_orders = k.get_open_orders()
        ## if we have at least an oper order (we should actually have only 1...)
        if open_orders.shape[0] > 0:
            my_open = open_orders[open_orders['descr_pair'] == pair]
            log_message(f"Open orders: {my_open.shape[0]}",COLOR_BLUE)
            mkt_price = get_typical_price(pair)
            for index, o_ord in my_open.iterrows():
                current_timestamp = int(time.time())
                # Calculate the difference in seconds between timestamp and now
                expiration_mins = (int(o_ord['expiretm']) - int(time.time()) ) // 60
                log_message(f"{o_ord['descr_order']} - Expiring in {expiration_mins} minutes",COLOR_END)
                gap = round((mkt_price/float(o_ord['descr_price'])-1)*100,4)
                log_message(f"Current typical price: {round(mkt_price,4)} - we're {gap}% away",COLOR_END)
        else:  ## if we don't have open orders the last one expired, so we revert to wallet
            closed_orders = k.get_closed_orders()
            ## let's just take the last few ones
            closed_orders = closed_orders[0].head(20)
            ## we just need the expired
            exp_orders = closed_orders[closed_orders['status'] == 'expired']
            ## ... and the last expired of our pair
            last_exp_pair_order = exp_orders[exp_orders['descr_pair'] == pair].head(1)
            ## if the order expiration is not older than 60 seconds then revent than exit the market anyway
            if time.time() - int(last_exp_pair_order['expiretm']) < 60:
                revert_order = make_order(pair,"sell","market",validate=debug)
                log_message(f"Revert Order submitted... - ID: {revert_order['txid'][0]}",COLOR_RED)
                log_message(f"Description: {revert_order['descr']['order']}",COLOR_END)
                sell_price = float(k.query_orders_info(revert_order['txid'][0])['price']) ## let's get our sell price
                log_message(f"We sold at {sell_price}",COLOR_END)
            else:
                log_message("Ooops!! We are in a weird state and help is needed, no funds and no open orders!!!",COLOR_RED)


# Main loop to cycle the algorithm every 60 seconds
while True:
    start_time = time.time()  # Record the start time
    main(debug=debug_flag,
         profit_rate=expected_uplift_for_limit_order,
         expire_limit=GTD_expiration_for_limit_order,
         funds_threshold=minimum_funds_threshold)  # Execute the algorithm
    end_time = time.time()  # Record the end time

    # Calculate the duration in seconds
    duration_seconds = end_time - start_time
    log_message("This round took {:.2f} seconds to execute.".format(duration_seconds),COLOR_END)
    time.sleep(60-duration_seconds)  # Pause for 60 seconds before next iteration


