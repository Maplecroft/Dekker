#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import logging

from flask import Flask, make_response

from werkzeug.contrib.fixers import ProxyFix


app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = ProxyFix(app.wsgi_app)


@app.before_first_request
def setup_logging():
    if not app.config['DEBUG']:
        # In production mode, add log handler to sys.stderr
        # app is internal so we want debug level logging
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)

@app.errorhandler(400)
def bad_request(error):
    response = make_response('lon, lat, and tif are all required parameters', 400)
    response.headers['Content-Type'] = 'text/plain'
    return response