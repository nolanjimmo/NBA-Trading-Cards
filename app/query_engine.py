import csv
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List, Set

from flask_login import UserMixin

from app import login, db_filename, schema_filename, basedir
from app.login_helper import hash_pw

MAX_CARDS = 5


def json_list_adapter(l: List) -> bytes:
    return json.dumps(l).encode("utf-8")


def json_list_converter(data: bytes) -> List[int]:
    return json.loads(data.decode("utf-8"))


def get_date():
    """ Generate timestamp for data inserts """
    d = datetime.now()
    return d.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Card:
    id: int
    owned: bool
    name: str
    team: str
    pos: str
    age: int
    gp: int
    mpg: int
    fta: int
    ft_pct: int
    two_pa: int
    two_p_pct: int
    three_pa: int
    three_p_pct: int
    shooting_pct: int
    ppointspg: int
    reboundspg: int
    assistspg: int
    stealspg: int
    blockspg: int
    image: str

    def __hash__(self):
        return hash((self.id,
                     self.owned,
                     self.name,
                     self.team,
                     self.pos,
                     self.age,
                     self.gp,
                     self.mpg,
                     self.fta,
                     self.ft_pct,
                     self.two_pa,
                     self.two_p_pct,
                     self.three_pa,
                     self.three_p_pct,
                     self.shooting_pct,
                     self.ppointspg,
                     self.reboundspg,
                     self.assistspg,
                     self.stealspg,
                     self.blockspg,
                     self.image))


def create_card(
        card_data: Tuple[
            int, int, str, str, str, int, int, int, int, int, int,
            int, int, int, int, int, int, int, int, int, str]) -> Card:
    return Card(
        card_data[0],
        bool(card_data[1]),
        card_data[2],
        card_data[3],
        card_data[4],
        card_data[5],
        card_data[6],
        card_data[7],
        card_data[8],
        card_data[9],
        card_data[10],
        card_data[11],
        card_data[12],
        card_data[13],
        card_data[14],
        card_data[15],
        card_data[16],
        card_data[17],
        card_data[18],
        card_data[19],
        card_data[20])


@dataclass
class Trade:
    unique_id: int
    user1_id: int
    user1_cards: Set[int]
    user1_confirmed: bool
    user2_id: int
    user2_cards: Set[int]
    user2_confirmed: bool

    def __hash__(self):
        return hash((self.unique_id, self.user1_id, self.user1_confirmed,
                     self.user2_id, self.user2_confirmed))


def create_trade(trade_data: Tuple[int, int, List[int], int, int, List[int], int]) -> Trade:
    return Trade(trade_data[0], trade_data[1], set(trade_data[2]), bool(trade_data[3]),
                 trade_data[4], set(trade_data[5]), bool(trade_data[6]))


@dataclass
class User(UserMixin):
    unique_id: int
    name: str
    hashed_pass: str
    access: int
    last_seen: datetime
    cards: Set[int]
    trades: Set[int]

    def get_id(self):
        return self.unique_id

    def __hash__(self):
        return hash((self.unique_id, self.name, self.hashed_pass, self.access, self.last_seen))


def create_user(user_data: Tuple[int, str, str, int, datetime, List[int], List[int]]) -> User:
    return User(user_data[0], user_data[1], user_data[2], user_data[3],
                user_data[4], set(user_data[5]), set(user_data[6]))


def check_user_has_cards(user_cards: Set[int], cards: Set[int]):
    for card in cards:
        if card not in user_cards:
            return False

    return True


@login.user_loader
def load_user(unique_id) -> User:
    return QueryEngine.get_user_from_id(unique_id)


class QueryEngineError(Exception):
    """
    Base class for exceptions in this module
    """
    pass


class NoOutputError(QueryEngineError):
    """
    This error is raised when a query returns zero rows
    """

    def __init__(self, query: str, message: str = "No output for query"):
        self.query = query
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.query} -> {self.message}"


def check_trade_is_confirmed(t: Trade):
    return t.user1_confirmed and t.user2_confirmed


