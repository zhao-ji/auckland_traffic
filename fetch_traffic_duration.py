from celery import Celery
from celery.schedules import crontab
from requests import get
import sqlite3

from local_settings import GOOGLE_URL, GOOGLE_API_KEY, REDIS_URL, DB_LOCATION
from local_settings import HOME, OFFICE
from local_settings import SCHOOL, CITY, DOMINION_ROAD, KOREAN_SHOP, BARBER_SHOP

app = Celery("auckland_traffic")
app.conf.update(
    CELERY_TIMEZONE="Pacific/Auckland",
    BROKER_URL=REDIS_URL,
    CELERY_TASK_SERIALIZER="json",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERYBEAT_SCHEDULE={
        "fetch_duration": {
            "task": "auckland_traffic.fetch_duration",
            "schedule": crontab(minute="*/2"),
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
    insert into
    fetch_result(ID, Timestamp, Origin, Destination, Distance, Duration)
    values (NULL, DATETIME('now'),?,?,?,?);
"""


def ping():
    params = {
        "departure_time": "now",
        "destinations": "|".join([SCHOOL, CITY, DOMINION_ROAD, KOREAN_SHOP, BARBER_SHOP]),
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "origins": "|".join([HOME, OFFICE]),
        "region": "nz",
        "units": "metric",
        "traffic_model": "best_guess",
    }
    ret = get(GOOGLE_URL, params=params, timeout=(2,5))
    if ret.ok:
        data = ret.json()
        for i in data["rows"]:
            for j in i["elements"]:
                yield j


@app.task(name="auckland_traffic.fetch_duration")
def fetch_duration():
    result = ping()
    insert_list = []

    for origin in ["home", "office"]:
        for destination in ["school", "city", "dominion_road", "korean_shop", "barber_shop"]:
            data = result.next()
            distance = data["distance"]["value"]
            duration = data["duration_in_traffic"]["value"]
            print " ".join([origin, "=>", destination, data["distance"]["text"], data["duration_in_traffic"]["text"]])
            insert_list.append((origin, destination, distance, duration))

    with sqlite3.connect(DB_LOCATION, timeout=100) as sqlite_conn:
        c = sqlite_conn.cursor()
        c.executemany(INSERT_SQL, insert_list)
        sqlite_conn.commit()


if __name__ == "__main__":
    fetch_duration()
