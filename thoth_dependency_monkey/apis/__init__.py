from flask_restplus import Api

import thoth_dependency_monkey
from .validations import ns as validations_v0alpha0

api = Api(version=thoth_dependency_monkey.__version__, title='Thoth: Dependency Monkey API',
          description='The "Dependency Monkey" is a service for validating package dependencies within an application stack', doc='/openapi/')

api.add_namespace(validations_v0alpha0, path='/api/v0alpha0/validations')
