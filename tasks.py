#!/usr/bin/env python
# utf-8

from functools import wraps
from json import dumps
from pprint import pprint

from celery import Celery
from celery import shared_task
from celery.schedules import crontab
from websocket import create_connection

from local_settings import REDIS_URL
from local_settings import LOCAL_WEBSOCKET_SERVER

app = Celery("tasks")
app.conf.update(
    CELERY_TIMEZONE="Pacific/Auckland",
    BROKER_URL=REDIS_URL,
    CELERY_TASK_SERIALIZER="json",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERYBEAT_SCHEDULE_FILENAME="/tmp/celerybeat_schedule",
    CELERYBEAT_SCHEDULE={
        "fetch_routes": {
            "task": "fetch_routes",
            "schedule": crontab(minute="*/15"),
            "options": {
                "expires": 60,
                "priority": 0,
            }
        }
    }
)


#####################################
# utils used to send result back to server
#####################################
def ws_send(data, message_type="", address=None):
    """Create connection to websocket server, send task run result back to user
    """
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
    """Websocket server views wrap
    """
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


#####################################
# schedule tasks
#####################################
@shared_task
def fetch_routes():
    from models import Route
    for route in Route.select():
        route.check_and_trace()


#####################################
# websocket server views
#####################################
@shared_task
@websocket_wrap
def google_trace(start, stop, method):
    from apis import google_trace as trace
    return trace(start, stop, method)


@shared_task
@websocket_wrap
def bing_trace(start, stop, method):
    from apis import bing_trace as trace
    return trace(start, stop, method)


@shared_task
@websocket_wrap
def address_suggest(input_text):
    from apis import address_suggest as fetch
    return fetch(input_text)
