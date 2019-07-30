#!/usr/bin/env python
# utf-8

from datetime import datetime

import sqlite3

from local_settings import DB_LOCATION

CREATE_TABLE = """
CREATE TABLE fetch_result (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    Origin TEXT,
    Destination TEXT,
    Duration INTEGER,
    Distance INTEGER
);
"""
INSERT_SQL = """
    insert into
    fetch_result(ID, Timestamp, Origin, Destination, Distance, Duration)
    values (NULL, DATETIME('now'),?,?,?,?);
"""
QUERY_SQL = """
    select Timestamp, Duration from fetch_result
    where Origin = ? and Destination = ? and Timestamp >= ? and Timestamp <= ? ;
"""
QUERY_ALL_SQL = """
    select Origin, Destination, Timestamp, Duration from fetch_result
    where Timestamp >= ? and Timestamp <= ? ;
"""


def slim_dataset(rows, threshold=410, step_base=100):
    # we don't want too many points in the chart, 100 points is enough I think
    if len(rows) > threshold:
        step = len(rows) / step_base
        rows = rows[::step]

    return rows


def fetch_all(time_from, time_to="now"):
    if not time_from or not time_from.isdigit():
        return []

    time_from = datetime.utcfromtimestamp(int(time_from))
    if time_to == "now":
        time_to = datetime.now()

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.execute(QUERY_ALL_SQL, (time_from, time_to))
        rows = c.fetchall()

    ret = {
        "home": {},
    }
    for item in rows:
        if item[0] not in ["home", ]:
            continue
        if item[1] not in ret[item[0]]:
            ret[item[0]][item[1]] = [[item[2], item[3]], ]
        else:
            ret[item[0]][item[1]].append([item[2], item[3]])

    for origin in ret:
        for destination in ret[origin]:
            ret[origin][destination] = slim_dataset(ret[origin][destination])

    return ret


def fetch(origin, destination, time_from, time_to):
    # fetch traffic data by origin, destination, from, to
    if not time_from or not time_from.isdigit():
        return []

    time_from = datetime.utcfromtimestamp(int(time_from))
    if time_to == "now":
        time_to = datetime.now()

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.execute(QUERY_SQL, (origin, destination, time_from, time_to))
        rows = c.fetchall()

    return slim_dataset(rows)


def multi_insert(data_list):
    # insert the traffic data into database
    if not data_list:
        return
    if not isinstance(data_list, "list"):
        return

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.executemany(INSERT_SQL, data_list)
        sqlite_conn.commit()
