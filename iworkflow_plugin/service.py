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

import sys

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

from iworkflow_plugin import load_connection_params
from iworkflow_sdk import iworkflow, exceptions

KEY_TENANT_NAME = 'tenant_name'
KEY_SERVICE_NAME = 'service_name'
KEY_TEMPLATE_NAME = 'template_name'

PARAMS_IP = "ip"
PARAMS_SYNC_GROUP = "sync_group"
PARAMS_USER = "user"
PARAMS_PASSWORD = "password"


@load_connection_params
@operation
def create_service(vars,
                   tables,
                   properties,
                   connection_params,
                   bigip_params,
                   reference_hostname,
                   retry_interval,
                   ctx):
    """
    Creates request payload
    and sends a 'create service' request
    to the iWorkflow.
    Polls for a service status
    """
    template_name = ctx.node.properties.get(KEY_TEMPLATE_NAME)

    if not template_name:
        raise NonRecoverableError("Template name is required")

    iworkflow_service = _get_iworkflow(ctx, connection_params)

    if ctx.operation.retry_number == 0:
        # start is executed for the first time, request service creation once.
        _create_service_request(iworkflow_service,
                                template_name,
                                vars,
                                tables,
                                properties,
                                reference_hostname,
                                ctx)

    _create_service_polling(iworkflow_service,
                            retry_interval,
                            ctx)

    iworkflow_service.sync(bigip_params.get(PARAMS_IP),
                           bigip_params.get(PARAMS_SYNC_GROUP),
                           bigip_params.get(PARAMS_USER),
                           bigip_params.get(PARAMS_PASSWORD),
                           retry_interval
                           )


@load_connection_params
@operation
def delete_service(connection_params,
                   ctx):
    """
    Sends 'delete service' request to the iWorkflow
    """
    iworkflow_service = _get_iworkflow(ctx, connection_params)

    try:
        iworkflow_service.delete_service()
        ctx.logger.info("Service {0} has been deleted".format(
            iworkflow_service.service_name))
    except Exception:
        _, exc_value, exc_traceback = sys.exc_info()
        raise NonRecoverableError(
            "Failed deleting service '{0}'".format(
                iworkflow_service.service_name
            ),
            causes=[exception_to_error_cause(exc_value, exc_traceback)]
        )


def _get_iworkflow(ctx, connection_params):
    """
    Creates an IWorkflowService based on context parameters.

    :param ctx: current context
    :param connection_params: iWorkflow connection parameters
    :return: An IWorkflowService object
    """
    tenant_name = ctx.node.properties.get(KEY_TENANT_NAME)
    service_name = ctx.node.properties.get(KEY_SERVICE_NAME)

    if not (tenant_name and service_name):
        raise NonRecoverableError(
            "Creation failed: Both tenant name and service name are required"
        )

    return iworkflow.IWorkflowService(tenant_name, service_name,
                                      connection_params)


def _create_service_request(iworkflow_service,
                            template_name,
                            vars,
                            tables,
                            properties,
                            reference_hostname,
                            ctx):
    try:
        iworkflow_service.create_service(template_name,
                                         vars,
                                         tables,
                                         properties,
                                         reference_hostname)
        ctx.logger.info("Service {0} has been requested".format(
            iworkflow_service.service_name))
    except Exception:
        _, exc_value, exc_traceback = sys.exc_info()
        raise NonRecoverableError(
            "Failed creating service '{0}' for template '{1}'".format(
                iworkflow_service.service_name,
                template_name),
            causes=[exception_to_error_cause(exc_value, exc_traceback)]
        )


def _create_service_polling(iworkflow_service,
                            retry_interval,
                            ctx):
    try:
        iworkflow_service.poll_service()
        ctx.logger.info("Service {0} has been created".format(
            iworkflow_service.service_name))
    except exceptions.IWorkflowNotFoundException as iwe:
        return ctx.operation.retry(
            message="Service {0} is not created yet. "
                    "Response details: {1}".format(
                        iworkflow_service.service_name, str(iwe)),
            retry_after=retry_interval
        )
    except Exception:
        _, exc_value, exc_traceback = sys.exc_info()
        raise NonRecoverableError(
            "Failed creating service '{0}'".format(
                iworkflow_service.service_name
            ),
            causes=[exception_to_error_cause(exc_value, exc_traceback)]
        )
