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
        bot.send_message(call.from_user.id, "Type the alert ID which you would like to delete.")
        all_alerts = database.get_all_alerts(connection)
        bot.send_message(call.from_user.id, all_alerts)
        bot.register_next_step_handler(call.message, delete_alert_by_id)
        bot.send_message(call.from_user.id, "Alert has been deleted.")
    elif call.data == "cb_show":
        show_all_alerts(call)

def add_alert(call):
    bot.send_message(call.from_user.id, "Type the ticker symbol which you would like to add.")
    bot.register_next_step_handler(call.message, validate_ticker_and_price_data)

def validate_ticker_and_price_data(message):
    '''Handle the user input for entering a ticker symbol'''
    # (Re)set attributes for validation
    validated_ticker_symbol = None
    validated_price_data = None

    # Check for illegal symbols
    if any(s in message.text for s in "., "):
        send_error_message(message, category="ticker symbol", reason="an illegal character")
    else:
        # Download price data for valid symbol
        validated_ticker_symbol = message.text.upper()
        price_data = get_price_data(validated_ticker_symbol)

        # Check downloaded price data not empty
        if price_data.empty:
            send_error_message(message, category="ticker symbol", reason="a lack of price data")
        else:
            validated_price_data = price_data
            alert_prompt = f"Add an alert level for {validated_ticker_symbol}. For example:\n130.02\nMA100 (100 daily moving average)\n10%\n-5.5%"
            price_message = bot.send_message(message.chat.id, alert_prompt)
            bot.register_next_step_handler(message, validate_alert_level, validated_ticker_symbol, validated_price_data)

def get_price_data(ticker):
    return yf.download(ticker, period="1y")

def prompt_alert_level(message):
    bot.send_message(message.chat.id, "Type the ticker symbol which you would like to add.")
    bot.register_next_step_handler(message, validate_alert_level)

def validate_alert_level(message, validated_ticker_symbol, validated_price_data):
        ''''''
        alert_level = None
        last_close = validated_price_data["Adj Close"].iloc[-1]
        
        if message.text.startswith("MA") and message.text.replace("MA", "", 1).isdigit():
            validated_alert_level = message.text
        elif message.text.replace("%", "", 1).replace(".", "", 1).replace("-", "", 1).isdigit() and message.text.endswith("%"):
            validated_alert_level = (1+float(message.text.replace("%", "", 1))/100)*last_close
        elif message.text.replace(".", "", 1).isdigit():
            validated_alert_level = float(message.text)
        else:
            # Display an error for an invalid alert level
            send_error_message(message.chat.id, category="alert level", reason="a wrong price input")
            return
        add_alert_to_database(validated_ticker_symbol, validated_alert_level, last_close)

def add_alert_to_database(validated_ticker_symbol, validated_alert_level, last_close):
    connection = database.connect()
    database.create_table(connection)
    database.add_alert(connection, validated_ticker_symbol, validated_alert_level, last_close)

def show_all_alerts(call):
    connection = database.connect()
    all_alerts = database.get_all_alerts(connection)
    formatted_alerts = "\n".join(map(str, all_alerts))
    bot.send_message(call.from_user.id, formatted_alerts)

bot.infinity_polling()






"""
    def add_alert(self, call):
        '''Orchestrates everything to add an alert'''
        # Send a message prompting user to enter ticker symbol
        bot.send_message(call.from_user.id, "Type the ticker symbol which you would like to add.")
        
        # callback function to set attributes for validated
        # ticker symbol and price to be used for if condition
        bot.register_next_step_handler(call.message, self.validate_ticker_and_price_data)

        print(self.validated_ticker_symbol)
        print(self.validated_price_data)

        # # With validated ticker symbol and price data, proceed 
        # # to prompt user for entering alert level
        # if self.validated_ticker_symbol and self.validated_price_data:
        #     alert_prompt = f"Add an alert level for {self.validated_ticker_symbol}. For example:\n130.02\nMA100 (100 daily moving average)\n10%\n-5.5%"
        #     price_message = bot.send_message(call.from_user.id, alert_prompt)
        #     bot.register_next_step_handler(price_message, self.validate_alert_level)
        
        # if self.validated_price_data:
        #     database.add_alert(self.connection, self.validated_ticker_symbol, self.alert_level, self.last_close)
 
    def validate_ticker_and_price_data(self, message):
        '''Handle the user input for entering a ticker symbol'''
        # (Re)set attributes for validation
        self.validated_ticker_symbol = None
        self.validated_price_data = None

        # Check for illegal symbols
        if any(s in message.text for s in "., "):
            self.send_error_message(message, category="ticker symbol", reason="an illegal character")
        else:
            # Download price data for valid symbol
            self.validated_ticker_symbol = message.text.upper()
            price_data = self.get_price_data(self.validated_ticker_symbol)

        # Check downloaded price data not empty
        if price_data.empty:
            self.send_error_message(message, category="ticker symbol", reason="a lack of price data")
        else:
            self.validated_price_data = price_data

    def validate_alert_level(self, message):
        ''''''
        # (Re)set attribute for validation
        self.alert_level = None

        # Store last close price
        self.last_close = self.validated_price_data["Adj Close"].iloc[-1]
        
        # 
        if message.text.startswith("MA") and message.text.replace("MA", "", 1).isdigit():
            self.alert_level = message.text
        elif message.text.replace("%", "", 1).replace(".", "", 1).replace("-", "", 1).isdigit() and message.text.endswith("%"):
            self.alert_level = (1+float(message.text.replace("%", "", 1))/100)*self.last_close
        elif message.text.replace(".", "", 1).isdigit():
            self.alert_level = float(message.text)
        else:
            # Display an error for an invalid alert level
            self.send_error_message(message.chat.id, category="alert level", reason="a wrong price input")
        

    
    def send_error_message(message, category, reason):
        bot.send_message(message.chat.id, f"Invalid {category} due to {reason}! Please enter a valid one.")

    def delete_alert_by_id(message):
        ''''''
        validated_id = message.text # check if int and in database
        database.delete_alert_by_id(validated_id)

"""