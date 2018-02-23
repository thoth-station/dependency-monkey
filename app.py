#!/usr/bin/env python3

"""Thoth: Dependency Monkey API"""

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

app = Flask(__name__)
app.config.SWAGGER_UI_JSONEDITOR = True
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

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

    app.run(host='0.0.0.0', port=8080, debug=True)
