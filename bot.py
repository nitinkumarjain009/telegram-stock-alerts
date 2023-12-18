import constants
import telebot 
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf
import database
from logger_config import setup_logger
import os


logger = setup_logger(os.path.basename(__file__))

# Telegram token stored in constants.py
TELEGRAM_TOKEN = constants.TELEGRAM_TOKEN

# Create an instance of Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Create alerts database
connection = database.connect()
database.create_table(connection)

# Define a command handler for /start or /help
@bot.message_handler(commands=["start", "help"])
def start_menu(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("Add alert", callback_data="cb_add"),
        InlineKeyboardButton("Delete alert", callback_data="cb_delete"),
        InlineKeyboardButton("Show all alerts", callback_data="cb_show"),
    )
    bot.send_message(message.chat.id, "Select what you want to do:", reply_markup=markup)

# Define a callback query handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # Call the callback_query method of the AlertBot instance
    if call.data == "cb_add":
        logger.info(f"{call.message.chat.id}: Add Alert button clicked")
        add_alert(call)
    elif call.data == "cb_delete":
        logger.info(f"{call.message.chat.id}: Delete Alert button clicked")
        delete_alert(call)
    elif call.data == "cb_show":
        logger.info(f"{call.message.chat.id}: Show Alerts button clicked")
        show_all_alerts(call)

def add_alert(call):
    bot.send_message(call.message.chat.id, "Type the ticker symbol which you would like to add.")
    logger.info(f"{call.message.chat.id}: Prompt for ticker symbol sent. Wait for response.")
    bot.register_next_step_handler(call.message, validate_ticker_and_price_data)

def delete_alert(call):
    connection = database.connect()
    all_alerts = database.get_all_alerts(connection, call.message.chat.id)
    if all_alerts:
        bot.send_message(call.message.chat.id, "Type the alert ID which you would like to delete.")
        show_all_alerts(call)
        bot.register_next_step_handler(call.message, validate_row_number)
    else:
        bot.send_message(call.message.chat.id, "No alerts have been added yet.")

def validate_row_number(message):
    validated_row_number = int(message.text) if message.text.isdigit() else None 
    if validated_row_number:
        connection = database.connect()
        database.delete_alert_by_row_number(connection, message.chat.id, validated_row_number)
        bot.send_message(message.chat.id, "Alert has been deleted.")
    else:
        bot.send_message(message.chat.id, "That's not a valid alert ID. Please provide only the number.")

def show_all_alerts(call):
    connection = database.connect()
    all_alerts = database.get_all_alerts(connection, call.message.chat.id)
    if all_alerts:
        formatted_alerts = [f"<b>Alert {row[5]}</b>\n<b>Ticker:</b> {row[2]}\n<b>Close Price:</b> {row[4]}\n<b>Alert Level:</b> {row[3]}\n" for row in all_alerts]
        formatted_alerts = "\n".join(formatted_alerts)
        bot.send_message(call.message.chat.id, formatted_alerts, parse_mode="html")
    else:
        bot.send_message(call.message.chat.id, "No alerts have been added yet.")


def validate_ticker_and_price_data(message):
    '''Handle the user input for entering a ticker symbol'''
    
    logger.info(f"{message.chat.id}: Received response: {message.text}")
    
    # (Re)set attributes for validation
    validated_ticker = None
    validated_price_data = None

    # Check for illegal symbols
    validated_ticker = validate_ticker(message)
    
    if validated_ticker:
        # Download price data for valid symbol
        price_data = yf.download(validated_ticker, period="1y")
        logger.info(f"{message.chat.id}: Downloaded price data for {validated_ticker}")

        # Check downloaded price data not empty
        if price_data.empty:
            send_error_message(message, category="ticker symbol", reason="a lack of price data")
            logger.info(f"{message.chat.id}: Price data for {validated_ticker} is empty. Error message sent.")
        else:
            validated_price_data = price_data
            
            last_close = validated_price_data["Adj Close"].iloc[-1]
            last_date = validated_price_data.index[-1].date()
                        
            alert_prompt = f"The last close price for {validated_ticker} is {last_close:.2f} on {last_date}.\n\nAdd an alert level for {validated_ticker}. For example:\n130.02\nMA100 (100 daily moving average)\n10%\n-5.5%"
            price_message = bot.send_message(message.chat.id, alert_prompt)
            logger.info(f"{message.chat.id}: Price data for {validated_ticker} is OK. Prompt for alert level sent. Waiting for reply.")
            bot.register_next_step_handler(message, validate_alert_level, validated_ticker, validated_price_data)

def validate_ticker(message):
    logger.info(f"{message.chat.id}: Validating ticker symbol {message.text}")
    # Check for illegal symbols
    if any(s in message.text for s in "., "):
        send_error_message(message, category="ticker symbol", reason="an illegal character")
        logger.info(f"{message.chat.id}: Error message sent to due to illegal character in ticker symbol: {message.text}")
    else:
        logger.info(f"{message.chat.id}: Ticker symbol {message.text} is valid.")
        validated_ticker = message.text.upper()
        return validated_ticker

# def prompt_alert_level(message):
#     bot.send_message(message.chat.id, "Type the ticker symbol which you would like to add.")
#     bot.register_next_step_handler(message, validate_alert_level)

def validate_alert_level(message, validated_ticker_symbol, validated_price_data):
        ''''''
        logger.info(f"{message.chat.id}: Validating alert level {message.text} for ticker {validated_ticker_symbol}.")
        last_close = round(validated_price_data["Adj Close"].iloc[-1], 2)
        if message.text.startswith("MA") and message.text.replace("MA", "", 1).isdigit():
            validated_alert_level = message.text
        elif message.text.replace("%", "", 1).replace(".", "", 1).replace("-", "", 1).isdigit() and message.text.endswith("%"):
            validated_alert_level = round((1+float(message.text.replace("%", "", 1))/100)*last_close, 2)
        elif message.text.replace(".", "", 1).isdigit():
            validated_alert_level = round(float(message.text), 2)
        else:
            # Display an error for an invalid alert level
            send_error_message(message, category="alert level", reason="a wrong price input")
            logger.info(f"{message.chat.id}: Alert level {message.text} is not valid. Error message sent.")
            return
        logger.info(f"{message.chat.id}: Alert level {message.text} is valid. Adding to database.")
        add_alert_to_database(message, validated_ticker_symbol, validated_alert_level, last_close)

def add_alert_to_database(message, validated_ticker_symbol, validated_alert_level, last_close):
    connection = database.connect()
    database.add_alert(connection, message.chat.id, validated_ticker_symbol, validated_alert_level, last_close)
    bot.send_message(message.chat.id, f"Successfully added alert for {validated_ticker_symbol} at {validated_alert_level}!")

def send_error_message(message, category, reason):
    bot.send_message(message.chat.id, f"Invalid {category} due to {reason}! Please enter a valid one.")

bot.infinity_polling()