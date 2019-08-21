#!/usr/bin/env python
# utf-8

# from datetime import datetime
from functools import wraps
from json import dumps
from pprint import pprint

from celery import Celery
from celery.schedules import crontab
from requests import get
from websocket import create_connection

from local_settings import GOOGLE_URL, GOOGLE_PREDICT_URL, GOOGLE_API_KEY
from local_settings import GOOGLE_GEOCODE_URL
from local_settings import BING_URL, BING_API_KEY
from local_settings import REDIS_URL
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
            "task": "auckland_traffic.fetch_duration",
            "schedule": crontab(minute="0"),
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
    ws_send(insert_list, "MESSAGE")


def ws_send(data, message_type="", address=None):
    websocket_client = create_connection(LOCAL_WEBSOCKET_SERVER)
    if address:
        websocket_client.send(dumps({
            "type": "REPLY",
            "data": data,
            "data_type": message_type,
            "address": address,
        }))
    else:
        websocket_client.send(dumps({
            "type": "BROADCAST",
            "data": data,
            "data_type": message_type,
        }))
    websocket_client.close()


def websocket_wrap(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            assert "address" in kwargs
            address = kwargs.pop("address")
            assert "success_constant" in kwargs
            success_constant = kwargs.pop("success_constant")
            assert "fail_constant" in kwargs
            fail_constant = kwargs.pop("fail_constant")
            data = function(*args, **kwargs)
        except Exception as e:
            pprint(e)
            error_msg = "Ops, something happened!"
            return ws_send(error_msg, fail_constant, address)
        else:
            return ws_send(data, success_constant, address)
    return wrapper


@app.task(name="auckland_traffic.google_trace")
@websocket_wrap
def google_trace(start, stop, method):
    params = {
        "departure_time": "now",
        "key": GOOGLE_API_KEY,
        "mode": method,
        "origins": start,
        "destinations": stop,
        "region": "nz",
        "units": "metric",
        "traffic_model": "best_guess",
    }
    ret = get(GOOGLE_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    assert data["status"] == "OK"

    item = data["rows"][0]["elements"][0]
    distance = item["distance"]["text"]
    if method == "driving":
        duration = item["duration_in_traffic"]["text"]
    else:
        duration = item["duration"]["text"]
    return {"distance": distance, "duration": duration}


@app.task(name="auckland_traffic.bing_trace")
@websocket_wrap
def bing_trace(start, stop, method):
    params = {
        "origins": address_translate(start),
        "destinations": address_translate(stop),
        "travelMode": method,
        # "startTime": datetime.now().strftime('%Y-%m-%dT12:00:00-%H:%M'),
        "key": BING_API_KEY,
    }
    ret = get(BING_URL, params=params, timeout=(2, 5))
    assert ret.ok, "bing fetching error"

    data = ret.json()
    assert data["statusCode"] == 200, "status code is not 200"

    result = data["resourceSets"][0]["resources"][0]["results"][0]
    return {
        "distance": result["travelDistance"],
        "duration": result["travelDuration"],
    }


def address_translate(address_text):
    """
    address_text => latitude, longitude
    """
    params = {
        "key": GOOGLE_API_KEY,
        "address": address_text,
    }
    ret = get(GOOGLE_GEOCODE_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    location = data["results"][0]["geometry"]["location"]
    return "{},{}".format(location["lat"], location["lng"])


@app.task(name="auckland_traffic.address_suggest")
@websocket_wrap
def address_suggest(input_text):
    """
    TODO: use session token
    """
    params = {
        "key": GOOGLE_API_KEY,
        "components": "country:nz",
        "types": "address",
        # "sessiontoken": sessiontoken,
        "input": input_text,
    }
    ret = get(GOOGLE_PREDICT_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    predictions = data["predictions"]
    return [i["description"] for i in predictions]


if __name__ == "__main__":
    # address_suggest("188 carrin", "123456")
    # address_translate("68 stanhope road, auckland")
    bing_trace(
        "60 stanhope road, auckland",
        "188 carrington road, auckland", "driving")
