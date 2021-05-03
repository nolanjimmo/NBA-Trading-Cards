"""
File to control the database
"""

from app.login_helper import hash_pw, authenticate

from app.query_engine import QueryEngine, get_date, User, NoOutputError


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
    if QueryEngine.check_user_exists(username):
        return -1
    QueryEngine.add_user(username, hashed_pw, access, date)


def search_pass(username):
    """
    Given a username select the password and return it
    :param username:
    :return:
    """
    try:
        user: User = QueryEngine.get_user_from_username(username)
    except NoOutputError:
        return -1
    else:
        return user.hashed_pass


def search_access(username):
    """
    given a username select the access level and return it
    :param username:
    :return:
    """
    try:
        user: User = QueryEngine.get_user_from_username(username)
    except NoOutputError:
        return -1
    else:
        return user.access
