import os
import sqlite3
import csv
import json
from dataclasses import dataclass
from typing import Tuple, List

db_filename = "trading_card_data.db"
schema_filename = "trading_card_schema.sql"


def parse_ids(ids: str) -> Tuple[int]:
    return tuple([int(id) for id in ids.split(",")])


def json_list_adapter(l: List) -> bytes:
    return json.dumps(l).encode("utf-8")


def json_list_converter(data: bytes) -> List[int]:
    return json.loads(data.decode("utf-8"))


@dataclass
class Player:
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


def create_player(
        player_data: Tuple[
            int, str, str, str, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int
        ]) -> Player:
    return Player(
        player_data[0],
        player_data[1],
        player_data[2],
        player_data[3],
        player_data[4],
        player_data[5],
        player_data[6],
        player_data[7],
        player_data[8],
        player_data[9],
        player_data[10],
        player_data[11],
        player_data[12],
        player_data[13],
        player_data[14],
        player_data[15],
        player_data[16],
        player_data[17],
        player_data[18])


@dataclass
class Trade:
    id: int
    user1_id: int
    user1_players: Tuple[int]
    user2_id: int
    user2_players: Tuple[int]


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


class QueryEngine:
    conn: sqlite3.Connection

    def __init__(self, db_loc: str):
        self.conn = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)

    def get_player_from_id(self, player_id: int) -> Player:
        output = self.conn.execute("select * from Players where id = ?", (player_id,)).fetchone()
        if output is None:
            raise Exception("no player with id", player_id)
        return create_player(output)

    def get_trade_from_id(self, trade_id: int) -> Trade:
        output = self.conn.execute("select * from Trades where id = ?", (trade_id,)).fetchone()
        if output is None:
            raise Exception("no trade with id", trade_id)
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

    # TODO: Write functions to add users and trades


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

            with open("NBAdata.csv", 'r') as players_file:
                players = csv.DictReader(players_file)

                sql = """insert into Players (name, team, pos, age, gp, mpg, fta, ft_pct, two_pa, two_p_pct, three_pa, three_p_pct, shooting_pct, ppointspg, reboundspg, assistspg, stealspg, blockspg)
                values (:NAME, :TEAM, :POS, :AGE, :GP, :MPG, :FTA, :FTpct, :2PA, :2Ppct, :3PA, :3Ppct, :SHOOTINGpct, :PPOINTSPG, :REBOUNDSPG, :ASSISTSPG, :STEALSPG, :BLOCKSPG)
                """

                cursor = conn.cursor()
                cursor.executemany(sql, players)

        conn.commit()


def load_test_data(db_loc: str) -> None:
    conn: sqlite3.Connection

    with sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        sqlite3.register_adapter(list, json_list_adapter)
        sqlite3.register_converter("json", json_list_converter)
        # TODO: Create csv files with test data for Users and Trades to make this easier and more robust
        conn.execute("insert into Users (name, cards, trades) values ('chuck', ?, ?), ('nolan', ?, ?)", ([1, 2, 3], [1], [4], [1]))
        conn.execute("insert into Trades (user1_id, user1_players, user2_id, user2_players) values (1, ?, 2, ?)", ([1], [4]))
        conn.commit()


if __name__ == "__main__":
    if os.path.exists(db_filename):
        os.remove(db_filename)
    load_database(db_filename, schema_filename)
    load_test_data(db_filename)
    qe = QueryEngine(db_filename)
    user1 = qe.get_user_from_id(1)
    user2 = qe.get_user_from_username('chuck')
    print(user1, user2)
    print(qe.get_player_from_id(55))
    print(qe.get_trade_from_id(1))
