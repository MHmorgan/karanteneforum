
import sqlite3
import threading
import time

from datetime import datetime
from karantene_forum_lib import *
from typing import List, Tuple


DATABASE = 'karanteneforum.db'
AKTIVITETER_TABLE = 'Aktiviteter'
STATUS_TABLE = 'Status'
MELDINGER_TABLE = 'Meldinger'
RETTIGHETER_TABLE = 'Rettigheter'
LIVE_KVISS_TABLE = 'LiveKviss'


class DB:

    conn: sqlite3.Connection

    def __init__(self, file: str = DATABASE):
        self.file = file

    def __enter__(self) -> sqlite3.Connection:
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()


# ------------------------------------------------------------------------------
# Aktiviteter

Activity = Tuple[str,str]  # (Timestamp, Aktivitet)

def add_activity(text: str, user: str):
    with DB() as db:
        db.execute(f'''INSERT INTO {AKTIVITETER_TABLE} (TEXT, USER) VALUES (?, ?);''', (text,user))


def latest_activity() -> Activity:
    '''Return the most recent activity'''
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), TEXT FROM {AKTIVITETER_TABLE} WHERE TIME=(SELECT max(TIME) FROM {AKTIVITETER_TABLE});''').fetchone()
    return res


def all_activity() -> List[Activity]:
    '''Get all activities. Latest activity is last in list.'''
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), TEXT FROM {AKTIVITETER_TABLE};''').fetchall()
    return res


# ------------------------------------------------------------------------------
# Messages

Message = Tuple[str,str,str]  # (Timestamp, User, Message)

def new_message(msg: str, user: str):
    with DB() as db:
        db.execute(f'INSERT INTO {MELDINGER_TABLE} (MSG, USER) VALUES (?, ?);', (msg,user))


def latest_messages(n: int = 1) -> List[Message]:
    '''Return the n most recent messages'''
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {MELDINGER_TABLE} ORDER BY TIME DESC LIMIT {n};''').fetchall()
    return res


def all_messages() -> List[Message]:
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {MELDINGER_TABLE};''').fetchone()
    return res


# ------------------------------------------------------------------------------
# Status

Status = Tuple[str,str,str]  # (Timestamp, User, Status)

def new_status(msg: str, user: str):
    with DB() as db:
        db.execute(f'INSERT INTO {STATUS_TABLE} (MSG, USER) VALUES (?, ?);', (msg,user))


def edit_latest_status(msg: str):
    with DB() as db:
        db.execute(f'UPDATE {STATUS_TABLE} SET MSG=? WHERE TIME=(SELECT max(TIME) FROM {STATUS_TABLE});', (msg,))


def delete_latest_status():
    with DB() as db:
        db.execute(f'DELETE FROM {STATUS_TABLE} WHERE TIME=(SELECT max(TIME) FROM {STATUS_TABLE});')


def latest_status(n: int = 1) -> List[Status]:
    '''Return the n most recent messages'''
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {STATUS_TABLE} ORDER BY TIME DESC LIMIT {n};''').fetchall()
    return res


def all_status() -> List[Status]:
    with DB() as db:
        res = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {STATUS_TABLE};''').fetchall()
    return res


# ------------------------------------------------------------------------------
# All