class QueryEngine:
    """
    QueryEngine organizes the functions used to interface with the database
    """
    initialized: bool = False

    @staticmethod
    def initialize_database():
        """
        Private method to initialize the database
        """
        db_exists = os.path.exists(db_filename)
        if not db_exists:
            load_database()
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)
        QueryEngine.initialized = True

        if not db_exists:
            QueryEngine.load_test_data()

    @staticmethod
    def load_test_data() -> None:
        """
        load test data
        """
        date = datetime.utcnow()
        hashed_pw = hash_pw('test1234')
        QueryEngine.add_user("chuck", hashed_pw, 3, date)
        user_id = QueryEngine.get_user_from_username("chuck").unique_id
        for card_id in [1, 2, 3]:
            QueryEngine.add_card_to_user(user_id, card_id)

        QueryEngine.add_user("nolan", hashed_pw, 3, date)
        user_id = QueryEngine.get_user_from_username("nolan").unique_id
        for card_id in [4, 5, 6]:
            QueryEngine.add_card_to_user(user_id, card_id)

        QueryEngine.add_user("dean", hashed_pw, 3, date)
        user_id = QueryEngine.get_user_from_username("dean").unique_id
        for card_id in [7, 8, 9]:
            QueryEngine.add_card_to_user(user_id, card_id)

        QueryEngine.add_user("george", hashed_pw, 3, date)
        user_id = QueryEngine.get_user_from_username("george").unique_id
        for card_id in [10, 11, 12]:
            QueryEngine.add_card_to_user(user_id, card_id)

        QueryEngine.create_trade(1, [2], 2, [4])
        QueryEngine.create_trade(3, [7, 8], 4, [10])

    @staticmethod
    def __get_connection() -> sqlite3.Connection:
        """
        private function to return a sqlite3 connection
        :return: a sqlite3 connection object
        """
        if not QueryEngine.initialized:
            QueryEngine.initialize_database()
        return sqlite3.connect(db_filename, detect_types=sqlite3.PARSE_DECLTYPES)

    @staticmethod
    def update_user_last_seen(u: User):
        """
        update the values of last seen
        :param u: the user to update in the db
        """
        query = "update Users set last_seen = ? where id = ?"
        data = u.last_seen, u.unique_id

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

    @staticmethod
    def get_all_users() -> Set[User]:
        """
        get a set of all the users
        :return: a set of all the users
        """
        query = "select * from Users"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query).fetchall()

        if output is None:
            raise NoOutputError(query, "No output for `get_all_users()`")

        users: List[User] = []
        for row in output:
            users.append(create_user(row))

        return set(users)

    @staticmethod
    def get_all_card_ids() -> Set[int]:
        """
        Get the ids of all the cards that exist in the database

        :return: A set of card ids as integers

        :raise NoOutputError: if the query returns zero rows
        """
        query = "select id from Cards"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query).fetchall()

        if output is None:
            raise NoOutputError(query, "No output for `get_all_card_ids()`")

        card_ids: List[int] = []
        for row in output:
            card_ids.append(row[0])

        return set(card_ids)

    @staticmethod
    def get_all_cards() -> Set[Card]:
        """
        Get all the cards that exist in the database

        :return: A set of Cards

        :raise NoOutputError: if the query returns zero rows
        """
        query = "select * from Cards"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query).fetchall()

        if output is None:
            raise NoOutputError(query, "No output for `get_all_cards()`")

        cards: List[Card] = []
        for row in output:
            cards.append(create_card(row))

        return set(cards)

    @staticmethod
    def get_card_from_id(card_id: int) -> Card:
        """
        Get the Card with the given card_id

        :param card_id: the id of the desired card
        :return: the Card with the given card_id

        :raise NoOutputError: if a Card with the given card_id cannot be found
        """
        query = "select * from Cards where id = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (card_id,)).fetchone()

        if output is None:
            raise NoOutputError(query, f"No Card with id: {card_id}")
        return create_card(output)

    @staticmethod
    def get_card_from_name(card_name: str) -> Card:
        """
        Get the Card with the given card_name

        :param card_name: the name of the player for the desired card
        :return: the Card with the given card_name

        :raise NoOutputError: if a Card with the given card_name cannot be found
        """
        query = "select * from Cards where name = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (card_name,)).fetchone()

        if output is None:
            raise NoOutputError(query, f"No Card with name: {card_name}")
        return create_card(output)

    @staticmethod
    def get_trade_from_id(trade_id: int) -> Trade:
        """
        Get the Trade with the given trade_id

        :param trade_id: the id of the desired Trade
        :return: the Trade with the given trade_id

        :raise NoOutputError: if a Trade with the given trade_id cannot be found
        """
        query = "select * from Trades where id = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, str(trade_id)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No Trade with id: {trade_id}")
        return create_trade(output)

    @staticmethod
    def get_trade_from_values(
            user1_id: int,
            user1_cards: List[int],
            user2_id: int,
            user2_cards: List[int]) -> Trade:
        """
        Get a Trade based on the suspected values

        :param user1_id: the id of the first user involved in the trade
        :param user1_cards: the cards being offered by the first user
        :param user2_id: the id of the second user involved in the trade
        :param user2_cards: the cards being offered by the second user
        :return: the Trade with the given values

        :raise NoOutputError: if no trade exists with the given values
        """
        query = "select * from Trades where user1_id = ? and user1_cards = ? and user2_id = ? and user2_cards = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (user1_id, user1_cards, user2_id, user2_cards)).fetchone()

        if output is None:
            raise NoOutputError(query, f"No Trade with values "
                                       f"user1_id: {user1_id}, "
                                       f"user1_cards: {user1_cards}, "
                                       f"user2_id: {user2_id}, "
                                       f"user2_cards: {user2_cards}")
        return create_trade(output)

    @staticmethod
    def get_user_from_id(user_id: int) -> User:
        """
        Get the User with the given user_id

        :param user_id: the id of the desired User
        :return: the User with the given user_id

        :raise NoOutputError: if no User exists with the given user_id
        """
        query = "select * from Users where id = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (user_id,)).fetchone()

        if output is None:
            raise NoOutputError(query, f"No User with id: {user_id}")
        return create_user(output)

    @staticmethod
    def get_available_cards() -> Set[Card]:
        """
        Get the currently available cards that are not owned by other users
        :return: a set of the currently available Cards
        """
        cards = QueryEngine.get_all_cards()
        available_cards = []
        for card in cards:
            if not card.owned:
                available_cards.append(card)

        return set(available_cards)

    @staticmethod
    def get_user_from_username(username: str) -> User:
        """
        Get the User with the given username

        :param username: the name of the User
        :return: the User with the given username

        :raise NoOutputError: if no User exists with the given username
        """
        query = "select * from Users where name = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (username,)).fetchone()

        if output is None:
            raise NoOutputError(query, f"No User with username: {username}")
        return create_user(output)

    @staticmethod
    def get_user_cards(user_id: int) -> Set[Card]:
        """
        Get the Cards of the User with the given user_id

        :param user_id: the id of the User whose Cards will be returned
        :return: a set of the Cards that the User has
        """
        u: User = QueryEngine.get_user_from_id(user_id)
        user_cards: List[Card] = []
        for card_id in u.cards:
            user_cards.append(QueryEngine.get_card_from_id(card_id))

        return set(user_cards)

    @staticmethod
    def get_user_trades(user_id: int) -> Set[Trade]:
        """
        Get the Trades of the User with the given user_id

        :param user_id: the id of the User whose Trades will be returned
        :return: a set of the Trades that the User has
        """
        u: User = QueryEngine.get_user_from_id(user_id)
        user_trades: List[Trade] = []
        for trade_id in u.trades:
            user_trades.append(QueryEngine.get_trade_from_id(trade_id))

        return set(user_trades)

    @staticmethod
    def set_card_owned(card_id: int):
        """
        set the owned field of a Card to true

        :param card_id: the id of the Card that is now owned
        """
        query = "update Cards set owned = ? where id = ?"
        data = 1, card_id
        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

    @staticmethod
    def set_card_not_owned(card_id: int):
        """
        set the owned field of a Card to false

        :param card_id: the id of the Card that is now available
        """
        query = "update Cards set owned = ? where id = ?"
        data = 0, card_id

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

    @staticmethod
    def add_user(username: str, hashed_pass: str, access: int, last_seen: datetime) -> None:
        """
        Add a new User to the database with the given info

        :param username: the username of the new User
        :param hashed_pass: the hashed password of the new User
        :param access: the access level of the new User
        :param last_seen: the str format of the date the new User was last seen
        """
        query = "insert into Users (name, hashed_pass, access, last_seen, cards, trades) values (?, ?, ?, ?, ?, ?)"
        data = str(username), str(hashed_pass), int(access), last_seen, list(), list()
        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:  # Database update failed, rollback changes from this transaction
                conn.rollback()
            else:  # Database update succeeded, commit transaction
                conn.commit()

    @staticmethod
    def __add_trade(user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]) -> None:
        """
        Internal method to add a new Trade without performing any checks, used by the public helper method/s
        """
        query = "insert into Trades (user1_id, user1_cards, user2_id, user2_cards) values (?, ?, ?, ?)"
        data = int(user1_id), user1_cards, int(user2_id), user2_cards

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:  # Database update failed, rollback changes from this transaction
                conn.rollback()
            else:  # Database update succeeded, commit transaction
                conn.commit()

    @staticmethod
    def __check_trade_exists(
            user1_id: int,
            user1_cards: List[int],
            user2_id: int,
            user2_cards: List[int],
            user1_confirmed: bool = False,
            user2_confirmed: bool = False) -> bool:
        """
        Internal method to check if a trade with the given parameters exists

        :return: true if the trade exists, false if it does not
        """
        query = "select 1 from Trades " \
                "where " \
                "user1_id = ? and user1_cards = ? and user1_confirmed = ? " \
                "and user2_id = ? and user2_cards = ? and user2_confirmed = ? " \
                "limit 1"

        data = user1_id, user1_cards, user1_confirmed, user2_id, user2_cards, user2_confirmed

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, data).fetchall()

            return len(output) > 0

    @staticmethod
    def __add_trade_to_user(user_id: int, trade_id: int):
        """
        Internal method to add the trade_id to the trade ids of the User with the given user_id

        :param user_id: the id of the User
        :param trade_id: the id of the Trade
        """
        u: User = QueryEngine.get_user_from_id(user_id)
        new_user_trades: List[int] = list(u.trades)
        new_user_trades.append(trade_id)

        query = "update Users set trades = ? where id = ?"

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, (new_user_trades, user_id))
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

    @staticmethod
    def check_valid_trade(user1_id: int, user1_cards: Set[int], user2_id: int, user2_cards: Set[int]) -> bool:
        """
        Check if a trade between user1 and user2 is valid with the given cards. If both users have all the cards that
        they say they do, then the trade is valid.

        :param user1_id: the id of user1
        :param user1_cards: the cards being offered by user1
        :param user2_id: the id of user2
        :param user2_cards: the cards being offered by user2
        :return: true if the trade is valid and false if it is not
        """
        return check_user_has_cards(QueryEngine.get_user_from_id(user1_id).cards, user1_cards) \
            and check_user_has_cards(QueryEngine.get_user_from_id(user2_id).cards, user2_cards)

    @staticmethod
    def create_trade(user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]):
        """
        Create a new trade between two users.

        :param user1_id: the id of user1
        :param user1_cards: the cards being offered by user1
        :param user2_id: the id of user2
        :param user2_cards: the cards being offered by user2
        """
        if QueryEngine.check_valid_trade(user1_id, set(user1_cards), user2_id, set(user2_cards)):
            # if the trade does not exist already then we can create it
            if not QueryEngine.__check_trade_exists(user1_id, user1_cards, user2_id, user2_cards):
                # add trade to Trades table
                QueryEngine.__add_trade(user1_id, user1_cards, user2_id, user2_cards)

                # get the Trade from the database so that it now has the generated unique id
                new_trade: Trade = QueryEngine.get_trade_from_values(user1_id, user1_cards, user2_id, user2_cards)

                # add the Trade to both Users
                QueryEngine.__add_trade_to_user(user1_id, new_trade.unique_id)
                QueryEngine.__add_trade_to_user(user2_id, new_trade.unique_id)
                return True
        return False

    @staticmethod
    def __remove_trade_from_user(user_id: int, trade_id: int):
        """
        Internal method to remove a trade_id from the trade ids of the User with the user_id

        :param user_id: the id of the User
        :param trade_id: the id of the Trade to be removed
        """
        user_trades: List[int] = list(QueryEngine.get_user_from_id(user_id).trades)
        user_trades.remove(trade_id)

        query = "update Users set trades = ? where id = ?"

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, (user_trades, user_id))
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

    @staticmethod
    def __delete_trade(trade_id: int):
        """
        Internal method to delete a trade from the database

        :param trade_id: the id of the Trade to be deleted
        """
        with QueryEngine.__get_connection() as conn:
            conn.execute("delete from Trades where id = ?", (trade_id,))
            conn.commit()

    @staticmethod
    def delete_trade(trade_id: int):
        """
        Delete a Trade from the database and remove it from both User's trade ids

        :param trade_id: the id of the Trade to be deleted
        """
        t: Trade = QueryEngine.get_trade_from_id(trade_id)
        QueryEngine.__remove_trade_from_user(t.user1_id, trade_id)
        QueryEngine.__remove_trade_from_user(t.user2_id, trade_id)
        QueryEngine.__delete_trade(trade_id)

    @staticmethod
    def check_card_owned(card_id: int):
        """
        check if a card is currently owned

        :param card_id: the id of the Card to check
        :return: true if it is owned and false if it is not owned
        """
        c: Card = QueryEngine.get_card_from_id(card_id)
        return c.owned

    @staticmethod
    def unconfirm_all_trades(user_id: int):
        """
        unconfirm all trades for a user
        :param user_id: the id of the user
        """
        u = QueryEngine.get_user_from_id(user_id)
        for trade_id in u.trades:
            trade = QueryEngine.get_trade_from_id(trade_id)
            QueryEngine.user_unconfirm_trade(u, trade)

    @staticmethod
    def add_card_to_user(user_id: int, card_id: int) -> bool:
        """
        Add the card_id to the card ids of the User with user_id

        :param user_id: the id of the User who the card is being added to
        :param card_id: the id of the Card
        :return: true if succeeds false if fails
        """
        if not QueryEngine.check_card_owned(card_id):
            u: User = QueryEngine.get_user_from_id(int(user_id))
            if len(u.cards) < MAX_CARDS:
                new_user_cards: List[int] = list(u.cards)
                new_user_cards.append(int(card_id))

                query = "update Users set cards = ? where id = ?"

                with QueryEngine.__get_connection() as conn:
                    try:
                        conn.execute(query, (new_user_cards, user_id))
                    except sqlite3.IntegrityError:
                        conn.rollback()
                    else:
                        conn.commit()
                        QueryEngine.set_card_owned(card_id)
                        QueryEngine.unconfirm_all_trades(user_id)
                        return True
            else:
                return False

    @staticmethod
    def remove_card_from_user(user_id: int, card_id: int):
        """
        Remove the card_id from the card ids of the User with user_id

        :param user_id: the id of the User who the Card is being removed from
        :param card_id: the id of the Card
        """
        user = QueryEngine.get_user_from_id(int(user_id))
        user_cards: List[int] = list(user.cards)
        user_cards.remove(int(card_id))

        query = "update Users set cards = ? where id = ?"

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, (user_cards, user_id))
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()
                QueryEngine.set_card_not_owned(card_id)
                for trade_id in user.trades:
                    trade = QueryEngine.get_trade_from_id(trade_id)
                    if int(card_id) in trade.user1_cards.union(trade.user2_cards):
                        QueryEngine.delete_trade(trade_id)

    @staticmethod
    def user_unconfirm_trade(u: User, t: Trade):
        """
        let the User unconfirm the trade

        :param u: the User who would like to unconfirm the trade
        :param t: the Trade that the User would like to unconfirm
        """
        query: str
        data: Tuple
        if u.unique_id == t.user1_id:
            t.user1_confirmed = False
            query = "update Trades set user1_confirmed = ? where id = ?"
            data = t.user1_confirmed, t.unique_id
        elif u.unique_id == t.user2_id:
            t.user2_confirmed = False
            query = "update Trades set user2_confirmed = ? where id = ?"
            data = t.user2_confirmed, t.unique_id
        else:
            raise QueryEngineError("User is not involved in trade", u, t)

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()
                return True

    @staticmethod
    def user_confirm_trade(u: User, t: Trade) -> bool:
        """
        let the User confirm the trade

        :param u: the User who would like to confirm the trade
        :param t: the Trade that the User would like to confirm
        :return: true if success false if fails
        """
        query: str
        data: Tuple
        if u.unique_id == t.user1_id:
            if len(u.cards) + len(t.user1_cards) <= 5:
                t.user1_confirmed = True
                query = "update Trades set user1_confirmed = ? where id = ?"
                data = t.user1_confirmed, t.unique_id
            else:
                return False
        elif u.unique_id == t.user2_id:
            if len(u.cards) + len(t.user2_cards) <= 5:
                t.user2_confirmed = True
                query = "update Trades set user2_confirmed = ? where id = ?"
                data = t.user2_confirmed, t.unique_id
            else:
                return False
        else:
            raise QueryEngineError("User is not involved in trade", u, t)

        with QueryEngine.__get_connection() as conn:
            try:
                conn.execute(query, data)
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                conn.commit()

        if t.user1_confirmed and t.user2_confirmed:
            QueryEngine.do_trade(t.unique_id)

        return True

    @staticmethod
    def do_trade(trade_id: int) -> bool:
        """
        Execute the trade with the given trade_id. The cards offered by user1 will be added to user2 and the cards
        offered by user2 will be added to user1

        :param trade_id: the id of the Trade to execute
        :return: true if the trade succeeds and false if it does not
        """
        t: Trade = QueryEngine.get_trade_from_id(trade_id)
        # check that trade is still valid
        if QueryEngine.check_valid_trade(t.user1_id, t.user1_cards, t.user2_id, t.user2_cards) \
                and check_trade_is_confirmed(t):
            QueryEngine.delete_trade(trade_id)

            user1_cards = QueryEngine.get_user_cards(t.user1_id)
            if len(user1_cards) + len(t.user1_cards) > MAX_CARDS:
                return False

            user2_cards = QueryEngine.get_user_cards(t.user2_id)
            if len(user2_cards) + len(t.user2_cards) > MAX_CARDS:
                return False

            # remove user1 cards from user1 and add them to user2
            for card in t.user1_cards:
                QueryEngine.remove_card_from_user(t.user1_id, card)
                QueryEngine.add_card_to_user(t.user2_id, card)

            # remove user2 cards from user2 and add them to user1
            for card in t.user2_cards:
                QueryEngine.remove_card_from_user(t.user2_id, card)
                QueryEngine.add_card_to_user(t.user1_id, card)
            return True
        else:
            return False

    @staticmethod
    def check_user_exists(username: str) -> bool:
        """
        Check if a User with the given username exists in the database

        :param username: the username of the User
        :return: true if the User exists and false if it does not
        """
        query = "select * from Users where name = ?"

        with QueryEngine.__get_connection() as conn:
            output = conn.execute(query, (username,)).fetchone()
            if output is None:
                return False
            else:
                return True


def load_database() -> None:
    """
    Load the database. Register adapters/converters. Create tables if they don't exist. Load Card data into Cards table.
    """
    conn: sqlite3.Connection
    db_exists = os.path.exists(db_filename)
    with sqlite3.connect(db_filename, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)
        if not db_exists:
            with open(schema_filename, 'rt') as schema_file:
                schema = schema_file.read()
            conn.executescript(schema)

            with open(os.path.join(basedir, "NBAdata.csv"), 'r') as cards_file:
                cards = csv.DictReader(cards_file)

                sql = """insert into Cards (name, team, pos, age, gp, mpg, fta, ft_pct, two_pa, two_p_pct, three_pa, three_p_pct, shooting_pct, ppointspg, reboundspg, assistspg, stealspg, blockspg, image)
                values (:NAME, :TEAM, :POS, :AGE, :GP, :MPG, :FTA, :FTpct, :2PA, :2Ppct, :3PA, :3Ppct, :SHOOTINGpct, :PPOINTSPG, :REBOUNDSPG, :ASSISTSPG, :STEALSPG, :BLOCKSPG, :IMAGE)
                """

                cursor = conn.cursor()
                cursor.executemany(sql, cards)
                cursor.close()

        conn.commit()
