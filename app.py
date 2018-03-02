#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   thoth-dependency-monkey
#   Copyright(C) 2018 Christoph Görn
#
#   This program is free software: you can redistribute it and / or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Thoth: Dependency Monkey API"""

import os
import time
import logging

from flask import Flask, redirect, request, jsonify
from flask.helpers import make_response

from flask_restplus import Resource, Api, fields

from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, core

import thoth_dependency_monkey
from thoth_dependency_monkey.validation_dao import ValidationDAO, NotFoundError, EcosystemNotSupportedError
from thoth_dependency_monkey.apis import api

FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
                                  ['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
                              ['method', 'endpoint', 'http_status'])

DEBUG = bool(os.getenv('DEBUG', False))

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


app = Flask(__name__)
app.config.SWAGGER_UI_JSONEDITOR = True
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.logger.setLevel(logging.DEBUG)

api.init_app(app)


def before_request():
    request.start_time = time.time()


def after_request(response):
    request_latency = time.time() - request.start_time
    FLASK_REQUEST_LATENCY.labels(
        request.method, request.path).observe(request_latency)
    FLASK_REQUEST_COUNT.labels(
        request.method, request.path, response.status_code).inc()

    return response


@app.route('/')
def index():
    return "Thoth Dependency Monkey v{}".format(thoth_dependency_monkey.  __version__)


@app.route('/metrics/')
def metrics():
    registry = core.REGISTRY
    output = generate_latest(registry)
    response = make_response(output)
    response.headers['Content-Type'] = CONTENT_TYPE_LATEST

    return response


@app.route('/schema')
def print_api_schema():
    return jsonify(api.__schema__)


if __name__ == "__main__":
    app.before_request(before_request)
    app.after_request(after_request)

    app.run(host='0.0.0.0', port=8080, debug=DEBUG)
