import sqlite3
import csv


def load_database(connection_str: str) -> None:
    conn: sqlite3.Connection = sqlite3.connect(connection_str)

    try:
        conn.execute("drop table Players")
        conn.execute("drop table Users")
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

    with open("NBAdata.csv", 'r') as players_file:
        players = csv.DictReader(players_file)
        player_id: int = 0
        for player in players:
            conn.execute("insert into Players values (" +
                         str(player_id) + ", '" +
                         player["FULL NAME"].replace("'", "''") + "', '" +
                         player["TEAM"] + "', '" +
                         player["POS"] + "', " +
                         player["AGE"] + ", " +
                         player["GP"] + ", " +
                         player["MPG"] + ", " +
                         player["FTA"] + ", " +
                         player["FTpct"] + ", " +
                         player["2PA"] + ", " +
                         player["2Ppct"] + ", " +
                         player["3PA"] + ", " +
                         player["3Ppct"] + ", " +
                         player["SHOOTINGpct"] + ", " +
                         player["PPOINTSPG"] + ", " +
                         player["REBOUNDSPG"] + ", " +
                         player["ASSISTSPG"] + ", " +
                         player["STEALSPG"] + ", " +
                         player["BLOCKSPG"] + ")")

            player_id += 1

    conn.commit()
    conn.close()


if __name__ == "__main__":
    load_database("trading_card_data.db")
    conn = sqlite3.connect("trading_card_data.db")
