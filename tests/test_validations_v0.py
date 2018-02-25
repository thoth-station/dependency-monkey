import unittest
import pytest

from flask import url_for

import flask_restplus as restplus


class ValidationsV0Test(object):
    def test_root_endpoint(self, app):
        api = restplus.Api(app, version="0.0.0-test")

        with app.test_request_context():
            url = url_for('root')

            assert url == '/'
            assert api.base_url == 'http://localhost/'
