from celery import Celery
from celery.schedules import crontab
from requests import get
import sqlite3

from local_settings import GOOGLE_URL, GOOGLE_API_KEY, REDIS_URL, DB_LOCATION

app = Celery("auckland_traffic")
app.conf.update(
    CELERY_TIMEZONE="Pacific/Auckland",
    BROKER_URL=REDIS_URL,
    CELERY_TASK_SERIALIZER="json",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERYBEAT_SCHEDULE={
        "fetch_duration": {
            "task": "auckland_traffic.fetch_duration",
            "schedule": crontab(minute="*"),
            "options": {
                "expires": 30,
                "priority": 0,
            }
        }
    }
)

CREATE_TABLE = """
CREATE table fetch_result (
    ID INTEGER PRIMARY KEY ASC,
    CREATED_AT DATATIME DEFAULT (datetime('now', 'localtime')),
    from TEXT,
    to TEXT,
    status TEXT
);
"""
INSERT_SQL = """
    insert into fetch_result(id, created_at, from, to, status)
    values (NULL, DATETIME('now'),?,?,?);
"""


@app.task(name="auckland_traffic.fetch_duration")
def fetch_duration():
    params = {
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "region": "nz",
        "units": "metric",
        "origins": "60 stanhope road, auckland",
        "destinations": "victoria street car park",
    }
    ret = get(GOOGLE_URL, params=params)
    if ret.ok:
        status = ret.json()["rows"]["elements"][0]
        with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
            c = sqlite_conn.cursor()
            hey = c.execute(INSERT_SQL, ("home", "city", status))
            print hey
            print status
            sqlite_conn.commit()


if __name__ == "__main__":
    fetch_duration()
