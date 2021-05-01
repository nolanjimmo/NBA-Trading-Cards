import os
import sqlite3
import csv
import json
from dataclasses import dataclass
from typing import Tuple, List, Set

db_filename = "trading_card_data.db"
schema_filename = "trading_card_schema.sql"


def json_list_adapter(l: List) -> bytes:
    return json.dumps(l).encode("utf-8")


def json_list_converter(data: bytes) -> List[int]:
    return json.loads(data.decode("utf-8"))


@dataclass
class Card:
    id: int
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

    def __hash__(self):
        return hash((self.id,
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
                     self.blockspg))


def create_card(
        card_data: Tuple[
            int, str, str, str, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int]) -> Card:
    return Card(
        card_data[0],
        card_data[1],
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
        card_data[18])


@dataclass
class Trade:
    id: int
    user1_id: int
    user1_cards: Set[int]
    user2_id: int
    user2_cards: Set[int]

    def __hash__(self):
        return hash((self.id, self.user1_id, self.user1_cards, self.user2_id, self.user2_cards))


def create_trade(trade_data: Tuple[int, int, List[int], int, List[int]]) -> Trade:
    return Trade(trade_data[0], trade_data[1], set(trade_data[2]), trade_data[3], set(trade_data[4]))


@dataclass
class User:
    id: int
    name: str
    cards: Set[int]
    trades: Set[int]

    def __hash__(self):
        return hash((self.id, self.name, self.cards, self.trades))


def create_user(user_data: Tuple[int, str, List[int], List[int]]) -> User:
    return User(user_data[0], user_data[1], set(user_data[2]), set(user_data[3]))


def check_user_has_cards(user_cards: Set[int], cards: Set[int]):
    for card in cards:
        if card not in user_cards:
            return False

    return True


class QueryEngineError(Exception):
    """
    Base class for exceptions in this module
    """
    pass


class NoOutputError(QueryEngineError):
    def __init__(self, query: str, message: str = "No output for query"):
        self.query = query
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.query} -> {self.message}"


