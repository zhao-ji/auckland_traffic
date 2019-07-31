#!/usr/bin/env python
# utf-8

from collections import OrderedDict
import json
from pprint import pprint

from geventwebsocket import Resource
from geventwebsocket import WebSocketServer, WebSocketApplication

from operate import fetch, fetch_all


class TrafficHandler(WebSocketApplication):

    def on_open(self, *args, **kwargs):
        print 'delete the connection'

    def on_close(self, *args, **kwargs):
        print "something come!"

    def fetch_all_data(self):
        self.ws.send(json.dumps({
            'msg_type': 'MESSAGE',
            'message': fetch_all(),
        }))

    def fetch_data(self, message):
        self.ws.send(json.dumps({
            'msg_type': 'MESSAGE',
            'message': fetch(
                message["origin"],
                message["destination"],
                message["from"],
                message["to"],
            ),
        }))

    def on_message(self, message):
        if message is None:
            return

        message = json.loads(message)

        if message['msg_type'] == 'MESSAGE':
            self.broadcast(message)
        elif message['msg_type'] == 'SUBSCRIBE':
            self.fetch_all_data()
        elif message['msg_type'] == 'UNSUBSCRIBE':
            self.on_close()
        elif message['msg_type'] == 'FETCH':
            self.fetch_data(message)
        else:
            pprint(message)

    def broadcast(self, message):
        for addr, client in self.ws.handler.server.clients.iteritems():
            pprint(addr)
            pprint(client.address)
            client.ws.send(json.dumps({
                'msg_type': 'MESSAGE',
                'message': message['msg_data'],
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
