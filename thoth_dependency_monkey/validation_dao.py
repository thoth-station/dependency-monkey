import os
import logging
import uuid

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId, InvalidId
from werkzeug.exceptions import BadRequest, ServiceUnavailable

from .ecosystem import ECOSYSTEM, EcosystemNotSupportedError


MONGODB_USER = os.getenv('MONGODB_USER', 'mongo')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'mongo')
MONGODB_HOSTNAME = os.getenv('MONGODB_HOSTNAME', 'mongodb')
MONGODB_PORT = os.getenv('MONGODB_SERVICE_PORT', 27017)
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'dev')

MONGODB_URL = 'mongodb://{}:{}@{}:{}/{}'.format(
    MONGODB_USER, MONGODB_PASSWORD, MONGODB_HOSTNAME, MONGODB_PORT, MONGODB_DATABASE)


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
        logger.info(MONGODB_URL)
        self.mongo = MongoClient(MONGODB_URL)

        # TODO handle

    def get(self, id):
        try:
            v = self.mongo[MONGODB_DATABASE]['validations'].find_one(
                {"_id": ObjectId(id)})
        except ConnectionFailure as e:
            raise e  # TODO
        except InvalidId as e:
            raise NotFoundError(id)

        if v is None:
            raise NotFoundError(id)

        v['id'] = id

        return v

    def get_all(self):
        return self.mongo[MONGODB_DATABASE]['validations'].find()

    def create(self, data):
        v = data

        if v['ecosystem'] not in ECOSYSTEM:
            raise EcosystemNotSupportedError(v['ecosystem'])

        # TODO check if stack_specification is valid

        v['result_queue_name'] = self._get_result_queue_name()

        try:
            _v = self.mongo[MONGODB_DATABASE]['validations'].insert_one(v)
        except Exception as e:
            # FIXME we should log here...
            raise ServiceUnavailable('database')

        v['id'] = _v.inserted_id

        return v

    def delete(self, id):
        v = self.get(id)

        self.mongo[MONGODB_DATABASE]['validations'].remove(
            {"_id": ObjectId(id)})

    def _get_result_queue_name(self):
        return str(uuid.uuid4())
