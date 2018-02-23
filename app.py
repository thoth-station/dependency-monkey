#!/usr/bin/env python3

"""Thoth: Dependency Monkey"""

import time
import logging

from flask import Flask, redirect, request
from flask.helpers import make_response

from flask_restplus import Resource, Api, fields
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, core

import thoth_dependency_monkey


FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
                                  ['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
                              ['method', 'endpoint', 'http_status'])

log = logging.getLogger(__name__)

app = Flask(__name__)

api = Api(app, version='0.1.0-dev', title='Thoth: Dependency Monkey API',
          description='... API',
          )

ns = api.namespace('validations', path='/api/v0', description='Validations')

validation = api.model('Todo', {
    'id': fields.Integer(required=True, readOnly=True, description='The Validation unique identifier'),
    'stack_specification': fields.String(required=True, description='Specification of the Software Stack'),
})


def before_request():
    request.start_time = time.time()


def after_request(response):
    request_latency = time.time() - request.start_time
    FLASK_REQUEST_LATENCY.labels(
        request.method, request.path).observe(request_latency)
    FLASK_REQUEST_COUNT.labels(
        request.method, request.path, response.status_code).inc()

    return response


class ValidationDAO():
    def __init__(self):
        self.counter = 0
        self.validations = []

    def get(self, id):
        for v in self.validations:
            if v['id'] == id:
                return v

        api.abort(404, "Validation {} doesn't exist".format(id))

    def create(self, data):
        v = data
        v['id'] = self.counter = self.counter + 1

        self.validations.append(v)

        return v

    def delete(self, id):
        v = self.get(id)

        self.validations.remove(v)


DAO = ValidationDAO()


@app.route('/')
def base_url():
    return redirect('api')


@api.route('/api/hello')
class HelloWorld(Resource):
    def get(self):
        return {'name': 'Thoth Dependency Monkey', 'version': thoth_dependency_monkey.  __version__}


@app.route('/metrics/')
def metrics():
    registry = core.REGISTRY
    output = generate_latest(registry)
    response = make_response(output)
    response.headers['Content-Type'] = CONTENT_TYPE_LATEST

    return response
    return data


@ns.route('/<int:id>')
@ns.response(404, 'Validation not found')
@ns.param('id', 'The Validation identifier')
class Validation(Resource):
    """Show a single Validation and lets you delete them"""
    @ns.doc('get_validation')
    @ns.marshal_with(validation)
    def get(self, id):
        """Fetch a given Validation"""

        return DAO.get(id)

    @ns.doc('delete_validation')
    @ns.response(204, 'Validation deleted')
    def delete(self, id):
        """Delete a Validation given its identifier"""

        DAO.delete(id)

        return '', 204


@ns.route('/')
class ValidationList(Resource):
    """Shows a list of all Validations, and let's you request a new Validation"""
    @ns.doc('list_validations')
    @ns.marshal_list_with(validation)
    def get(self):
        """List all Validations"""
        return DAO.validations

    @ns.doc('request_validation')
    @ns.expect(validation)
    @ns.marshal_with(validation, code=201)
    def post(self):
        """Request a new Validation"""
        return DAO.create(api.payload), 201


if __name__ == "__main__":
    app.before_request(before_request)
    app.after_request(after_request)

    app.run(port=8080, debug=True)
