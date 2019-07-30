#!/usr/bin/env python
# utf-8

from collections import OrderedDict
import json
from pprint import pprint

from geventwebsocket import Resource
from geventwebsocket import WebSocketServer, WebSocketApplication


class TrafficHandler(WebSocketApplication):

    def on_open(self):
        print "something come!"

    def on_close(self):
        print 'delete the connection'

    def on_message(self, message):
        if message is None:
            return

        message = json.loads(message)

        if message['msg_type'] == 'MESSAGE':
            self.broadcast(message)

    def broadcast(self, message):
        for client in self.ws.handler.server.clients.values():
            pprint(dir(client))
            client.ws.send(json.dumps({
                'msg_type': 'MESSAGE',
                'message': message['msg_data']
            }))


if __name__ == "__main__":
    print("Listen on 0.0.0.0:8005...")
    WebSocketServer(
        ('0.0.0.0', 8005),
        Resource(OrderedDict([
            ("/", TrafficHandler),
        ])),
        debug=True,
    ).serve_forever()
