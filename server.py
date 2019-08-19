#!/usr/bin/env python
# utf-8

from collections import OrderedDict
import json
from pprint import pprint

from geventwebsocket import Resource
from geventwebsocket import WebSocketServer, WebSocketApplication

from operate import fetch, fetch_all
from tasks import trace


class TrafficHandler(WebSocketApplication):

    def on_open(self, *args, **kwargs):
        print 'open the connection'

    def on_close(self, *args, **kwargs):
        print "delete the connection!"

    def fetch_all_data(self):
        self.ws.send(json.dumps({
            'type': 'SUBSCRIBE_SUCCESS',
            'data': fetch_all("1563404375"),
        }))

    def fetch_data(self, message):
        self.ws.send(json.dumps({
            'type': 'MESSAGE',
            'data': fetch(
                message["origin"],
                message["destination"],
                message["from"],
                message["to"],
            ),
        }))

    def trace(self, message):
        print self.ws.handler.client_address
        trace.delay(message["start"], message["stop"], message["method"], self.ws.handler.client_address)

    def on_message(self, message):
        if message is None:
            return

        message = json.loads(message)
        # turn below one into route

        if message['type'] == 'MESSAGE':
            self.broadcast(message)
        elif message['type'] == 'SUBSCRIBE':
            self.fetch_all_data()
        elif message['type'] == 'UNSUBSCRIBE':
            self.on_close()
        elif message['type'] == 'FETCH_TRAFFIC_DATA_TRY':
            self.fetch_data(message)
        elif message['type'] == 'FETCH_TRACE_DATA_TRY':
            self.trace(message)
        elif message['type'] == 'BROADCAST':
            self.broadcast(message)
        elif message['type'] == 'REPLY':
            self.reply(message)
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

        from pprint import pprint
        pprint(message)
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