class QueryEngine:
    """
    QueryEngine manages the database connection and has functions to query and update the database.
    This class should be instantiated using the `with QueryEngine(<db_loc>) as qe:` statement
    """
    conn: sqlite3.Connection

    def __init__(self, db_loc: str):
        self.conn = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def get_all_card_ids(self) -> Set[int]:
        """
        Get the ids of all the cards that exist in the database

        :return: A set of card ids as integers

        :raise NoOutputError: if the query returns zero rows
        """
        query = "select id from Cards"
        output = self.conn.execute(query).fetchall()
        if output is None:
            raise NoOutputError(query, "No output for `get_all_card_ids()`")

        card_ids: List[int] = []
        for row in output:
            card_ids.append(row[0])

        return set(card_ids)

    def get_all_cards(self) -> Set[Card]:
        """
        Get all the cards that exist in the database

        :return: A set of Cards

        :raise NoOutputError: if the query returns zero rows
        """
        query = "select * from Cards"
        output = self.conn.execute(query).fetchall()
        if output is None:
            raise NoOutputError(query, "No output for `get_all_cards()`")

        cards: List[Card] = []
        for row in output:
            cards.append(create_card(row))

        return set(cards)

    def get_card_from_id(self, card_id: int) -> Card:
        """
        Get the Card with the given card_id

        :param card_id: the id of the desired card
        :return: the Card with the given card_id

        :raise NoOutputError: if a Card with the given card_id cannot be found
        """
        query = "select * from Cards where id = ?"
        output = self.conn.execute(query, (card_id,)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No Card with id: {card_id}")
        return create_card(output)

    def get_card_from_name(self, card_name: str) -> Card:
        """
        Get the Card with the given card_name

        :param card_name: the name of the player for the desired card
        :return: the Card with the given card_name

        :raise NoOutputError: if a Card with the given card_name cannot be found
        """
        query = "select * from Cards where name = ?"
        output = self.conn.execute(query, (card_name,)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No Card with name: {card_name}")
        return create_card(output)

    def get_trade_from_id(self, trade_id: int) -> Trade:
        """
        Get the Trade with the given trade_id

        :param trade_id: the id of the desired Trade
        :return: the Trade with the given trade_id

        :raise NoOutputError: if a Trade with the given trade_id cannot be found
        """
        query = "select * from Trades where id = ?"
        output = self.conn.execute(query, str(trade_id)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No Trade with id: {trade_id}")
        return create_trade(output)

    def get_trade_from_values(
            self,
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
        output = self.conn.execute(query, (user1_id, user1_cards, user2_id, user2_cards)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No Trade with values "
                                       f"user1_id: {user1_id}, "
                                       f"user1_cards: {user1_cards}, "
                                       f"user2_id: {user2_id}, "
                                       f"user2_cards: {user2_cards}")
        return create_trade(output)

    def get_user_from_id(self, user_id: int) -> User:
        """
        Get the User with the given user_id

        :param user_id: the id of the desired User
        :return: the User with the given user_id

        :raise NoOutputError: if no User exists with the given user_id
        """
        query = "select * from Users where id = ?"
        output = self.conn.execute(query, (user_id,)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No User with id: {user_id}")
        return create_user(output)

    def get_user_from_username(self, username: str) -> User:
        """
        Get the User with the given username

        :param username: the name of the User
        :return: the User with the given username

        :raise NoOutputError: if no User exists with the given username
        """
        query = "select * from Users where name = ?"
        output = self.conn.execute(query, (username,)).fetchone()
        if output is None:
            raise NoOutputError(query, f"No User with username: {username}")
        return create_user(output)

    def get_user_cards(self, user_id: int) -> Set[Card]:
        """
        Get the Cards of the User with the given user_id

        :param user_id: the id of the User whose Cards will be returned
        :return: a set of the Cards that the User has
        """
        u: User = self.get_user_from_id(user_id)
        user_cards: List[Card] = []
        for card_id in u.cards:
            user_cards.append(self.get_card_from_id(card_id))

        return set(user_cards)

    def get_user_trades(self, user_id: int) -> Set[Trade]:
        """
        Get the Trades of the User with the given user_id

        :param user_id: the id of the User whose Trades will be returned
        :return: a set of the Trades that the User has
        """
        u: User = self.get_user_from_id(user_id)
        user_trades: List[Trade] = []
        for trade_id in u.trades:
            user_trades.append(self.get_trade_from_id(trade_id))

        return set(user_trades)

    def add_user(self, username: str, cards: List[int] = None, trades: List[int] = None) -> None:
        """
        Add a new User to the database with the given info

        :param username: the username of the new User
        :param cards: the cards that the new User has, default is none
        :param trades: the trades that the new User has, default is none
        """
        if cards is None:
            cards = []
        if trades is None:
            trades = []

        try:
            query = "insert into Users (name, cards, trades) values (?, ?, ?)"
            self.conn.execute(query, (username, cards, trades))
        except sqlite3.IntegrityError:  # Database update failed, rollback changes from this transaction
            self.conn.rollback()
        else:  # Database update succeeded, commit transaction
            self.conn.commit()

    def __add_trade(self, user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]) -> None:
        """
        Internal method to add a new Trade without performing any checks, used by the public helper method/s
        """
        query = "insert into Trades (user1_id, user1_cards, user2_id, user2_cards) values (?, ?, ?, ?)"
        try:
            self.conn.execute(query, (user1_id, user1_cards, user2_id, user2_cards))
        except sqlite3.IntegrityError:  # Database update failed, rollback changes from this transaction
            self.conn.rollback()
        else:  # Database update succeeded, commit transaction
            self.conn.commit()

    def __check_trade_exists(
            self,
            user1_id: int,
            user1_cards: List[int],
            user2_id: int,
            user2_cards: List[int]) -> bool:
        """
        Internal method to check if a trade with the given parameters exists

        :return: true if the trade exists, false if it does not
        """
        query = "select 1 from Trades " \
                "where user1_id = ? and user1_cards = ? and user2_id = ? and user2_cards = ? limit 1"

        output = self.conn.execute(query, (user1_id, user1_cards, user2_id, user2_cards)).fetchall()

        return len(output) > 0

    def __add_trade_to_user(self, user_id: int, trade_id: int):
        """
        Internal method to add the trade_id to the trade ids of the User with the given user_id

        :param user_id: the id of the User
        :param trade_id: the id of the Trade
        """
        u: User = self.get_user_from_id(user_id)
        new_user_trades: List[int] = list(u.trades)
        new_user_trades.append(trade_id)

        query = "update Users set trades = ? where id = ?"
        try:
            self.conn.execute(query, (new_user_trades, user_id))
        except sqlite3.IntegrityError:
            self.conn.rollback()
        else:
            self.conn.commit()

    def check_valid_trade(self, user1_id: int, user1_cards: Set[int], user2_id: int, user2_cards: Set[int]) -> bool:
        """
        Check if a trade between user1 and user2 is valid with the given cards. If both users have all the cards that
        they say they do, then the trade is valid.

        :param user1_id: the id of user1
        :param user1_cards: the cards being offered by user1
        :param user2_id: the id of user2
        :param user2_cards: the cards being offered by user2
        :return: true if the trade is valid and false if it is not
        """
        return check_user_has_cards(self.get_user_from_id(user1_id).cards, user1_cards) \
               and check_user_has_cards(self.get_user_from_id(user2_id).cards, user2_cards)

    def create_trade(self, user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]):
        """
        Create a new trade between two users.

        :param user1_id: the id of user1
        :param user1_cards: the cards being offered by user1
        :param user2_id: the id of user2
        :param user2_cards: the cards being offered by user2
        """
        if self.check_valid_trade(user1_id, set(user1_cards), user2_id, set(user2_cards)):
            # if the trade does not exist already then we can create it
            if not self.__check_trade_exists(user1_id, user1_cards, user2_id, user2_cards):
                # add trade to Trades table
                self.__add_trade(user1_id, user1_cards, user2_id, user2_cards)

                # get the Trade from the database so that it now has the generated unique id
                new_trade: Trade = self.get_trade_from_values(user1_id, user1_cards, user2_id, user2_cards)

                # add the Trade to both Users
                self.__add_trade_to_user(user1_id, new_trade.id)
                self.__add_trade_to_user(user2_id, new_trade.id)

    def __remove_trade_from_user(self, user_id: int, trade_id: int):
        """
        Internal method to remove a trade_id from the trade ids of the User with the user_id

        :param user_id: the id of the User
        :param trade_id: the id of the Trade to be removed
        """
        user_trades: List[int] = list(self.get_user_from_id(user_id).trades)
        user_trades.remove(trade_id)

        query = "update Users set trades = ? where id = ?"
        try:
            self.conn.execute(query, (user_trades, user_id))
        except sqlite3.IntegrityError:
            self.conn.rollback()
        else:
            self.conn.commit()

    def __delete_trade(self, trade_id: int):
        """
        Internal method to delete a trade from the database

        :param trade_id: the id of the Trade to be deleted
        """
        self.conn.execute("delete from Trades where id = ?", (trade_id,))
        self.conn.commit()

    def delete_trade(self, trade_id: int):
        """
        Delete a Trade from the database and remove it from both User's trade ids

        :param trade_id: the id of the Trade to be deleted
        """
        t: Trade = self.get_trade_from_id(trade_id)
        self.__remove_trade_from_user(t.user1_id, trade_id)
        self.__remove_trade_from_user(t.user2_id, trade_id)
        self.__delete_trade(trade_id)

    def add_card_to_user(self, user_id: int, card_id: int):
        """
        Add the card_id to the card ids of the User with user_id

        :param user_id: the id of the User who the card is being added to
        :param card_id: the id of the Card
        """
        u: User = self.get_user_from_id(user_id)
        new_user_cards: List[int] = list(u.cards)
        new_user_cards.append(card_id)

        query = "update Users set cards = ? where id = ?"
        try:
            self.conn.execute(query, (new_user_cards, user_id))
        except sqlite3.IntegrityError:
            self.conn.rollback()
        else:
            self.conn.commit()

    def remove_card_from_user(self, user_id: int, card_id: int):
        """
        Remove the card_id from the card ids of the User with user_id

        :param user_id: the id of the User who the Card is being removed from
        :param card_id: the id of the Card
        """
        user_cards: List[int] = list(self.get_user_from_id(user_id).cards)
        user_cards.remove(card_id)

        query = "update Users set cards = ? where id = ?"
        try:
            self.conn.execute(query, (user_cards, user_id))
        except sqlite3.IntegrityError:
            self.conn.rollback()
        else:
            self.conn.commit()

    def do_trade(self, trade_id: int) -> bool:
        """
        Execute the trade with the given trade_id. The cards offered by user1 will be added to user2 and the cards
        offered by user2 will be added to user1

        :param trade_id: the id of the Trade to execute
        :return: true if the trade succeeds and false if it does not
        """
        t: Trade = self.get_trade_from_id(trade_id)
        # check that trade is still valid
        if self.check_valid_trade(t.user1_id, t.user1_cards, t.user2_id, t.user2_cards):
            self.delete_trade(trade_id)

            # remove user1 cards from user1 and add them to user2
            for card in t.user1_cards:
                self.remove_card_from_user(t.user1_id, card)
                self.add_card_to_user(t.user2_id, card)

            # remove user2 cards from user2 and add them to user1
            for card in t.user2_cards:
                self.remove_card_from_user(t.user2_id, card)
                self.add_card_to_user(t.user1_id, card)
            return True
        else:
            return False

    def check_user_exists(self, username: str) -> bool:
        """
        Check if a User with the given username exists in the database

        :param username: the username of the User
        :return: true if the User exists and false if it does not
        """
        query = "select * from Users where name = ?"
        output = self.conn.execute(query, (username,)).fetchone()
        if output is None:
            return False
        else:
            return True


def load_database(db_loc: str, schema_loc: str) -> None:
    """
    Load the database. Register adapters/converters. Create tables if they don't exist. Load Card data into Cards table.

    :param db_loc: the relative path to the database file
    :param schema_loc: the relative path to the schema file
    """
    conn: sqlite3.Connection
    db_exists = os.path.exists(db_loc)
    with sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)
        if not db_exists:
            with open(schema_loc, 'rt') as schema_file:
                schema = schema_file.read()
            conn.executescript(schema)

            with open("NBAdata.csv", 'r') as cards_file:
                cards = csv.DictReader(cards_file)

                sql = """insert into Cards (name, team, pos, age, gp, mpg, fta, ft_pct, two_pa, two_p_pct, three_pa, three_p_pct, shooting_pct, ppointspg, reboundspg, assistspg, stealspg, blockspg)
                values (:NAME, :TEAM, :POS, :AGE, :GP, :MPG, :FTA, :FTpct, :2PA, :2Ppct, :3PA, :3Ppct, :SHOOTINGpct, :PPOINTSPG, :REBOUNDSPG, :ASSISTSPG, :STEALSPG, :BLOCKSPG)
                """

                cursor = conn.cursor()
                cursor.executemany(sql, cards)
                cursor.close()

        conn.commit()


def load_test_data(qe: QueryEngine) -> None:
    qe.add_user("chuck", [1, 2, 3], [])
    qe.add_user("nolan", [4, 5, 6], [])
    qe.add_user("dean", [7, 8, 9], [])
    qe.add_user("george", [10, 11, 12], [])

    qe.create_trade(1, [2], 2, [4])
    qe.create_trade(3, [7, 8], 4, [10])


if __name__ == "__main__":
    if os.path.exists(db_filename):
        os.remove(db_filename)
    load_database(db_filename, schema_filename)

    with QueryEngine(db_filename) as qe:
        load_test_data(qe)
