# Project Description
A Telegram bot which can set price alerts for stocks and other securities. Data is pulled from Yahoo Finance, using the [yfinance](https://github.com/ranaroussi/yfinance) library. Library used to create Telegram bot is [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI). 

Overview of files:
- bot.py: contains bot logic
- check_alerts.py: runs once per day to check all the alerts that have been set and trigger alert if condition is met
- database.py: CRUD functions for sqlite database. Database used for persistent storage.

# How to set it up
1. Download repository
1. Create constants.py and add the line `TELEGRAM_TOKEN = "TOKEN"` 
    - Note: replace TOKEN with your API token which you can get following [this](https://core.telegram.org/bots/tutorial#obtain-your-bot-token))
1. Run app.py