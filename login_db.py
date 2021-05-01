"""
File to control the database
"""

import sqlite3
from login_helper import hash_pw
from datetime import datetime


def create_db():
    """ Create user database """
    try:
        conn = sqlite3.connect('info.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE users
                    (
                    username text,
                    password text,
                    access text,
                    date text
                    )''')
        conn.commit()
        return True
    except BaseException:
        return False
    finally:
        date = get_date()
        hashed_pw = hash_pw('test1234')
        data_to_insert = [('chuck', hashed_pw, 2, date)]
        try:
            c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", data_to_insert)
            conn.commit()
        except sqlite3.IntegrityError:
            print("Error. Tried to add duplicate record!")
        else:
            print("Success")
        date = get_date()
        hashed_pw = hash_pw('test1234')
        data_to_insert = [('nolan', hashed_pw, 3, date)]
        try:
            c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", data_to_insert)
            conn.commit()
        except sqlite3.IntegrityError:
            print("Error. Tried to add duplicate record!")
        else:
            print("Success")

        date = get_date()
        hashed_pw = hash_pw('test1234')
        data_to_insert = [('george', hashed_pw, 3, date)]
        try:
            c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", data_to_insert)
            conn.commit()
        except sqlite3.IntegrityError:
            print("Error. Tried to add duplicate record!")
        else:
            print("Success")
        date = get_date()
        hashed_pw = hash_pw('test1234')
        data_to_insert = [('dean', hashed_pw, 3, date)]
        try:
            c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", data_to_insert)
            conn.commit()
        except sqlite3.IntegrityError:
            print("Error. Tried to add duplicate record!")
        else:
            print("Success")
        finally:
            if c is not None:
                c.close()
            if conn is not None:
                conn.close()


def get_date():
    """ Generate timestamp for data inserts """
    d = datetime.now()
    return d.strftime("%m/%d/%Y, %H:%M:%S")


def register_user(username, password, access):
    """
    given a username, password, and access, register a new user in the database, returns -1 if the user already exists
    :param username:
    :param password:
    :param access:
    :return:
    """
    date = get_date()
    hashed_pw = hash_pw(password)
    data_to_insert = [(username, hashed_pw, access, date)]
    try:
        conn = sqlite3.connect('info.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        q = c.fetchone()
        if q is not None:
            return -1
        else:
            try:
                c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", data_to_insert)
                conn.commit()
            except sqlite3.IntegrityError:
                print("Error. Tried to add duplicate record!")
            else:
                print("Success")
    finally:
        if c is not None:
            c.close()
        if conn is not None:
            conn.close()


def search_pass(username):
    """
    Given a username select the password and return it
    :param username:
    :return:
    """
    try:
        conn = sqlite3.connect('info.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        q = c.fetchone()
        if q is not None:
            return q
        else:
            return -1
    except sqlite3.DatabaseError:
        return -1
    finally:
        if c is not None:
            c.close()
        if conn is not None:
            conn.close()


def search_access(username):
    """
    given a username select the access level and return it
    :param username:
    :return:
    """
    try:
        conn = sqlite3.connect('info.db')
        c = conn.cursor()
        c.execute("SELECT access FROM users WHERE username=?", (username,))
        q = c.fetchone()
        if q is not None:
            return q
        else:
            return -1
    except sqlite3.DatabaseError:
        return -1
    finally:
        if c is not None:
            c.close()
        if conn is not None:
            conn.close()
