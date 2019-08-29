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

from models import Address, Route, Trace
from third_party_apis import google_trace as _google_trace
from third_party_apis import bing_trace as _bing_trace
from third_party_apis import address_suggest as _address_suggest

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
    for route in Route.select():
        route.check_and_trace()


#####################################
# websocket server views for trace page
#####################################
@shared_task
@websocket_wrap
def google_trace(start, stop, method):
    return _google_trace(start, stop, method)


@shared_task
@websocket_wrap
def bing_trace(start, stop, method):
    return _bing_trace(start, stop, method)


@shared_task
@websocket_wrap
def address_suggest(input_text):
    return _address_suggest(input_text)


#####################################
# websocket server views for trace page
#####################################
@shared_task
@websocket_wrap
def fetch_address():
    all_address = Address.select()
    return [address.serialize() for address in all_address]


@shared_task
@websocket_wrap
def create_address(address, alias="", latitude="", longitude=""):
    Address.create(address=address, alias=alias, latitude=latitude, longitude=longitude)
    return [_address.serialize() for _address in Address.select()]


@shared_task
@websocket_wrap
def delete_address(address_id):
    address = Address.get(id == address_id)
    address.delete_instance()
    return [_address.serialize() for _address in Address.select()]


@shared_task
@websocket_wrap
def update_address(address_id, address_str=None, alias=None, latitude=None, longitude=None):
    address = Address.get(id == address_id)
    if address_str:
        address.address = address_str
    elif alias:
        address.alias = alias
    elif latitude:
        address.latitude = latitude
    elif longitude:
        address.longitude = longitude
    address.save()
    return [_address.serialize() for _address in Address.select()]


@shared_task
@websocket_wrap
def fetch_route():
    all_route = Route.select()
    return [
        route.serialize()
        for route in all_route
    ]


@shared_task
@websocket_wrap
def fetch_trace(route_id):
    all_trace = Trace.select().where(Trace.route_id==route_id)
    return [trace.serialize() for trace in all_trace]


@shared_task
@websocket_wrap
def delete_trace(trace_id):
    trace = Trace.get(id == trace_id)
    trace.delete_instance()
    return [_trace.serialize() for _trace in Trace.select()]
