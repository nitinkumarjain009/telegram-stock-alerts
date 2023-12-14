import constants
import database
import telebot
import yfinance


# Telegram token stored in constants.py
TELEGRAM_TOKEN = constants.TELEGRAM_TOKEN

# Create an instance of Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# all_alerts = database.get_all_alerts()

bot.send_message(, "Hi!")

# for alert in all_alerts:
#     ticker = alert[1]
#     previous_close = alert[2]
#     price_data = yf.download(ticker, period="1y")

#     current_close = price_data["Adj Close"].iloc[-1]
    

#     if ((current_close > previous_close) & (["Adj Close"].iloc[-2] < last_close)) | ((new_close < last_close) & (["Adj Close"].iloc[-2] > last_close)):
#         bot.send_message(f"Alert for ticker {ticker}! Price ({})has crossed ")