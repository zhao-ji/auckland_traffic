#!/usr/bin/env python
# utf-8

from collections import OrderedDict
import json
from pprint import pprint

from geventwebsocket import Resource
from geventwebsocket import WebSocketServer, WebSocketApplication

from tasks import google_trace, bing_trace, address_suggest
from tasks import fetch_address, fetch_route, fetch_trace


class TrafficHandler(WebSocketApplication):

    def on_open(self, *args, **kwargs):
        print 'open the connection'

    def on_close(self, *args, **kwargs):
        print "delete the connection!"

    def on_message(self, message):
        if message is None:
            return

        message = json.loads(message)
        # turn below one into route

        # global websocket action
        if message['type'] == 'SUBSCRIBE':
            self.ws.send(json.dumps({
                'type': 'SUBSCRIBE_SUCCESS',
                'data': [],  # fetch_all("1563404375"),
            }))
        elif message['type'] == 'UNSUBSCRIBE':
            self.on_close()

        # for home page
        elif message['type'] == 'FETCH_TRAFFIC_DATA_TRY':
            self.ws.send(json.dumps({
                'type': 'MESSAGE',
                'data': [],  # fetch( message["origin"], message["destination"], message["from"], message["to"],),
            }))

        # for trace page
        elif message['type'] == 'FETCH_TRACE_DATA_TRY':
            google_trace.delay(
                message["start"], message["stop"], message["method"],
                address=self.ws.handler.client_address,
                success_constant="FETCH_TRACE_DATA_SUCCESS",
                fail_constant="FETCH_TRACE_DATA_FAIL",
            )
        elif message['type'] == 'FETCH_BING_TRACE_DATA_TRY':
            bing_trace.delay(
                message["start"], message["stop"], message["method"],
                address=self.ws.handler.client_address,
                success_constant="FETCH_BING_TRACE_DATA_SUCCESS",
                fail_constant="FETCH_BING_TRACE_DATA_FAIL",
            )
        elif message['type'] == 'FETCH_ADDRESS_SUGGESTIONS_TRY':
            address_suggest.delay(
                message["text"],
                address=self.ws.handler.client_address,
                success_constant="FETCH_ADDRESS_SUGGESTIONS_SUCCESS",
                fail_constant="FETCH_ADDRESS_SUGGESTIONS_FAIL",
            )

        # for edit page
        elif message['type'] == 'FETCH_ADDRESS_TRY':
            fetch_address.delay(
                address=self.ws.handler.client_address,
                success_constant="FETCH_ADDRESS_SUCCESS",
                fail_constant="FETCH_ADDRESS_FAIL",
            )
        elif message['type'] == 'FETCH_ROUTE_TRY':
            fetch_route.delay(
                address=self.ws.handler.client_address,
                success_constant="FETCH_ROUTE_SUCCESS",
                fail_constant="FETCH_ROUTE_FAIL",
            )
        elif message['type'] == 'FETCH_TRACE_TRY':
            fetch_trace.delay(
                message["route_id"],
                address=self.ws.handler.client_address,
                success_constant="FETCH_TRACE_SUCCESS",
                fail_constant="FETCH_TRACE_FAIL",
            )

        # reply from celery
        elif message['type'] == 'BROADCAST':
            self.broadcast(message)
        elif message['type'] == 'REPLY':
            self.reply(message)

        # error action handler
        else:
            pprint(message)

    def broadcast(self, message):
        for addr, client in self.ws.handler.server.clients.iteritems():
            pprint(addr)
            pprint(client.address)
            client.ws.send(json.dumps({
                'type': 'MESSAGE',
                'data': message['msg_data'],
            }))

    def reply(self, message):
        if "address" not in message:
            print "message body error"
            return

        address = message["address"]

        for addr, client in self.ws.handler.server.clients.iteritems():
            if addr[0] == address[0] and addr[1] == address[1]:
                client.ws.send(json.dumps({
                    'type': message["data_type"],
                    'data': message['data'],
                }))


if __name__ == "__main__":
    print "Listen on 127.0.0.1:8001..."
    WebSocketServer(
        ('127.0.0.1', 8001),
        Resource(OrderedDict([
            ("/", TrafficHandler),
        ])),
        debug=True,
    ).serve_forever()
