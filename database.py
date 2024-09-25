import sqlite3
from logger_config import setup_logger
import os

# Set up logging
logger = setup_logger(os.path.basename(__file__))

# SQL queries
CREATE_ALERTS_TABLE = "CREATE TABLE IF NOT EXISTS alerts (alert_id INTEGER PRIMARY KEY, chat_id TEXT,  ticker TEXT, alert_level TEXT, last_close REAL);"
GET_MAX_ROW_NUMBER = "SELECT MAX(row_number) FROM alerts;"
INSERT_ALERT = "INSERT INTO alerts (chat_id, ticker, alert_level, last_close) VALUES (?, ?, ?, ?);"
GET_ALL_ALERTS = "SELECT *, ROW_NUMBER() OVER (ORDER BY chat_id) FROM alerts;"
GET_ALL_ALERTS_PER_CHAT = "SELECT *, ROW_NUMBER() OVER (ORDER BY chat_id) FROM alerts WHERE chat_id=?;"
DELETE_ALERT = "DELETE FROM alerts WHERE alert_id=?;"
GET_ALL_CHAT_IDS = "SELECT DISTINCT chat_id FROM alerts;"
UPDATE_ALERT_CLOSE = "UPDATE alerts SET last_close=? WHERE alert_id=?;"

def connect():
    """Establish a connection to the SQLite database and return the connection object."""
    logger.info(f"Connect to database")
    return sqlite3.connect("./alerts.db")

def get_all_chat_ids(connection):
    """Retrieve all unique chat IDs from the database that have active alerts."""
    logger.info(f"Retrieving all chat ids with active alerts from database")
    with connection:
        return connection.execute(GET_ALL_CHAT_IDS).fetchall()

def create_table(connection):
    """Create the alerts table if it doesn't already exist in the database."""
    with connection:
        connection.execute(CREATE_ALERTS_TABLE)

def add_alert(connection, chat_id, ticker, alert_level, last_close):
    """Insert a new alert into the database for a specific chat ID, ticker, and alert level."""
    with connection:
        connection.execute(INSERT_ALERT, (chat_id, ticker, alert_level, last_close))
    logger.info(f"{chat_id}: Alert level {alert_level} and last close {last_close} for ticker {ticker} has been added to the database.")

def get_all_alerts(connection, chat_id=None):
    """Retrieve all alerts from the database, or retrieve alerts specific to a chat ID if provided."""
    with connection:
        if chat_id:
            logger.info(f"{chat_id}: Retrieving all alerts for this chat from database")
            return connection.execute(GET_ALL_ALERTS_PER_CHAT, (chat_id,)).fetchall()
        else:
            logger.info(f"Retrieving all alerts from database")
            return connection.execute(GET_ALL_ALERTS).fetchall()

def delete_alert_by_row_number(connection, chat_id, row_number):
    """Delete an alert from the database by its row number for a specific chat ID."""
    for alert in get_all_alerts(connection, chat_id):
        if alert[5] == row_number:
            alert_id = alert[0]
    delete_alert(connection, alert_id)
    logger.info(f"{chat_id}: {row_number} found in database. Alert removed from database.")

def delete_alert(connection, alert_id):
    """Delete an alert from the database by its alert ID."""
    with connection:
        connection.execute(DELETE_ALERT, (alert_id,))

def update_close_price(connection, alert_id, current_close):
    """Update the last close price for a specific alert in the database."""
    with connection:
        connection.execute(UPDATE_ALERT_CLOSE, (current_close, alert_id))
