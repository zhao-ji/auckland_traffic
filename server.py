#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request, jsonify

from models import Address, Route, Trace

app = Flask(__name__)


@app.route("/address", methods=['GET'])
def get_address():
    all_address = Address.select()
    return jsonify([address.serialize() for address in all_address])


@app.route("/address", methods=['PUT'])
def update_address():
    address_id = request.args.get('address_id')
    content = request.json
    query = Address.update(**content).where(Address.id == address_id)
    query.execute()
    all_address = Address.select()
    return jsonify([address.serialize() for address in all_address])


@app.route("/address", methods=['DELETE'])
def delete_address():
    address_id = request.args.get('address_id')
    thatone = Address.get(Address.id == address_id)
    thatone.delete_instance()
    all_address = Address.select()
    return jsonify([address.serialize() for address in all_address])


@app.route("/address", methods=['POST'])
def create_address():
    content = request.json
    Address.create(
        address=content["address"],
        alias=content.get("alias", ""),
        latitude=content.get("latitude", ""),
        longitude=content.get("longitude", ""),
    )
    all_address = Address.select()
    return jsonify([address.serialize() for address in all_address])


@app.route("/route", methods=['GET'])
def get_route():
    address_id = request.args.get('address_id')
    all_route = Route.select()
    if address_id:
        all_route = all_route.where((Route.start == address_id) | (Route.stop == address_id))
    return jsonify([route.serialize() for route in all_route])


@app.route("/route", methods=['POST'])
def create_route():
    content = request.json
    Route.create(
        start=content["start"],
        stop=content["stop"],
        method=content["method"],
        cron=content.get("cron", ""),
    )
    all_route = Route.select()
    return jsonify([route.serialize() for route in all_route])


@app.route("/route", methods=['PUT'])
def update_route():
    route_id = request.args.get('route_id')
    content = request.json
    query = Route.update(**content).where(Route.id == route_id)
    query.execute()
    all_route = Route.select()
    return jsonify([route.serialize() for route in all_route])


@app.route("/route", methods=['DELETE'])
def delete_route():
    route_id = request.args.get('route_id')
    thatone = Route.get(Route.id == route_id)
    thatone.delete_instance()
    all_route = Route.select()
    return jsonify([route.serialize() for route in all_route])


@app.route("/trace", methods=['GET'])
def get_trace():
    route_id = request.args.get('route_id')
    all_trace = Trace.select().where(Trace.route_id == route_id)
    return jsonify([trace.serialize() for trace in all_trace])


@app.route("/trace", methods=['DELETE'])
def delete_trace():
    trace_id = request.args.get('trace_id')
    route_id = request.args.get('route_id')
    thatone = Trace.get(Trace.id == trace_id)
    thatone.delete_instance()
    all_trace = Trace.select().where(Trace.route_id == route_id)
    return jsonify([trace.serialize() for trace in all_trace])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8003")
