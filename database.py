import sqlite3


CREATE_ALERTS_TABLE = "CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, ticker TEXT, alert_level TEXT, last_close REAL);"
GET_MAX_ROW_NUMBER = "SELECT MAX(row_number) FROM alerts;"
INSERT_ALERT = "INSERT INTO alerts (ticker, alert_level, last_close) VALUES (?, ?, ?);"
GET_ALL_ALERTS = "SELECT *, ROW_NUMBER() OVER(ORDER BY id) FROM alerts;"
DELETE_ALERT = "DELETE FROM alerts WHERE id=?;"

def connect():
    return sqlite3.connect("alerts.db")

def create_table(connection):
    with connection:
        connection.execute(CREATE_ALERTS_TABLE)

def add_alert(connection, ticker, alert_level, last_close):
    with connection:
        connection.execute(INSERT_ALERT, (ticker, alert_level, last_close))

def get_all_alerts(connection):
    with connection:
        return connection.execute(GET_ALL_ALERTS).fetchall()

def delete_alert_by_row_number(connection, row_number):
    for row in get_all_alerts(connection):
        if row[4] == row_number:
            row_id_to_delete = row[0]
    
    with connection:
        connection.execute(DELETE_ALERT, (row_id_to_delete,))
