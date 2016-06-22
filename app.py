#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import re
from datetime import datetime
from flask import Flask, abort, make_response, request, jsonify
from flask import __version__ as flask_version

import conf
from utils import (
    get_value_at_points,
    get_buffer_value_at_point,
    get_point_in_polygon_value,
    get_buffer_value_at_polygon,
    get_buffer_values_at_points,
)

app = Flask(__name__)


@app.route('/pointbuffer')
@app.route('/custombuffer')
def buffer_value_at_point(rad=None, legacy=False):
    """View to get average value in buffer around point."""
    point_id = request.args.get('id') or 999

    try:
        rad = rad or request.args.get('radius')
    except:
        abort(400)

    lon = request.args.get('lon')
    lat = request.args.get('lat')
    raster_table = request.args.get('raster_table')
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'
    fixed = request.args.get('explain', False) == 'true'

    if not lon or not lat or not len(raster_table):
        abort(400)

    start = datetime.now()
    result = {}
    try:
        row, explanation = get_buffer_values_at_points(
            float(rad),
            [(lon, lat, int(point_id))],
            raster_table,
            explain=explain,
            legacy=legacy,
        )
        result = {
            'query': {
                'value': row[0][1],
                'id': row[0][0],
                'raster': raster_table,
            },
            'time': (datetime.now() - start).total_seconds(),
        }
        if explanation:
            result['explanation'] = explanation
    except Exception:
        return abort(400)

    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.route('/buffer')
def legacy_buffer_value_at_point():
    """Backward consistency preservation.  Scored radius used to be
       hard-coded at 25km for all buffer lookups regardless of arguments"""
    return buffer_value_at_point(rad=25, legacy=True)


@app.route('/polygon')
def value_at_polygon():
    point_id = request.args.get('id') or 999
    raster_table = request.args.get('raster_table')
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'
    geom = request.args.get('geom')

    if not geom:
        return jsonify({}, jsonp=jsonp)

    # Check polygon syntax
    rx = re.compile(
        "POLYGON\(\((?P<point>(-?\d+(?:\.\d+)? -?\d+(?:\.\d+)?)(?:, ?)?)+\)\)"
    )
    if not rx.match(geom):
        abort(400)

    start = datetime.now()
    result = {}
    try:
        row, explanation = get_buffer_value_at_polygon(
            point_id,
            geom,
            raster_table,
            explain=explain
        )
        result = {
            'query': {
                'value': row[0][1],
                'id': row[0][0],
                'raster': raster_table,
            },
            'time': (datetime.now() - start).total_seconds(),
        }
        if explanation:
            result['explanation'] = explanation
    except Exception:
        return abort(400)

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


@app.route('/point_in_polygon')
def value_point_in_pol():
    """Get the value for a polygon field at a lon, lat."""
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    table = request.args.get('table')
    field = request.args.get('field')
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'

    if not lon or not lat or not table or not field:
        abort(400)

    start = datetime.now()
    point = {'lon': lon, 'lat': lat}
    row, explanation = get_point_in_polygon_value(
        point, table, field, explain=explain,
    )

    result = {
        'field': row[0],
        'result': row[1],
        'time': (datetime.now() - start).total_seconds(),
    }
    if explanation:
        result['explanation'] = explanation
    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.errorhandler(400)
def bad_request(error):
    import pudb; pudb.set_trace()
    expected = ""
    resp = make_response('Bad arguments provided. Expected: %s', 400)
    resp.headers['Content-Type'] = 'text/plain'
    return resp


if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run()
