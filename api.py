#!/usr/bin/env python
# coding: utf8

from json import dumps
from time import strftime
from datetime import datetime

from flask import Flask
from flask import request

import sqlite3

from local_settings import DB_LOCATION

import redis

app = Flask(__name__)
QUERY_SQL = """
    select Timestamp, Duration from fetch_result
    where Origin = ? and Destination = ? and Timestamp >= ? and Timestamp <= ? ;
"""


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

    return dumps(rows)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001)
