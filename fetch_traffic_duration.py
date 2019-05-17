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
    insert into fetch_result(ID, Timestamp, Origin, Destination, Distance, Duration)
    values (NULL, DATETIME('now'),?,?,?,?);
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
        status = ret.json()["rows"][0]["elements"][0]
        distance = status["distance"]["value"]
        duration = status["duration"]["value"]
        with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
            c = sqlite_conn.cursor()
            c.execute(INSERT_SQL, ("home", "city", distance, duration))
            print status["distance"]["text"], status["duration"]["text"]
            sqlite_conn.commit()


if __name__ == "__main__":
    fetch_duration()
