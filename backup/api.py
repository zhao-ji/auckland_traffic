#!/usr/bin/env python
# coding: utf8

from datetime import datetime

from flask import Flask, request, abort, jsonify

import sqlite3

from local_settings import DB_LOCATION


app = Flask(__name__)
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


@app.route("/", methods=['GET'])
def query():
    origin = request.args.get("origin", "home")
    destination = request.args.get("destination", "city")
    time_from = request.args.get("time_from", "")
    time_to = request.args.get("time_to", "now")
    if not time_from or not time_from.isdigit():
        abort(400)

    time_from = datetime.utcfromtimestamp(int(time_from))
    if time_to == "now":
        time_to = datetime.now()

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.execute(QUERY_SQL, (origin, destination, time_from, time_to))
        rows = c.fetchall()

    return jsonify(slim_dataset(rows))


@app.route("/all", methods=['GET'])
def query_all_origins_and_destinations():
    time_from = request.args.get("time_from", "")
    time_to = request.args.get("time_to", "now")
    if not time_from or not time_from.isdigit():
        abort(400)

    time_from = datetime.utcfromtimestamp(int(time_from))
    if time_to == "now":
        time_to = datetime.now()

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.execute(QUERY_ALL_SQL, (time_from, time_to))
        rows = c.fetchall()

    ret = {
        "home": {},
        # "office": {}
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

    return jsonify(ret)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001)
