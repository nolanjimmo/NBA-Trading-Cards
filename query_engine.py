import sqlite3
import csv
from typing import List


def load_database(connection_str: str) -> None:
    conn: sqlite3.Connection = sqlite3.connect(connection_str)

    try:
        conn.execute("drop table Players")
        conn.execute("drop table Users")
        conn.execute("drop table Trades")
    except sqlite3.OperationalError as err:
        print("table does not exist", err)

    conn.execute("""
    create table Players (
    id integer primary key,
    name text not null,
    team text not null,
    pos text not null,
    age real not null,
    gp integer not null,
    mpg real not null,
    fta integer not null,
    ft_pct real not null,
    two_pa integer not null,
    two_p_pct real not null,
    three_pa integer not null,
    three_p_pct real not null,
    shooting_pct real not null,
    ppointspg real not null,
    reboundspg real not null,
    assistspg real not null,
    stealspg real not null,
    blockspg real not null)
    """)

    conn.execute("""
    create table Users (
    id integer primary key,
    name text not null,
    cards text not null,
    trades text not null)
    """)

    conn.execute("""
    create table Trades (
    id integer primary key,
    user1_id integer not null references Users,
    user1_players text not null,
    user2_id integer not null references Users,
    user2_players text not null)
    """)

    with open("NBAdata.csv", 'r') as players_file:
        players = csv.DictReader(players_file)
        for player in players:
            player_data: List[str] = []
            for key, value in player.items():
                if key == "FULL NAME" or \
                        key == "TEAM" or \
                        key == "POS":
                    value = value.replace("'", "''")
                    player_data.append(f'\'{value}\'')
                else:
                    player_data.append(value)
            conn.execute(f"""
            insert into Players (
                name, team, pos, age, gp, mpg, fta, ft_pct, two_pa, two_p_pct, three_pa, three_p_pct, 
                shooting_pct, ppointspg, reboundspg, assistspg, stealspg, blockspg)
            values ({", ".join(player_data)})
            """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    load_database("trading_card_data.db")
    conn = sqlite3.connect("trading_card_data.db")
    print(conn.execute("select * from Players limit 5").fetchall())
