
import sqlite3
import threading
import time

from datetime import datetime
from karantene_forum_lib import *
from typing import List, Tuple


# def get_db() -> sqlite3.Connection:
#     return sqlite3.connect(DATABASE)


class DB:

    conn: sqlite3.Connection

    def __init__(self, file: str = DATABASE):
        self.file = file

    def __enter__(self) -> sqlite3.Cursor:
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()


################################################################################
#                                                                              #
#  Aktiviteter
#                                                                              #
################################################################################

def add_activity(text: str, user: str):
    with DB() as db:
        db.execute(f'INSERT INTO {AKTIVITETER_TABLE} (TEXT, USER) VALUES (?, ?);', (text,user))


def latest_activity() -> str:
    '''Return the most recent activity'''
    with DB() as db:
        res = db.execute('SELECT TEXT, TIME FROM Aktiviteter WHERE TIME=(SELECT max(TIME) FROM Aktiviteter);').fetchone()
    return res[0] if res else '<ingen aktivitet>'
    # return f'{res[0]} ({res[1]})' if res else '<ingen aktivitet>'


def all_activity() -> List[str]:
    '''Get all activities. Latest activity is last in list.'''
    with DB() as db:
        res = db.execute('''SELECT TEXT, datetime(TIME, 'localtime') FROM Aktiviteter;''').fetchall()
    return [ (i[0], i[1]) for i in res ]