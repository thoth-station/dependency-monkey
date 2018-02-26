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
import logging
import uuid
import yaml

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId, InvalidId
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from tempfile import NamedTemporaryFile
from openshift import client, config
from kubernetes import client as kclient
from kubernetes.client import Configuration
from kubernetes.client import api_client
from kubernetes.client.apis import batch_v1_api


from .ecosystem import ECOSYSTEM, EcosystemNotSupportedError

DEBUG = bool(os.getenv('DEBUG', False))

MONGODB_USER = os.getenv('MONGODB_USER', 'mongo')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'mongo')
MONGODB_HOSTNAME = os.getenv('MONGODB_HOSTNAME', 'mongodb')
MONGODB_PORT = os.getenv('MONGODB_SERVICE_PORT', 27017)
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'dev')

MONGODB_URL = 'mongodb://{}:{}@{}:{}/{}'.format(
    MONGODB_USER, MONGODB_PASSWORD, MONGODB_HOSTNAME, MONGODB_PORT, MONGODB_DATABASE)

# if DEBUG and MONGODB_HOSTNAME == 'localhost':
#    MONGODB_URL = 'mongodb://{}:{}/{}'.format(
#        MONGODB_HOSTNAME, MONGODB_PORT, MONGODB_DATABASE)

THOTH_NAMESPACE = 'thoth-dev'

logging.basicConfig()
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
        logger.debug('using MongoDB at {}'.format(MONGODB_URL))

        # TODO handle auth, think about reconnect etc
        self.mongo = MongoClient(MONGODB_URL)

        self.kconfig = Configuration()

        # if we can read bearer token from /var/run/secrets/kubernetes.io/serviceaccount/token use it,
        # otherwise use the one from env
        try:
            logger.debug(
                'trying to get bearer token from secrets file within pod...')
            with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as f:
                BEARER_TOKEN = f.read()

                self.kconfig.api_key['authorization'] = 'Bearer {}'.format(
                    BEARER_TOKEN)

            self.kconfig.ssl_ca_cert = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

            # Load the "kubernetes" service items.
            service_host = os.environ['KUBERNETES_SERVICE_HOST']
            service_port = os.environ['KUBERNETES_SERVICE_PORT']
            self.kconfig.host = 'https://{}:{}'.format(
                service_host, service_port)

        except:
            logger.info("not running within an OpenShift cluster...")

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

        _job = self._get_scheduled_validation_job(id)

        if 'succeeded' in _job.status.to_dict().keys():
            v['phase'] = 'succeeded'

        return v

    def get_all(self):
        return self.mongo[MONGODB_DATABASE]['validations'].find()

    def create(self, data):
        v = data

        if v['ecosystem'] not in ECOSYSTEM:
            raise EcosystemNotSupportedError(v['ecosystem'])

        # check if stack_specification is valid
        if not self._validate_requirements(v['stack_specification']):
            raise BadRequest(
                'specification is not valid within Ecosystem {}'.format(v['ecosystem']))

        v['phase'] = 'pending'

        try:
            _v = self.mongo[MONGODB_DATABASE]['validations'].insert_one(v)
        except Exception as e:
            logger.error(e)
            raise ServiceUnavailable('database')

        v['id'] = _v.inserted_id

        self._schedule_validation_job(v['id'])

        return v

    def delete(self, id):
        self.mongo[MONGODB_DATABASE]['validations'].remove(
            {"_id": ObjectId(id)})

        # TODO add kubernetes job stuff

    def _validate_requirements(self, spec):
        """This function will check if the syntax of the provided specification is valid"""
        from pip.req.req_file import parse_requirements

        # create a temporary file and store the spec there since
        # `parse_requirements` requires a file
        with NamedTemporaryFile(mode='w+', suffix='pysolve') as f:
            f.write(spec)
            f.flush()
            reqs = parse_requirements(f.name, session=f.name)

        if reqs:
            return True

        return False

    def _whats_my_name(self, id):
        return 'validation-job-' + str(id)

    def _schedule_validation_job(self, id):
        logger.debug('scheduling validation id {}'.format(id))

        config.load_kube_config()
        _client = api_client.ApiClient()

        _name = self._whats_my_name(id)
        _job_manifest = {
            'kind': 'Job',
            'spec': {
                'template':
                    {'spec':
                        {'containers': [
                            {'image': 'busybox',
                             'name': _name,
                             'command': ["sh", "-c", "sleep 35"]
                             }],
                            'restartPolicy': 'Never'},
                        'metadata': {'name': _name}}},
            'apiVersion': 'batch/v1',
            'metadata': {
                    'name': _name,
                    'labels': {
                        'validation_id': str(id)
                    }
            }
        }

        _api = batch_v1_api.BatchV1Api(_client)

        try:
            _resp = _api.create_namespaced_job(
                body=_job_manifest, namespace=THOTH_NAMESPACE)
        except kclient.rest.ApiException as e:
            logger.error(e)

            raise ServiceUnavailable('OpenShift')

    def _get_scheduled_validation_job(self, id):
        logger.debug('looking for validation id {}'.format(id))

        config.load_kube_config()
        _client = api_client.ApiClient()

        _api = batch_v1_api.BatchV1Api(_client)

        try:
            _resp = _api.list_namespaced_job(
                namespace=THOTH_NAMESPACE, include_uninitialized=True, label_selector='validation_id='+str(id))

            _job = _resp.items[0]

            logger.debug(_job.status)

            return _job

        except kclient.rest.ApiException as e:
            logger.error(e)

            raise ServiceUnavailable('OpenShift')

        return None
