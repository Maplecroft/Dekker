#!/usr/bin/env python

# -*- coding: iso-8859-15 -*-
import os
import re

from datetime import datetime
import logging

from flask import Flask, abort, make_response, request, jsonify
from flask import __version__ as flask_version

import conf
from utils import (
    get_buffer_value_at_polygon,
    get_buffer_values_at_points,
    get_point_in_polygon_value,
    get_raster_file_path,
    get_value_at_points,
    is_valid,
    make_live,
    md5sum
)

app = Flask(__name__)


@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr
        # app is internal so we want debug level logging
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)


@app.route('/pointbuffer')
@app.route('/custombuffer')
def buffer_value_at_point(rad=None, legacy=False):
    """Get average value in buffer around point.

       Expects:
            id:           a given point id (int) - defaults to 999
            lon:          longitude of point (float)
            lat:          latitude of point (float)
            radius:       radius of buffer in km (int/float)
            raster_table: name of raster table to query. (string)
            jsonp:        return result as jsonp function call (string)

    """
    point_id = request.args.get('id') or 999
    try:
        rad = rad or float(request.args.get('radius'))
    except:
        abort(400)

    lon = float(request.args.get('lon'))
    lat = float(request.args.get('lat'))
    raster_table = request.args.get('raster_table').lower()
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'

    if not lon or not lat or not len(raster_table):
        abort(400)

    start = datetime.now()
    result = {}
    try:
        results, explanation = get_buffer_values_at_points(
            rad,
            [(lon, lat, int(point_id))],
            raster_table,
            explain=explain,
            legacy=legacy,
        )

        result = {
            'query': {
                'value': results[0][1],
                'id': results[0][0],
                'raster': raster_table,
            },
            'time': (datetime.now() - start).total_seconds(),
        }
        if explanation:
            result['explanation'] = explanation
    except Exception, ex:
        app.logger.warning(ex)
        return abort(400)

    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.route('/buffer')
def legacy_buffer_value_at_point():
    """Get average value in buffer around point using set 25km radius.

       Expects:
            id:           a given point id (int) - defaults to 999
            lon:          longitude of point (float)
            lat:          latitude of point (float)
            raster_table: name of raster table to query. (string)
            jsonp:        return result as jsonp function call (string)

    """
    return buffer_value_at_point(rad=25, legacy=True)


@app.route('/polygon')
def value_at_polygon():
    """Get average value for an area of a scored raster defined by a polygon.

       Expects:
            id:           longitude of point (float)
            geom:         WKT format of POLYGON((..))
            raster_table: name of raster table to query. (string)
            jsonp:        return result as jsonp function call (string)
    """

    point_id = request.args.get('id') or 999
    raster_table = (request.args.get('raster_table') or "").lower()
    jsonp = request.args.get('jsonp', False) and float(flask_version) >= 0.9
    explain = request.args.get('explain', False) == 'true'
    geom = request.args.get('geom')

    if not geom:
        abort(400)

    # Check polygon syntax
    rx = re.compile(
        "POLYGON\(\((?P<point>(-?\d+(?:\.\d+)? -?\d+(?:\.\d+)?)(?:, ?)?)+\)\)"
    )

    if not rx.match(geom) or not raster_table:
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
    except Exception, ex:
        app.logger.warning(ex)
        return abort(400)

    return jsonify(result) if not jsonp else jsonify(result, jsonp=jsonp)


@app.route('/point')
def value_at_point():
    """Get the value at a lon, lat for a given view.

       Expects:
            lon:          longitude of point (float)
            lat:          latitude of point (float)
            tifs:         multiple raster tifs to get scores from
            jsonp:        return result as jsonp function call (string)
    """
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
    """Get the value for a polygon field at a lon, lat.

       Expects:
            lon:          longitude of point (float)
            lat:          latitude of point (float)
            table:        table to query (string)
            field:        field to retrieve (string)
            jsonp:        return result as jsonp function call (string)
    """
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




def _validate(index_view_slug):

    return is_valid(
        index_view_slug, base_path=conf.DRAFT_DIR
    )


@app.route('/validate', methods=['POST'])
def validate():
    """ Uploads a file to a draft area then tests if it is valid.
        Expects:
            index_view_slug:   unique name of tif file to lookup(string)
            file:              in request.files for upload
    """
    index_view_slug = request.form.get('index_view_slug')

    if not index_view_slug or 'file' not in request.files:
        abort(400)

    if index_view_slug.endswith('_raster'):
        index_view_slug = index_view_slug[:-7]

    draft_file = os.path.join(conf.DRAFT_DIR,
                              '{}.tif'.format(index_view_slug))
    request.files['file'].save(draft_file)
    result = {'errors': []}
    try:
        valid = is_valid(
            index_view_slug, base_path=conf.DRAFT_DIR
        )
        result = {
            'md5': md5sum(draft_file),
            'valid': valid
        }
        os.remove(draft_file)
    except NotImplementedError as e:
        result['errors'].append(e.message)

    return jsonify(result)


@app.route('/publish', methods=['POST'])
def publish():
    """ Uploads a file to a draft area then moves it to data directory if valid.
        Expects:
            index_view_slug:   unique name of tif file to lookup(string)
            file:              in request.files for upload
    """

    index_view_slug = request.form.get('index_view_slug')

    if not index_view_slug or 'file' not in request.files:
        abort(400)

    if index_view_slug.endswith('_raster'):
        index_view_slug = index_view_slug[:-7]

    draft_file = os.path.join(conf.DRAFT_DIR,
                              '{}.tif'.format(index_view_slug))
    request.files['file'].save(draft_file)
    result = {'errors': []}
    try:
        result['valid'] = is_valid(index_view_slug, base_path=conf.DRAFT_DIR)
        if result['valid']:
            live_file = make_live(draft_file)
            if os.path.exists(live_file):
                result = {
                    'md5': md5sum(live_file),
                }

    #except Exception as e:
    except NotImplementedError as e:
        result['errors'].append(e.message)

    return jsonify(result)


@app.route('/md5')
def get_md5_for_index_view_slug():
    """ Gets the md5 value for a tif matching the slug parameter or -1 if
    not found.

        Expects:
            index_view_slug:   unique name of tif file to lookup(string)
    """
    index_view_slug = request.args.get('index_view_slug')

    if not index_view_slug:
        abort(400)

    value = -1
    try:
        raster_file = get_raster_file_path(index_view_slug)
        value = md5sum(raster_file)

    except IOError:
        pass

    result = {
        'md5': value
    }
    return jsonify(result)


@app.errorhandler(400)
def bad_request(error):
    docstr = globals().get(request.endpoint).__doc__
    if 'Expects' not in docstr:
        docstr = ""
    else:
        docstr = docstr[docstr.find('Expects'):]

    path = request.path
    resp = make_response('Bad arguments provided to %s. %s' % (
        path,
        docstr,
    ), 400)
    resp.headers['Content-Type'] = 'text/plain'
    return resp


if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run(debug=conf.DEBUG)
