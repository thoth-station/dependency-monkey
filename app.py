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


FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
                                  ['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
                              ['method', 'endpoint', 'http_status'])

app = Flask(__name__)
app.config.SWAGGER_UI_JSONEDITOR = True
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

api = Api(app, version='0alpha0', title='Thoth: Dependency Monkey API',
          description='... API',
          doc='/openapi/'  # could be False
          )

ns = api.namespace('validations', path='/api/v0alpha0/validations',
                   description='Validations')

validation = api.model('Todo', {
    'id': fields.Integer(required=True, readOnly=True, description='The Validation unique identifier'),
    'stack_specification': fields.String(required=True, description='Specification of the Software Stack'),
    'ecosystem': fields.String(redirect=True, description='In which ecosystem is the stack specification to be validated')
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


DAO = ValidationDAO()


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


@ns.route('/<int:id>')
@ns.response(404, 'Validation not found')
@ns.param('id', 'The Validation identifier')
class Validation(Resource):
    """Show a single Validation and lets you delete them"""
    @ns.doc('get_validation')
    @ns.marshal_with(validation)
    def get(self, id):
        """Fetch a given Validation"""

        v = None

        try:
            v = DAO.get(id)
        except NotFoundError as err:
            app.logger.error(str(err))
            ns.abort(404, "Validation {} doesn't exist".format(id))

        return v

    @ns.doc('delete_validation')
    @ns.response(204, 'Validation deleted')
    def delete(self, id):
        """Delete a Validation given its identifier"""

        try:
            v = DAO.delete(id)
        except NotFoundError as err:
            app.logger.error(str(err))
            ns.abort(404, "Validation {} doesn't exist".format(id))

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
    @ns.response(400, 'Ecosystem not supported')
    def post(self):
        """Request a new Validation"""

        try:
            v = DAO.create(api.payload)
        except EcosystemNotSupportedError as err:
            app.logger.error(str(err))
            ns.abort(400, str(err))

        return v, 201


if __name__ == "__main__":
    app.before_request(before_request)
    app.after_request(after_request)

    app.run(host='0.0.0.0', port=8080, debug=True)
