
--------------------------------------------------------------------------------
-- Aktiviteter på karanteneforum

CREATE TABLE IF NOT EXISTS Aktiviteter (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	TEXT TEXT NOT NULL,
	USER TEXT NOT NULL,
	TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--------------------------------------------------------------------------------
-- Meldinger sendt på karanteneforum

CREATE TABLE IF NOT EXISTS Meldinger (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	MSG TEXT NOT NULL,
	USER TEXT NOT NULL,
	TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--------------------------------------------------------------------------------
-- Status

CREATE TABLE IF NOT EXISTS Status (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	MSG TEXT NOT NULL,
	USER TEXT NOT NULL,
	TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--------------------------------------------------------------------------------
-- Brukerrettigheter

CREATE TABLE IF NOT EXISTS Rettigheter (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	USER TEXT NOT NULL UNIQUE,
	AGENDA INTEGER DEFAULT 0,
	KVISSMASTER INTEGER DEFAULT 0,
	STATUS INTEGER DEFAULT 0,
	TILGANGER INTEGER DEFAULT 0,
	BDFL INTEGER DEFAULT 0,
	TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--------------------------------------------------------------------------------
-- Live-kviss
-- Live-kvisser holdt av en kvissmaster

CREATE TABLE IF NOT EXISTS LiveKviss (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	CREATOR TEXT NOT NULL,
	NAME TEXT NOT NULL,
	DESCRIPTION TEXT NOT NULL,
	ACTIVE INTEGER DEFAULT 0,
	WINNER TEXT,
	QUESTION INTEGER DEFAULT 0,
	TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
