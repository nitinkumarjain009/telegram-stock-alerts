import constants
import database
import telebot
import yfinance as yf


# Telegram token stored in constants.py
TELEGRAM_TOKEN = constants.TELEGRAM_TOKEN

# Create an instance of Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

connection = database.connect()
all_alerts = database.get_all_alerts(connection, *chat_id)

for alert in all_alerts:
    connection = database.connect()
    all_chat_ids = database.get_all_chat_ids(connection)
    for chat_id in all_chat_ids:
            ticker = alert[2]
            yf.download(ticker, period="1y")

# TODO: finish and deploy to Linode