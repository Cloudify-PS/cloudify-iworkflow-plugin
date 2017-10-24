########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


import unittest
import requests_mock

from iworkflow_sdk.iworkflow import IWorkflowService
from iworkflow_sdk.exceptions import (
    IWorkflowException,
    IWorkflowNotFoundException
)
from iworkflow_sdk.iworkflow import SERVICE_ENDPOINT

tenant_name = 'tenant1'
service_name = 'service1'


def get_connection_params(use_ssl=True):
    if use_ssl:
        port = 443
    else:
        port = 80

    return {
        "ip": "1.2.3.4",
        "port": port,
        "user": "user1",
        "password": "pass1",
        "use_ssl": use_ssl
    }


def get_url(connection_params):
    if connection_params.get('use_ssl'):
        proto = 'https'
    else:
        proto = 'http'

    return "{0}://{1}:{2}{3}".format(
        proto,
        connection_params.get("ip"),
        connection_params.get("port"),
        SERVICE_ENDPOINT.format(tenant_name)
    )


def get_iworkflow_service(connection_params):
    return IWorkflowService(
        tenant_name,
        service_name,
        connection_params
    )


class IWorkflowServiceTest(unittest.TestCase):

    def test_create_service_200_success(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        with requests_mock.mock() as m:
            m.post(url,
                   json={},
                   status_code=200)

            # when
            result = iworkflow_service.create_service(
                "template1",
                {"var": "data1"},
                {"tables": "data2"},
                {"properties": "data3"},
                "localhost"
            )

            # then
            self.assertIsNone(result)

    def test_create_service_200_success_no_ssl(self):
        # given
        conn_params = get_connection_params(use_ssl=False)
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        with requests_mock.mock() as m:
            m.post(url,
                   json={},
                   status_code=200)

            # when
            result = iworkflow_service.create_service(
                "template1",
                {"var": "data1"},
                {"tables": "data2"},
                {"properties": "data3"},
                "localhost"
            )

            # then
            self.assertIsNone(result)

    def test_create_service_error(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        error_msg = 'error1'
        expected_error = 'Error received while polling service: {0}'.format(
            error_msg
        )

        with requests_mock.mock() as m:
            m.post(url,
                   json={'message': error_msg},
                   status_code=400)

            # then
            with self.assertRaisesRegexp(IWorkflowException,
                                         expected_error):
                # when
                iworkflow_service.create_service(
                    "template1",
                    {"var": "data1"},
                    {"tables": "data2"},
                    {"properties": "data3"},
                    "localhost"
                )

    def test_create_service_error_no_json(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        error_msg = 'no error message'
        expected_error = 'Error received while polling service: {0}'.format(
            error_msg
        )

        with requests_mock.mock() as m:
            m.post(url,
                   text="no json",
                   status_code=400)

            # then
            with self.assertRaisesRegexp(IWorkflowException,
                                         expected_error):
                # when
                iworkflow_service.create_service(
                    "template1",
                    {"var": "data1"},
                    {"tables": "data2"},
                    {"properties": "data3"},
                    "localhost"
                )

    def test_poll_service_200_success(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        with requests_mock.mock() as m:
            m.get("{0}{1}".format(url, service_name),
                  json={},
                  status_code=200)

            # when
            result = iworkflow_service.poll_service()

            # then
            self.assertIsNone(result)

    def test_poll_service_200_with_error(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        error_msg = 'error1'
        expected_error = 'Error received while polling service: {0}'.format(
            error_msg
        )

        with requests_mock.mock() as m:
            m.get("{0}{1}".format(url, service_name),
                  json={'error': error_msg},
                  status_code=200)

            # then
            with self.assertRaisesRegexp(IWorkflowException,
                                         expected_error):
                # when
                iworkflow_service.poll_service()

    def test_poll_service_404(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        error_msg = 'error1'
        expected_error = 'Error received while polling service: {0}'.format(
            error_msg
        )

        with requests_mock.mock() as m:
            m.get("{0}{1}".format(url, service_name),
                  json={'message': error_msg},
                  status_code=404)

            # then
            with self.assertRaisesRegexp(IWorkflowNotFoundException,
                                         expected_error):
                # when
                iworkflow_service.poll_service()

    def test_poll_service_other_error(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        error_code = 400
        expected_error =\
            'An unexpected HTTP response code = {0} has been received'\
            .format(error_code)

        with requests_mock.mock() as m:
            m.get("{0}{1}".format(url, service_name),
                  json={},
                  status_code=error_code)

            # then
            with self.assertRaisesRegexp(IWorkflowException,
                                         expected_error):
                # when
                iworkflow_service.poll_service()

    def test_delete_service_200_success(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        with requests_mock.mock() as m:
            m.delete("{0}{1}".format(url, service_name),
                     json={},
                     status_code=200)

            # when
            result = iworkflow_service.delete_service()

            # then
            self.assertIsNone(result)

    def test_delete_service_error(self):
        # given
        conn_params = get_connection_params()
        url = get_url(conn_params)
        iworkflow_service = get_iworkflow_service(conn_params)

        expected_error = "Cannot delete service {0}".format(service_name)

        with requests_mock.mock() as m:
            m.delete("{0}{1}".format(url, service_name),
                     json={},
                     status_code=400)

            # then
            with self.assertRaisesRegexp(IWorkflowException,
                                         expected_error):
                # when
                iworkflow_service.delete_service()
