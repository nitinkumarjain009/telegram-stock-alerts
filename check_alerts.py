import constants
import database
import telebot
import yfinance as yf
from logger_config import setup_logger
import os


def main():
    logger = setup_logger(os.path.basename(__file__))
    logger.info("Start")

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
    
    error_message = "Need at least 2 alerts for this script to work"

    if len(all_tickers) < 2:
        logger.error(error_message)
        raise ValueError(error_message)
    
    logger.info(f"Download price data for all alerts")
    price_data = yf.download(all_tickers, period="1y")
    # Check last price against alert level
    for alert in all_alerts:
        alert_id, chat_id, ticker, alert_level, last_close, _ = alert
        current_close = round(price_data[("Adj Close", ticker)].loc[price_data[("Adj Close", ticker)].last_valid_index()], 2)
        

        if "MA" in alert_level:
            alert_level_MA = price_data[("Adj Close", ticker)].rolling(window=int(alert_level.split("MA")[1])).mean().iloc[-1]
            logger.info(f"chat_id: {chat_id}: Checking alert_id {alert_id} at alert level {alert_level} ({alert_level_MA:.2f}) for {ticker} at last close {last_close} and current close {current_close}")
            if (last_close < alert_level_MA and current_close > alert_level_MA) or (last_close > alert_level_MA and current_close < alert_level_MA):
                bot.send_message(chat_id, f"Alert triggered for {ticker}! Current close price {current_close} has crossed alert level {alert_level} ({alert_level_MA:.2f}).")
                connection = database.connect()
                database.delete_alert(connection, alert_id)
                logger.info(f"chat_id: {chat_id}: Alert message sent for {ticker} at alert level {alert_level} ({alert_level_MA:.2f}). Alert deleted.")
            else:
                logger.info(f"chat_id: {chat_id}: Alert not triggered.")
        else:
            alert_level = float(alert_level)
            logger.info(f"chat_id: {chat_id}: Checking alert_id {alert_id} at alert level {alert_level} for {ticker} at last close {last_close} and current close {current_close}")
            if (last_close < alert_level and current_close > alert_level) or (last_close > alert_level and current_close < alert_level):
                bot.send_message(chat_id, f"Alert triggered for {ticker}! Current close price {current_close} has crossed alert level {alert_level}.")
                connection = database.connect()
                database.delete_alert(connection, alert_id)
                logger.info(f"chat_id: {chat_id}: Alert message sent for {ticker} at alert level {alert_level}. Alert deleted.")
            else:
                connection = database.connect()
                database.update_close_price(connection, alert_id, current_close)
                logger.info(f"chat_id: {chat_id}: Alert not triggered for {ticker} at alert level {alert_level}. Updating close price from {last_close} to {current_close}.")

    logger.info("End")

if __name__=="__main__":
    main()
