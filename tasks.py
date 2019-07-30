#!/usr/bin/env python
# utf-8

from json import dumps

from celery import Celery
from celery.schedules import crontab
from requests import get
from websocket import create_connection

from local_settings import GOOGLE_URL, GOOGLE_API_KEY, REDIS_URL
from local_settings import ORIGIN_ADDRESS_LIST, DESTINATION_ADDRESS_LIST
from local_settings import ORIGIN_LABEL_LIST, DESTINATION_LABEL_LIST
from local_settings import LOCAL_WEBSOCKET_SERVER

from operate import multi_insert

app = Celery("tasks")
app.conf.update(
    CELERY_TIMEZONE="Pacific/Auckland",
    BROKER_URL=REDIS_URL,
    CELERY_TASK_SERIALIZER="json",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERY_RESULT_BACKEND=("db+sqlite:////var/lib/sqlite3/"
                           "auckland_traffic_celery_result_db"),
    CELERYBEAT_SCHEDULE_FILENAME="/tmp/celerybeat_schedule",
    CELERYBEAT_SCHEDULE={
        "fetch_duration": {
            "task": "tasks.fetch_duration",
            "schedule": crontab(minute="*/3"),
            "options": {
                "expires": 30,
                "priority": 0,
            }
        }
    }
)


@app.task(name="auckland_traffic.fetch_duration")
def fetch_duration():
    params = {
        "departure_time": "now",
        "destinations": "|".join(DESTINATION_ADDRESS_LIST),
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "origins": "|".join(ORIGIN_ADDRESS_LIST),
        "region": "nz",
        "units": "metric",
        "traffic_model": "best_guess",
    }
    ret = get(GOOGLE_URL, params=params, timeout=(2, 5))
    if ret.ok:
        data = ret.json()
        if data["status"] != "OK":
            print "Wired response: " + data["status"]
            return

    insert_list = []
    for origin_index, origin in enumerate(ORIGIN_LABEL_LIST):
        for destination_index, destination in enumerate(DESTINATION_LABEL_LIST):
            item = data["rows"][origin_index]["elements"][destination_index]
            distance = item["distance"]["value"]
            duration = item["duration_in_traffic"]["value"]
            print " ".join([
                origin, "=>", destination,
                item["distance"]["text"],
                item["duration_in_traffic"]["text"]
            ])
            insert_list.append((origin, destination, distance, duration))

    multi_insert(insert_list)

    websocket_client = create_connection(LOCAL_WEBSOCKET_SERVER)
    websocket_client.send(dumps({
        "msg_type": "MESSAGE",
        "msg_data": insert_list,
    }))
    websocket_client.close()


if __name__ == "__main__":
    fetch_duration()