def all(n_messages: int = 20) -> Tuple[Activity,Status,List[Message]]:
    '''
    Return info from latest_activity(), latest_status(), and latest_messages()
    using a single connection.
    '''
    with DB() as db:
        activity = db.execute(f'''SELECT datetime(TIME, 'localtime'), TEXT FROM {AKTIVITETER_TABLE} WHERE TIME=(SELECT max(TIME) FROM {AKTIVITETER_TABLE});''').fetchone()
        status   = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {STATUS_TABLE} WHERE TIME=(SELECT max(TIME) FROM {STATUS_TABLE});''').fetchone()
        messages = db.execute(f'''SELECT datetime(TIME, 'localtime'), USER, MSG FROM {MELDINGER_TABLE} ORDER BY TIME DESC LIMIT {n_messages};''').fetchall()
    return activity, status, messages


# ------------------------------------------------------------------------------
# Permissions

Permissions = Tuple[str, bool, bool, bool, bool]  # (Kvissmaster, Status, Tilganger, BDFL)

def get_permissions(user: str) -> Permissions:
    with DB() as db:
        perm = db.execute(f'''SELECT KVISSMASTER, STATUS, TILGANGER, BDFL FROM {RETTIGHETER_TABLE} WHERE USER=?;''', (user,)).fetchone()
    if perm:
        kvissmaster = bool(perm[0])
        status = bool(perm[1])
        tilganger = bool(perm[2])
        bdfl = bool(perm[3])
    else:
        kvissmaster = False
        status = False
        tilganger = False
        bdfl = False
    return (user, kvissmaster, status, tilganger, bdfl)

def all_permissions() -> List[Permissions]:
    with DB() as db:
        permissions = db.execute(f'''SELECT USER, KVISSMASTER, STATUS, TILGANGER, BDFL FROM {RETTIGHETER_TABLE} ORDER BY USER DESC;''').fetchall()
    permissions = [ (str(p[0]), bool(p[1]), bool(p[2]), bool(p[3]), bool(p[4])) for p in permissions ]
    return permissions


def set_permissions(user: str, kvissmaster: bool = False, status: bool = False, tilganger: bool = False):
    kvissmaster = 1 if kvissmaster else 0
    status = 1 if status else 0
    tilganger = 1 if tilganger else 0
    user = user.lower()
    with DB() as db:
        db.execute(f"INSERT OR REPLACE INTO Rettigheter (USER,KVISSMASTER,STATUS,TILGANGER) VALUES ('{user}',?,?,?);", 
                    (kvissmaster,status,tilganger))

def check_permissions(user: str, kvissmaster: bool = False, status: bool = False, tilganger: bool = False, bdfl: bool = False) -> bool:
    with DB() as db:
        perm = db.execute(f'''SELECT KVISSMASTER, STATUS, TILGANGER, BDFL FROM {RETTIGHETER_TABLE} WHERE USER=?;''', (user,)).fetchone()

    if not perm:
        return False
    if bool(perm[3]):
        return True
    if kvissmaster and not bool(perm[0]):
        return False
    if status and not bool(perm[1]):
        return False
    if tilganger and not bool(perm[2]):
        return False
    if bdfl and not bool(perm[3]):
        return False
    return True


# ------------------------------------------------------------------------------
# Live quiz

Livequiz = Tuple[int, str, str, str, bool, str, int]  # (Id, Creator, Name, Description, Active, Winner, Question)

def all_live_quiz() -> List[Livequiz]:
    with DB() as db:
        all_quizes = db.execute(f'''SELECT ID, CREATOR, NAME, DESCRIPTION, ACTIVE, WINNER, QUESTION FROM {LIVE_KVISS_TABLE} ORDER BY TIME DESC;''').fetchall()
    return [ (q[0], q[1], q[2], q[3], bool(q[4]), q[5], q[6]) for q in all_quizes ]


def get_live_quiz(id: int = -1, name: str = '') -> Livequiz:
    with DB() as db:
        if id > 0:
            quiz = db.execute(f'''SELECT ID, CREATOR, NAME, DESCRIPTION, ACTIVE, WINNER, QUESTION FROM {LIVE_KVISS_TABLE} WHERE ID=?;''', (id,)).fetchone()
        else:
            quiz = db.execute(f'''SELECT ID, CREATOR, NAME, DESCRIPTION, ACTIVE, WINNER, QUESTION FROM {LIVE_KVISS_TABLE} WHERE NAME=?;''', (name,)).fetchone()
    return (quiz[0], quiz[1], quiz[2], quiz[3], bool(quiz[4]), quiz[5], quiz[6])


def latest_live_quiz() -> Livequiz:
    with DB() as db:
        quiz = db.execute(f'''SELECT ID, CREATOR, NAME, DESCRIPTION, ACTIVE, WINNER, QUESTION FROM {LIVE_KVISS_TABLE} ORDER BY TIME DESC LIMIT 1;''').fetchone()
    return (quiz[0], quiz[1], quiz[2], quiz[3], bool(quiz[4]), quiz[5], quiz[6])


def new_live_quiz(creator: str, name: str, description: str) -> Livequiz:
    with DB() as db:
        db.execute(f'''INSERT INTO {LIVE_KVISS_TABLE} (CREATOR, NAME, DESCRIPTION) VALUES (?,?,?);''', (creator, name, description))


def update_live_quiz(creator: str, name: str, description: str) -> Livequiz:
    with DB() as db:
        db.execute(f'''INSERT INTO {LIVE_KVISS_TABLE} (CREATOR, NAME, DESCRIPTION) VALUES (?,?,?);''', (creator, name, description))
