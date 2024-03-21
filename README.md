# An Intraday Trading Bot in less than 200 lines of code

As a data scientist, I was always fascinated by the challenge of algorithmic intraday trading. Tinkering with cryptocurrencies is easy if you take advantage of the wide range of trading platforms and APIs available.

The ultimate test of my predictive trading models (I'm experimenting with XGBoost at the moment...) is to let it run on real data, and to do so I wrote a little trading bot leveraging Kraken's API.

## My trading strategy
The bot follows this trading logic: it pulls the 1-minute grain OHLCV (open-high-low-close-volume) data live data and lets you evaluate your trading rules based on any indicator of your choice or feed your predictive model.

When an "enter market" signal is predicted, the trade will proceed, and an order limit will be placed to take your profit if it is realized. You can choose the uplift/profit level you expect from your transaction (the limit price) and how long you want to stay exposed in the market. When the order limit expires, the trade exits at market price. 

