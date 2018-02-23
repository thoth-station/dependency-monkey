import logging

from werkzeug.exceptions import BadRequest

from .ecosystem import ECOSYSTEM, EcosystemNotSupportedError


logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


class NotFoundError(BadRequest):
    """Exception raised if a Validation does not exist.

    Attributes:
        id -- id of the Validation that does not exist
        message -- verbal representation
    """

    def __init__(self, id):
        self.id = id
        self.message = "Validation {} doesn't exist".format(id)


class ValidationDAO():
    def __init__(self):
        self.counter = 0
        self.validations = []

    def get(self, id):
        for v in self.validations:
            if v['id'] == id:
                return v

        raise NotFoundError(id)

    def create(self, data):
        v = data
        v['id'] = self.counter = self.counter + 1

        if v['ecosystem'] not in ECOSYSTEM:
            raise EcosystemNotSupportedError(v['ecosystem'])

        # TODO check if stack_specification is valid

        self.validations.append(v)

        return v

    def delete(self, id):
        v = self.get(id)

        self.validations.remove(v)
