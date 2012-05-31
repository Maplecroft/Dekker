#!/usr/bin/env python 
# -*- coding: iso-8859-15 -*-
from datetime import datetime
from flask import Flask, abort, make_response, request, jsonify
from flask import __version__ as flask_version

import conf
from utils import get_value_at_points, get_buffer_value_at_points

app = Flask(__name__)


@app.route('/buffer')
def buffer_value_at_point():
    """View to get average value in buffer around point."""
    
    rad = request.args.get('radius')
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    tifs = tuple(request.args.getlist('tif[]'))
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'

    if not lon or not lat or not len(tifs):
        abort(400)
    
    start = datetime.now()
    rows, explanation = get_buffer_value_at_points(
        float(rad), [(lon, lat)], tifs, explain=explain)
    values = [
        dict(zip(('gid', 'tif', 'lon', 'lat', 'value'), row)) for row in rows
    ]
    
    result = {
        'result': values,
        'count': len(values),
        'time': (datetime.now() - start).total_seconds(),
    }
    if explanation:
        result['explanation'] = explanation
   
    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.route('/point')
def value_at_point():
    """Get the value at a lon, lat for a given view."""
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    tifs = tuple(request.args.getlist('tif[]'))
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'

    if not lon or not lat or not len(tifs):
        abort(400)

    start = datetime.now()
    rows, explanation = get_value_at_points(
        [(lon, lat)], tifs, explain=explain)
    values = [
        dict(zip(('lon', 'lat', 'view', 'value'), row)) for row in rows
    ]

    result = {
        'result': values,
        'count': len(values),
        'time': (datetime.now() - start).total_seconds(),
    }
    if explanation:
        result['explanation'] = explanation
   
    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.errorhandler(400)
def bad_request(error):
    resp = make_response('lon, lat, and tif are all required parameters', 400)
    resp.headers['Content-Type'] = 'text/plain'
    return resp


if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run()
