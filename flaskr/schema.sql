DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS trade;
DROP TABLE IF EXISTS deposit;
DROP TABLE IF EXISTS account;

CREATE TABLE person (
    id SERIAL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE account (
    id SERIAL,
    balance FLOAT NOT NULL,
    person INTEGER NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY (person) REFERENCES person (id)
);

CREATE TABLE deposit (
    id SERIAL,
    person INTEGER NOT NULL,
    value FLOAT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY (person) REFERENCES person (id)
);

CREATE TABLE trade (
    id SERIAL,
    person INTEGER NOT NULL,
    price FLOAT NOT NULL,
    qty INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    -- dir = -1 => BUY 
    -- dir = 1 => SELL
    dir INTEGER NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY (person) REFERENCES person (id)
);