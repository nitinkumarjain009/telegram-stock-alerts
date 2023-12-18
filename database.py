import sqlite3
from logger_config import setup_logger
import os


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
    return sqlite3.connect("alerts.db")

def get_all_chat_ids(connection):
    with connection:
        return connection.execute(GET_ALL_CHAT_IDS).fetchall()

def create_table(connection):
    with connection:
        connection.execute(CREATE_ALERTS_TABLE)

def add_alert(connection, chat_id, ticker, alert_level, last_close):
    with connection:
        connection.execute(INSERT_ALERT, (chat_id, ticker, alert_level, last_close))
    logger.info(f"{chat_id}: Alert level {message.text} and last close for ticker {ticker} has been added to the database.")

def get_all_alerts(connection, chat_id=None):
    with connection:
        if chat_id:
            return connection.execute(GET_ALL_ALERTS_PER_CHAT, (chat_id,)).fetchall()
        else:
            return connection.execute(GET_ALL_ALERTS).fetchall()

def delete_alert(connection, alert_id):
    with connection:
        connection.execute(DELETE_ALERT, (alert_id,))

def delete_alert_by_row_number(connection, chat_id, row_number):
    for alert in get_all_alerts(connection, chat_id):
        if alert[5] == row_number:
            alert_id = alert[0]
    delete_alert(connection, alert_id)

def update_close_price(connection, alert_id, current_close):
    with connection:
        connection.execute(UPDATE_ALERT_CLOSE, (current_close, alert_id))