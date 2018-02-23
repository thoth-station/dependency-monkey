from flask_restplus import Api

import thoth_dependency_monkey
from .validations import ns as validations_v0alpha0

api = Api(version=thoth_dependency_monkey.__version__, title='Thoth: Dependency Monkey API',
          description='... API', doc='/openapi/')

api.add_namespace(validations_v0alpha0, path='/api/v0alpha0/validations')
