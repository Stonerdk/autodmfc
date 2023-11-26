import sqlite3
from constants import DB_DIR

conn = sqlite3.connect(DB_DIR)
cursor = conn.cursor()

def db_init():
    cursor.execute('''
        create table if not exists dmfc_log (
            Date TEXT, Time TEXT, Room TEXT, PV REAL, SV REAL, 
            IntegralTime TEXT, IntegralFlow REAL        
        )''')
    cursor.execute('''create table if not exists dmfc_sum
        (Date TEXT, Room TEXT, IntSum REAL, PvSum REAL, LatestTime TEXT)
    ''')

def commit():
    conn.commit()

def db_close():
    conn.close()