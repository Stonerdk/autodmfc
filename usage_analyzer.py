import sqlite3
from utils import calculate_price
from dbutils import conn, cursor
# 407
# start date: 2023.11.26

START_DATE = "20231126"
DENSITY = 0.7996
PRICE_PER_KG = 275 # configure

def fetch_by_day(date, room):
    cursor.execute("select IntSum from dmfc_sum where date = ? and room = ?", (date, room))
    res = cursor.fetchone()
    if not res:
        return 0
    return calculate_price(res[0][0])

def fetch_by_month(year, month, room):
    cursor.execute("select sum(IntSum) from dmfc_sum where date = ? and room = ?", (f"{year}{month}*", room))
    res = cursor.fetchone()
    if not res:
        return 0
    return calculate_price(res[0][0])