import json

from tasks import google_trace, bing_trace, address_suggest
from tasks import fetch_address, fetch_route, fetch_trace


def subscribe(request, *args, **kwargs):
    request.ws.send(json.dumps({
        'type': 'SUBSCRIBE_SUCCESS',
        'data': [],  # fetch_all("1563404375"),
    }))


def unsubscribe(request, *args, **kwargs):
    request.on_close()


def trace_data(request, start, stop, method):
    google_trace.delay(
        start, stop, method,
        address=request.ws.handler.client_address,
        success_constant="FETCH_TRACE_DATA_SUCCESS",
        fail_constant="FETCH_TRACE_DATA_FAIL",
    )
