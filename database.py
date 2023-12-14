import sqlite3


CREATE_ALERTS_TABLE = "CREATE TABLE IF NOT EXISTS alerts (alert_id INTEGER PRIMARY KEY, chat_id TEXT,  ticker TEXT, alert_level TEXT, last_close REAL);"
GET_MAX_ROW_NUMBER = "SELECT MAX(row_number) FROM alerts;"
INSERT_ALERT = "INSERT INTO alerts (chat_id, ticker, alert_level, last_close) VALUES (?, ?, ?, ?);"
GET_ALL_ALERTS = "SELECT *, ROW_NUMBER() OVER (ORDER BY chat_id) FROM alerts WHERE chat_id=?;"
DELETE_ALERT = "DELETE FROM alerts WHERE alert_id=?;"
GET_ALL_CHAT_IDS = "SELECT DISTINCT chat_id FROM alerts;"

def connect():
    return sqlite3.connect("alerts.db")

def create_table(connection):
    with connection:
        connection.execute(CREATE_ALERTS_TABLE)

def add_alert(connection, chat_id, ticker, alert_level, last_close):
    with connection:
        connection.execute(INSERT_ALERT, (chat_id, ticker, alert_level, last_close))

def get_all_alerts(connection, chat_id):
    with connection:
        return connection.execute(GET_ALL_ALERTS, (chat_id,)).fetchall()

def delete_alert_by_row_number(connection, chat_id, row_number):
    for row in get_all_alerts(connection, chat_id):
        if row[5] == row_number:
            row_id_to_delete = row[0]
    with connection:
        connection.execute(DELETE_ALERT, (row_id_to_delete,))

def get_all_chat_ids(connection):
    with connection:
        return connection.execute(GET_ALL_CHAT_IDS).fetchall()