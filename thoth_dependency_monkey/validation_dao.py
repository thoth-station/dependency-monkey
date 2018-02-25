import uuid

from pymongo import MongoClient
from bson.objectid import ObjectId, InvalidId
from werkzeug.exceptions import BadRequest

from .ecosystem import ECOSYSTEM, EcosystemNotSupportedError


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
        self.mongo = MongoClient('mongodb://localhost:27017/')

    def get(self, id):
        try:
            v = self.mongo['local']['validations'].find_one(
                {"_id": ObjectId(id)})
        except InvalidId as e:
            raise NotFoundError(id)

        if v is None:
            raise NotFoundError(id)

        v['id'] = id

        return v

    def get_all(self):
        return self.mongo['local']['validations'].find()

    def create(self, data):
        v = data

        if v['ecosystem'] not in ECOSYSTEM:
            raise EcosystemNotSupportedError(v['ecosystem'])

        # TODO check if stack_specification is valid

        v['result_queue_name'] = self._get_result_queue_name()
        _v = self.mongo['local']['validations'].insert_one(v)

        v['id'] = _v.inserted_id

        return v

    def delete(self, id):
        v = self.get(id)

        self.mongo['local']['validations'].remove({"_id": ObjectId(id)})

    def _get_result_queue_name(self):
        return str(uuid.uuid4())
