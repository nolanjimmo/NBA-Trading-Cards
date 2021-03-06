create table if not exists Cards (
    id integer primary key,
    owned integer not null default 0,
    name text not null unique,
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
    blockspg real not null,
    image text not null
);

create table if not exists Users (
    id integer primary key,
    name text not null unique,
    hashed_pass text not null,
    access text not null,
    last_seen timestamp not null,
    cards json,
    trades json
);

create table if not exists Trades (
    id integer primary key,
    user1_id integer not null references Users,
    user1_cards json,
    user1_confirmed integer not null default 0,
    user2_id integer not null references Users,
    user2_cards json,
    user2_confirmed integer not null default 0
);