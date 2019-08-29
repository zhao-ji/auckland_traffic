#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request, jsonify

from models import Address, Route, Trace

app = Flask(__name__)


@app.route("/address", methods=['GET'])
def get_address():
    all_address = Address.select()
    return jsonify([address.serialize() for address in all_address])


@app.route("/route", methods=['GET'])
def get_route():
    all_route = Route.select()
    return jsonify([route.serialize() for route in all_route])


@app.route("/trace", methods=['GET'])
def get_trace():
    route_id = request.args.get('route_id')
    all_trace = Trace.select().where(Trace.route_id == route_id)
    return jsonify([trace.serialize() for trace in all_trace])


@app.route("/address", methods=['DELETE'])
def delete_address():
    id = request.args.get('id')
    Address.delete().where(Address.id == id)


@app.route("/route", methods=['DELETE'])
def delete_route():
    id = request.args.get('id')
    Route.delete().where(Route.id == id)


@app.trace("/trace", methods=['DELETE'])
def delete_trace():
    id = request.args.get('id')
    Trace.delete().where(Trace.id == id)


@app.route("/address", methods=['PUT'])
def update_address():
    id = request.args.get('id')
    content = request.json
    Address.update(**content).where(Address.id == id)


@app.route("/address", methods=['POST'])
def create_address():
    content = request.json
    Address.create(
        address=content["address"],
        alias=content.get("alias", ""),
        latitude=content.get("latitude", ""),
        longitude=content.get("longitude", ""),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8002")
