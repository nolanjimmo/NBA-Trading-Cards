import os
import sqlite3
import csv
import json
from dataclasses import dataclass
from typing import Tuple, List

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


def create_card(
        card_data: Tuple[
            int, str, str, str, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int
        ]) -> Card:
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
    user1_cards: Tuple[int]
    user2_id: int
    user2_cards: Tuple[int]


def create_trade(trade_data: Tuple[int, int, List[int], int, List[int]]) -> Trade:
    return Trade(trade_data[0], trade_data[1], tuple(trade_data[2]), trade_data[3], tuple(trade_data[4]))


@dataclass
class User:
    id: int
    name: str
    cards: Tuple[int]
    trades: Tuple[int]


def create_user(user_data: Tuple[int, str, List[int], List[int]]) -> User:
    return User(user_data[0], user_data[1], tuple(user_data[2]), tuple(user_data[3]))


def check_user_has_cards(user_cards: Tuple[int], cards: Tuple[int]):
    for card in cards:
        if card not in user_cards:
            return False

    return True


class QueryEngine:
    conn: sqlite3.Connection

    def __init__(self, db_loc: str):
        self.conn = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def get_all_card_ids(self) -> Tuple[int]:
        output = self.conn.execute("select id from Cards").fetchall()
        if output is None:
            raise Exception("cards have not been loaded")

        card_ids: List[int] = []
        for row in output:
            card_ids.append(row[0])

        return tuple(card_ids)

    def get_all_cards(self) -> Tuple[Card]:
        output = self.conn.execute("select * from Cards").fetchall()
        if output is None:
            raise Exception("cards have not been loaded")

        cards: List[Card] = []
        for row in output:
            cards.append(create_card(row))

        return tuple(cards)

    def get_card_from_id(self, card_id: int) -> Card:
        output = self.conn.execute("select * from Cards where id = ?", (card_id,)).fetchone()
        if output is None:
            raise Exception("no card with id", card_id)
        return create_card(output)

    def get_trade_from_id(self, trade_id: int) -> Trade:
        output = self.conn.execute("select * from Trades where id = ?", (trade_id,)).fetchone()
        if output is None:
            raise Exception("no trade with id", trade_id)
        return create_trade(output)

    def get_trade_from_values(self, user1_id: int, user1_cards: List[int], user2_id: int,
                              user2_cards: List[int]) -> Trade:
        output = self.conn.execute(
            "select * from Trades where user1_id = ? and user1_cards = ? and user2_id = ? and user2_cards = ?",
            (user1_id, user1_cards, user2_id, user2_cards)).fetchone()
        if output is None:
            raise Exception("no trade with values", user1_id, user1_cards, user2_id, user2_cards)
        return create_trade(output)

    def get_user_from_id(self, user_id: int) -> User:
        output = self.conn.execute("select * from Users where id = ?", (user_id,)).fetchone()
        if output is None:
            raise Exception("no user with id", user_id)
        return create_user(output)

    def get_user_from_username(self, username: str) -> User:
        output = self.conn.execute("select * from Users where name = ?", (username,)).fetchone()
        if output is None:
            raise Exception("no user with username", username)
        return create_user(output)

    def get_user_cards(self, user_id: int) -> Tuple[Card]:
        u: User = self.get_user_from_id(user_id)
        user_cards: List[Card] = []
        for card_id in u.cards:
            user_cards.append(self.get_card_from_id(card_id))

        return tuple(user_cards)

    def get_user_trades(self, user_id: int) -> Tuple[Trade]:
        u: User = self.get_user_from_id(user_id)
        user_trades: List[Trade] = []
        for trade_id in u.trades:
            user_trades.append(self.get_trade_from_id(trade_id))

        return tuple(user_trades)

    def add_user(self, username: str, cards: List[int], trades: List[int]) -> None:
        try:
            self.conn.execute("insert into Users (name, cards, trades) values (?, ?, ?)", (username, cards, trades))
        except sqlite3.IntegrityError as err:
            print("ERROR:", err)
            self.conn.rollback()
        else:
            self.conn.commit()

    def __add_trade(self, user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]) -> None:
        try:
            self.conn.execute("insert into Trades (user1_id, user1_cards, user2_id, user2_cards) "
                              "values (?, ?, ?, ?)", (user1_id, user1_cards, user2_id, user2_cards))
        except Exception as err:
            print("ERROR:", err)
            self.conn.rollback()
        else:
            self.conn.commit()

    def __check_trade_exists(self, user1_id: int, user1_cards: List[int], user2_id: int,
                             user2_cards: List[int]) -> bool:
        return len(self.conn.execute(
            "select 1 from Trades where user1_id = ? and user1_cards = ? and user2_id = ? and user2_cards = ? limit 1",
            (user1_id, user1_cards, user2_id, user2_cards)).fetchall()) > 0

    def __add_trade_to_user(self, user_id: int, trade_id: int):
        u: User = self.get_user_from_id(user_id)
        new_user_trades: List[int] = list(u.trades)
        new_user_trades.append(trade_id)
        self.conn.execute("update Users set trades = ? where id = ?", (new_user_trades, user_id))
        self.conn.commit()

    def check_valid_trade(self, user1_id: int, user1_cards: Tuple[int], user2_id: int, user2_cards: Tuple[int]) -> bool:
        return check_user_has_cards(self.get_user_from_id(user1_id).cards, user1_cards) and \
               check_user_has_cards(self.get_user_from_id(user2_id).cards, user2_cards)

    def create_trade(self, user1_id: int, user1_cards: List[int], user2_id: int, user2_cards: List[int]):
        if self.check_valid_trade(user1_id, tuple(user1_cards), user2_id, tuple(user2_cards)):
            if not self.__check_trade_exists(user1_id, user1_cards, user2_id, user2_cards):
                self.__add_trade(user1_id, user1_cards, user2_id, user2_cards)
                new_trade: Trade = self.get_trade_from_values(user1_id, user1_cards, user2_id, user2_cards)
                self.__add_trade_to_user(user1_id, new_trade.id)
                self.__add_trade_to_user(user2_id, new_trade.id)

    def __remove_trade_from_user(self, user_id: int, trade_id: int):
        user_trades: List[int] = list(self.get_user_from_id(user_id).trades)
        user_trades.remove(trade_id)
        self.conn.execute("update Users set trades = ? where id = ?", (user_trades, user_id))
        self.conn.commit()

    def __delete_trade(self, trade_id: int):
        self.conn.execute("delete from Trades where id = ?", (trade_id,))
        self.conn.commit()

    def delete_trade(self, trade_id: int):
        t: Trade = self.get_trade_from_id(trade_id)
        self.__remove_trade_from_user(t.user1_id, trade_id)
        self.__remove_trade_from_user(t.user2_id, trade_id)
        self.__delete_trade(trade_id)

    def add_card_to_user(self, user_id: int, card_id: int):
        u: User = self.get_user_from_id(user_id)
        new_user_cards: List[int] = list(u.cards)
        new_user_cards.append(card_id)
        self.conn.execute("update Users set cards = ? where id = ?", (new_user_cards, user_id))
        self.conn.commit()

    def remove_card_from_user(self, user_id, card_id):
        user_cards: List[int] = list(self.get_user_from_id(user_id).cards)
        user_cards.remove(card_id)
        self.conn.execute("update Users set cards = ? where id = ?", (user_cards, user_id))
        self.conn.commit()

    def do_trade(self, trade_id: int):
        t: Trade = self.get_trade_from_id(trade_id)
        if self.check_valid_trade(t.user1_id, t.user1_cards, t.user2_id, t.user2_cards):
            self.delete_trade(trade_id)
            for card in t.user1_cards:
                self.remove_card_from_user(t.user1_id, card)
                self.add_card_to_user(t.user2_id, card)

            for card in t.user2_cards:
                self.remove_card_from_user(t.user2_id, card)
                self.add_card_to_user(t.user1_id, card)


def load_database(db_loc: str, schema_loc: str) -> None:
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
        # print(qe.get_user_from_id(1))
        # print(qe.get_user_from_id(2))
        qe.do_trade(1)
        # print(qe.get_user_from_id(1))
        # print(qe.get_user_from_id(2))
        print(qe.get_all_card_ids())
        print(qe.get_all_cards())
