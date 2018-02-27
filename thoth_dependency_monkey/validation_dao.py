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

from werkzeug.exceptions import BadRequest, ServiceUnavailable
from tempfile import NamedTemporaryFile
from kubernetes import client, config
from kubernetes.client import api_client
from kubernetes.client.apis import batch_v1_api


from .ecosystem import ECOSYSTEM, EcosystemNotSupportedError

DEBUG = bool(os.getenv('DEBUG', False))

KUBERNETES_API_URL = os.getenv(
    'KUBERNETES_API_URL', 'https://kubernetes.default.svc.cluster.local:443')
THOTH_DEPENDENCY_MONKEY_NAMESPACE = 'thoth-dev'

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
        self.BEARER_TOKEN = None

        # if we can read bearer token from /var/run/secrets/kubernetes.io/serviceaccount/token use it,
        # otherwise use the one from env
        try:
            logger.debug(
                'trying to get bearer token from secrets file within pod...')
            with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as f:
                self.BEARER_TOKEN = f.read()

            self.SSL_CA_CERT_FILENAME = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

        except:
            logger.info("not running within an OpenShift cluster...")

    def get(self, id):
        v = {}

        v['id'] = id

        _job = self._get_scheduled_validation_job(id)

        # if we didnt get back anything from OpenShift, we let it 404
        if _job is None:
            raise NotFoundError(id)

        # lets copy the Validation information from the Kubernetes Job
        for container in _job.spec.template.spec.containers:
            if container.name.endswith(str(id)):
                for env in container.env:
                    v[env.name] = env.value

        if _job.status.succeeded is not None:
            v['phase'] = 'succeeded'
        elif _job.status.failed is not None:
            v['phase'] = 'failed'
        elif _job.status.active is not None:
            v['phase'] = 'running'

        return v

    def create(self, data):
        v = data

        if v['ecosystem'] not in ECOSYSTEM:
            raise EcosystemNotSupportedError(v['ecosystem'])

        # check if stack_specification is valid
        if not self._validate_requirements(v['stack_specification']):
            raise BadRequest(
                'specification is not valid within Ecosystem {}'.format(v['ecosystem']))

        v['phase'] = 'pending'
        v['id'] = str(uuid.uuid4())

        self._schedule_validation_job(
            v['id'], v['stack_specification'], v['ecosystem'])

        return v

    def delete(self, id):
        # TODO add kubernetes job stuff
        pass

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

    def _schedule_validation_job(self, id, spec, ecosystem):
        logger.debug('scheduling validation id {}'.format(id))

        _name = self._whats_my_name(id)
        _job_manifest = {
            'kind': 'Job',
            'spec': {
                'template':
                    {'spec':
                        {'serviceAccountName': 'validation-job-runner',
                         'containers': [
                             {
                                 'image': 'busybox',
                                 'name': _name,
                                 'command': ["sh", "-c", "sleep 45"],
                                 'env': [
                                     {
                                         'name': 'stack_specification',
                                         'value': spec
                                     },
                                     {
                                         'name': 'ecosystem',
                                         'value': ecosystem
                                     }
                                 ]
                             }
                         ],
                            'restartPolicy': 'Never'},
                        'metadata': {'name': _name}}},
            'apiVersion': 'batch/v1',
            'metadata': {'name': _name, 'labels': {'validation_id': str(id)}}
        }

        config.load_incluster_config()
        _client = client.CoreV1Api()
        _api = client.BatchV1Api()

        try:
            _resp = _api.create_namespaced_job(
                body=_job_manifest, namespace=THOTH_DEPENDENCY_MONKEY_NAMESPACE)
        except client.rest.ApiException as e:
            logger.error(e)

            if e.status == 403:
                raise ServiceUnavailable('OpenShift auth failed')

            raise ServiceUnavailable('OpenShift')

    def _get_scheduled_validation_job(self, id):
        logger.debug('looking for validation id {}'.format(id))

        config.load_incluster_config()
        _client = client.CoreV1Api()
        _api = client.BatchV1Api()

        try:
            _resp = _api.list_namespaced_job(
                namespace=THOTH_DEPENDENCY_MONKEY_NAMESPACE, include_uninitialized=True, label_selector='validation_id='+str(id))

            if not _resp.items is None:
                return _resp.items[0]
        except client.rest.ApiException as e:
            logger.error(e)

            if e.status == 403:
                raise ServiceUnavailable('OpenShift auth failed')

            raise ServiceUnavailable('OpenShift')

        except IndexError as e:
            logger.debug('we got no jobs...')

            return None

        return None
