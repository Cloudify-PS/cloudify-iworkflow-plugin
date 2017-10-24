########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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
from mock import MagicMock
from mock import patch

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.exceptions import NonRecoverableError

from iworkflow_plugin import constants
from iworkflow_sdk import exceptions


class ConnectionNodeMock:
    def __init__(self):
        self.properties = {
            "conn1": "c"
        }


@patch("iworkflow_plugin.get_connected_node",
       return_value=ConnectionNodeMock())
class TestPlugin(unittest.TestCase):

    def test_create_success(self, mock_conn_params):
        _ctx = self._prepare_ctx()

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.create_service",
                   MagicMock(return_value=None)) as create_method:
            with patch("iworkflow_sdk.iworkflow.IWorkflowService.poll_service",
                       MagicMock(return_value=None)) as poll_method:
                from iworkflow_plugin import service
                service.create_service(vars=vars,
                                       tables=tables,
                                       properties=properties,
                                       reference_hostname=ref_host,
                                       retry_interval=10,
                                       ctx=_ctx)

                self.assertTrue(create_method.called)
                self.assertTrue(poll_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_create_no_params(self, mock_conn_params):
        _ctx = MockCloudifyContext(
            node_id="test_id",
            node_name="test_name",
            deployment_id="test_name",
            properties={}
        )

        _ctx._node.type = 'cloudify.iworkflow.Service'
        current_ctx.set(_ctx)

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        expected_error = 'Creation failed: ' \
                         'Tenant, service, template must be set.'

        with self.assertRaisesRegexp(NonRecoverableError,
                                     expected_error):
            from iworkflow_plugin import service
            # when
            service.create_service(vars=vars,
                                   tables=tables,
                                   properties=properties,
                                   reference_hostname=ref_host,
                                   retry_interval=10,
                                   ctx=_ctx)
        self.assertTrue(mock_conn_params.called)

    def test_create_failure(self, mock_conn_params):

        _ctx = self._prepare_ctx()

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        expected_error =\
            'Failed creating service \'{0}\' for template \'{1}\''\
            .format(_ctx._properties.get('service_name'),
                    _ctx._properties.get('template_name'))

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.create_service",
                   MagicMock(side_effect=Exception)) as create_method:
            from iworkflow_plugin import service
            # then
            with self.assertRaisesRegexp(NonRecoverableError,
                                         expected_error):
                # when
                service.create_service(vars=vars,
                                       tables=tables,
                                       properties=properties,
                                       reference_hostname=ref_host,
                                       retry_interval=10,
                                       ctx=_ctx)
                self.assertTrue(create_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_create_success_poll_failure(self, mock_conn_params):
        # given
        _ctx = self._prepare_ctx()

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        expected_error = 'Failed creating service \'{0}\''\
            .format(_ctx._properties.get('service_name'))

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.create_service",
                   MagicMock(return_value=None)) as create_method:
            with patch("iworkflow_sdk.iworkflow.IWorkflowService.poll_service",
                       MagicMock(side_effect=exceptions.IWorkflowException)) \
                    as poll_method:
                # then
                with self.assertRaisesRegexp(NonRecoverableError,
                                             expected_error):
                    # when
                    from iworkflow_plugin import service
                    service.create_service(vars=vars,
                                           tables=tables,
                                           properties=properties,
                                           reference_hostname=ref_host,
                                           retry_interval=10,
                                           ctx=_ctx)

                    self.assertTrue(create_method.called)
                    self.assertTrue(poll_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_poll_service_not_found(self, mock_conn_params):
        # given
        _ctx = self._prepare_ctx()

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.create_service",
                   MagicMock(return_value=None)) as create_method:
            with patch("iworkflow_sdk.iworkflow.IWorkflowService.poll_service",
                       MagicMock(
                           side_effect=exceptions.IWorkflowNotFoundException))\
                    as poll_method:
                with patch("cloudify.ctx.operation.retry",
                           MagicMock(return_value=None)) as retry_method:
                    # when
                    from iworkflow_plugin import service
                    service.create_service(vars=vars,
                                           tables=tables,
                                           properties=properties,
                                           reference_hostname=ref_host,
                                           retry_interval=10,
                                           ctx=_ctx)
                    # then
                    self.assertTrue(create_method.called)
                    self.assertTrue(poll_method.called)
                    self.assertTrue(retry_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_poll_retry_no_create(self, mock_conn_params):
        # given
        _ctx = self._prepare_ctx(1)

        vars = {"var1": "a"}
        tables = {"tab1": "b"}
        properties = {"prop1": "c"}
        ref_host = "local1"

        with patch(
                "iworkflow_sdk.iworkflow.IWorkflowService.create_service",
                MagicMock(return_value=None)) as create_method:
            with patch(
                    "iworkflow_sdk.iworkflow.IWorkflowService.poll_service",
                    MagicMock(
                        side_effect=exceptions.IWorkflowNotFoundException)) \
                    as poll_method:
                with patch("cloudify.ctx.operation.retry",
                           MagicMock(return_value=None)) as retry_method:
                    # when
                    from iworkflow_plugin import service
                    service.create_service(vars=vars,
                                           tables=tables,
                                           properties=properties,
                                           reference_hostname=ref_host,
                                           retry_interval=10,
                                           ctx=_ctx)
                    # then
                    self.assertFalse(create_method.called)
                    self.assertTrue(poll_method.called)
                    self.assertTrue(retry_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_delete_success(self, mock_conn_params):
        # given
        _ctx = self._prepare_ctx()

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.delete_service",
                   MagicMock(return_value=None)) as delete_method:
            # when
            from iworkflow_plugin import service
            service.delete_service(ctx=_ctx)
            # then
            self.assertTrue(delete_method.called)
        self.assertTrue(mock_conn_params.called)

    def test_delete_failure(self, mock_conn_params):
        # given
        _ctx = self._prepare_ctx()

        expected_error = 'Failed deleting service \'{0}\''\
            .format(_ctx._properties.get('service_name'))

        with patch("iworkflow_sdk.iworkflow.IWorkflowService.delete_service",
                   MagicMock(side_effect=Exception)) as delete_method:
            # when
            from iworkflow_plugin import service
            # then
            with self.assertRaisesRegexp(NonRecoverableError,
                                         expected_error):
                # when
                service.delete_service(ctx=_ctx)
                self.assertTrue(delete_method.called)
        self.assertTrue(mock_conn_params.called)

    def _prepare_ctx(self, retry_number=0):
        _ctx = MockCloudifyContext(
            node_id="test_id",
            node_name="test_name",
            deployment_id="test_name",
            properties={
                constants.KEY_TENANT_NAME: 'tenant1',
                constants.KEY_SERVICE_NAME: 'service1',
                constants.KEY_TEMPLATE_NAME: 'template1',
            },
            operation={"retry_number": retry_number}
        )
        _ctx._node.type = 'cloudify.iworkflow.Service'

        current_ctx.set(_ctx)

        return _ctx
