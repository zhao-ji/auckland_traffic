#!/usr/bin/env python
# utf-8

from collections import OrderedDict
import gevent
from pprint import pprint

from geventwebsocket import Resource, WebSocketError
from geventwebsocket import WebSocketServer, WebSocketApplication
from redis import StrictRedis


class TrafficHandler(WebSocketApplication):
    def __init__(self, ws):
        self.ws = ws

    def handle(self):
        self.on_open()
        ws_worker = gevent.spawn(self.listen_websocket)
        redis_worker = gevent.spawn(self.listen_redis_channel)
        gevent.joinall([ws_worker, redis_worker])

    def listen_redis_channel(self):
        for info in self.channel.listen():
            if info["channel"] == "traffic" and info["type"] == "message":
                pprint(info)
                self.ws.send(info["data"])

    def listen_websocket(self):
        while True:
            try:
                message = self.ws.receive()
                message = message.strip("\n")
                if message == "UNSUBSCRIBE":
                    self.on_close()
                    break
            except WebSocketError:
                self.on_close()
                break

    def on_open(self):
        self.channel = queue.pubsub(ignore_subscribe_messages=True)
        self.channel.subscribe("traffic")

    def on_close(self):
        self.channel.unsubscribe()
        self.channel.reset()


if __name__ == "__main__":
    queue = StrictRedis(host="localhost", port="6379")
    print "Listen on 0.0.0.0:8005..."
    WebSocketServer(
        ('0.0.0.0', 8005),
        Resource(OrderedDict([
            ("/", TrafficHandler),
        ])),
        debug=True,
    ).serve_forever()
