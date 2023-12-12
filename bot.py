import constants
import telebot 
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf
import database


# Telegram token stored in constants.py
TELEGRAM_TOKEN = constants.TELEGRAM_TOKEN

# Create an instance of Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
        add_alert(call)
    elif call.data == "cb_delete":
        delete_alert(call)
    elif call.data == "cb_show":
        show_all_alerts(call)

def add_alert(call):
    bot.send_message(call.from_user.id, "Type the ticker symbol which you would like to add.")
    bot.register_next_step_handler(call.message, validate_ticker_and_price_data)

def delete_alert(call):
    bot.send_message(call.from_user.id, "Type the alert ID which you would like to delete.")
    show_all_alerts(call)
    # TODO: should first validate before deleting
    bot.register_next_step_handler(call.message, validate_id)

def validate_id(message):
    validated_id = int(message.text) if message.text.isdigit() else None 
    if validated_id:
        connection = database.connect()
        database.delete_alert_by_id(connection, validated_id)
        bot.send_message(call.from_user.id, "Alert has been deleted.")

def show_all_alerts(call):
    connection = database.connect()
    all_alerts = database.get_all_alerts(connection)
    print(all_alerts)
    formatted_alerts = [f"{row_num}\t{row[1]}\t{row[2]}" for row_num, row in enumerate(all_alerts)]
    formatted_alerts = "\n".join(formatted_alerts)
    bot.send_message(call.from_user.id, formatted_alerts)

def validate_ticker(message):
    # Check for illegal symbols
    if any(s in message.text for s in "., "):
        send_error_message(message, category="ticker symbol", reason="an illegal character")
    else:
        validated_ticker = message.text.upper()
        return validated_ticker

def validate_ticker_and_price_data(message):
    '''Handle the user input for entering a ticker symbol'''
    # (Re)set attributes for validation
    validated_ticker = None
    validated_price_data = None

    # Check for illegal symbols
    validated_ticker = validate_ticker(message)
    
    if validated_ticker:
        # Download price data for valid symbol
        price_data = get_price_data(validated_ticker)

        # Check downloaded price data not empty
        if price_data.empty:
            send_error_message(message, category="ticker symbol", reason="a lack of price data")
        else:
            validated_price_data = price_data
            
            last_close = validated_price_data["Adj Close"].iloc[-1]
            last_date = validated_price_data.index[-1].date()
                        
            alert_prompt = f"The last close price for {validated_ticker} is {last_close:.2f} on {last_date}.\n\nAdd an alert level for {validated_ticker}. For example:\n130.02\nMA100 (100 daily moving average)\n10%\n-5.5%"
            price_message = bot.send_message(message.chat.id, alert_prompt)
            bot.register_next_step_handler(message, validate_alert_level, validated_ticker, validated_price_data)

def get_price_data(ticker):
    return yf.download(ticker, period="1y")

def prompt_alert_level(message):
    bot.send_message(message.chat.id, "Type the ticker symbol which you would like to add.")
    bot.register_next_step_handler(message, validate_alert_level)

def validate_alert_level(message, validated_ticker_symbol, validated_price_data):
        ''''''
        last_close = validated_price_data["Adj Close"].iloc[-1]
        if message.text.startswith("MA") and message.text.replace("MA", "", 1).isdigit():
            validated_alert_level = message.text
        elif message.text.replace("%", "", 1).replace(".", "", 1).replace("-", "", 1).isdigit() and message.text.endswith("%"):
            validated_alert_level = (1+float(message.text.replace("%", "", 1))/100)*last_close
        elif message.text.replace(".", "", 1).isdigit():
            validated_alert_level = float(message.text)
        else:
            # Display an error for an invalid alert level
            send_error_message(message, category="alert level", reason="a wrong price input")
            return
        add_alert_to_database(message, validated_ticker_symbol, validated_alert_level, last_close)

def add_alert_to_database(message, validated_ticker_symbol, validated_alert_level, last_close):
    connection = database.connect()
    database.create_table(connection)
    database.add_alert(connection, validated_ticker_symbol, validated_alert_level, last_close)
    bot.send_message(message.chat.id, f"Successfully added alert for {validated_ticker_symbol} at {validated_alert_level:.2f}!")

def send_error_message(message, category, reason):
    bot.send_message(message.chat.id, f"Invalid {category} due to {reason}! Please enter a valid one.")

bot.infinity_polling()


# TODO: fix delete functionality
# TODO: add row_number column to alerts SQL table
# TODO: format show all alerts as table
# TODO: format alert_prompt in a nicer way
# TODO: create check_alerts.py
# TODO: deploy to Linode