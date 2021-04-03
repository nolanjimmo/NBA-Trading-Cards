create table if not exists Players (
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
    blockspg real not null
);

create table if not exists Users (
    id integer primary key,
    name text not null,
    cards text not null,
    trades text not null
);

create table if not exists Trades (
    id integer primary key,
    user1_id integer not null references Users,
    user1_players text not null,
    user2_id integer not null references Users,
    user2_players text not null
);