import constants
import database
import telebot
import yfinance as yf
from logger_config import setup_logger
import os


logger = setup_logger(os.path.basename(__file__))

# Telegram token stored in constants.py
TELEGRAM_TOKEN = constants.TELEGRAM_TOKEN

# Create an instance of Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Get all chat_ids
connection = database.connect()
all_chat_ids = database.get_all_chat_ids(connection)

# Get all alerts
connection = database.connect()
all_alerts = database.get_all_alerts(connection)

# Download data in one go
all_tickers = set([alert[2] for alert in all_alerts])
price_data = yf.download(all_tickers, period="1y")["Adj Close"]

# Check last price against alert level
for alert in all_alerts:
    alert_id, chat_id, ticker, alert_level, last_close, _ = alert
    current_close = round(price_data[ticker].iloc[-1], 2)
    
    if "MA" in alert_level:
        alert_level_MA = price_data[ticker].rolling(window=int(alert_level.split("MA")[1])).mean().iloc[-1]
        if (last_close < alert_level_MA and current_close > alert_level_MA) or (last_close > alert_level_MA and current_close < alert_level_MA):
            bot.send_message(chat_id, f"Alert triggered for {ticker}! Current close price {current_close} has crossed alert level {alert_level} ({alert_level_MA:.2f}).")
            connection = database.connect()
            database.delete_alert(connection, alert_id)
    else:
        alert_level = float(alert_level)
        if (last_close < alert_level and current_close > alert_level) or (last_close > alert_level and current_close < alert_level):
            bot.send_message(chat_id, f"Alert triggered for {ticker}! Current close price {current_close} has crossed alert level {alert_level}.")
            connection = database.connect()
            database.delete_alert(connection, alert_id)
        else:
            connection = database.connect()
            database.update_close_price(connection, alert_id, current_close)