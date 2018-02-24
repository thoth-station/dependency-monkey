import logging

from werkzeug.exceptions import BadRequest
from flask import request
from flask_restplus import Namespace, Resource, fields

from thoth_dependency_monkey.validation_dao import ValidationDAO, NotFoundError
from thoth_dependency_monkey.ecosystem import ECOSYSTEM, EcosystemNotSupportedError


ns = Namespace('validations', description='Validations')

validation = ns.model('Validation', {
    'id': fields.Integer(required=True, readOnly=True, description='The Validation unique identifier'),
    'stack_specification': fields.String(required=True, description='Specification of the Software Stack'),
    'ecosystem': fields.String(required=True, default='pypi', description='In which ecosystem is the stack specification to be validated'),
    'result_queue_name': fields.String(description='The name of the Kafka queue containing the result of the Validation.')
})


DAO = ValidationDAO()
logger = logging.getLogger(__file__)


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
            ns.abort(404, "Validation {} doesn't exist".format(id))

        return v

    @ns.doc('delete_validation')
    @ns.response(204, 'Validation deleted')
    def delete(self, id):
        """Delete a Validation given its identifier"""

        try:
            v = DAO.delete(id)
        except NotFoundError as err:
            ns.abort(404, "Validation {} doesn't exist".format(id))

        return '', 204


@ns.route('/')
class ValidationList(Resource):
    """Shows a list of all Validations, and let's you request a new Validation"""
    @ns.doc('list_validations')
    @ns.marshal_list_with(validation)
    def get(self):
        """List all Validations"""

        logger.debug(request)

        return DAO.validations

    @ns.doc('request_validation')
    @ns.expect(validation)
    @ns.marshal_with(validation, code=201)
    @ns.response(400, 'Ecosystem not supported')
    @ns.response(201, 'Validation request accepted')
    def post(self):
        """Request a new Validation"""

        try:
            v = DAO.create(request.get_json())
        except EcosystemNotSupportedError as err:
            ns.abort(400, str(err))
        except Exception as e:
            ns.abort(400, str(e))
            raise BadRequest()

        return v, 201
