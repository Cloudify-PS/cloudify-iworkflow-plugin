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

import json
import requests
from requests.auth import HTTPBasicAuth
from requests import codes
import logging

import payload
import sync
from . exceptions import (IWorkflowException, IWorkflowNotFoundException)
from . import LOGGER_NAME

SERVICE_ENDPOINT = "/mgmt/cm/cloud/tenants/{0}/services/iapp/"

logger = logging.getLogger(LOGGER_NAME)


class IWorkflowService:

    def __init__(self, tenant_name, service_name, connection_params):
        self.tenant_name = tenant_name
        self.service_name = service_name
        self.connection_params = connection_params
        self.sslVerify = False

    def create_service(self,
                       template_name,
                       vars,
                       tables,
                       properties,
                       reference_hostname):

        data = payload.create_payload(self.tenant_name,
                                      self.service_name,
                                      template_name,
                                      vars,
                                      tables,
                                      properties,
                                      self._get_proto(),
                                      reference_hostname,
                                      self.connection_params.get("port"))

        logger.debug("Payload = {0}".format(json.dumps(data)))

        create_response = self._send_create_request(data)

        if create_response.status_code == codes.ok:
            logger.info("Create returns 200 OK")
            return
        error = self._retrive_error_message(create_response, "message")
        raise IWorkflowException(
            'Error received while polling service: {0}'.format(error)
        )

    def poll_service(self):
        logger.info("Poll service started")
        get_response = self._send_get_request()

        code = get_response.status_code

        if code == codes.ok:
            error = self._retrive_error_message(get_response, "error")
            if error:
                raise IWorkflowException(
                    'Error received while polling service: {0}'.format(error)
                )
            return
        elif code == codes.not_found:
            error = self._retrive_error_message(get_response, "message")
            raise IWorkflowNotFoundException(
                'Error received while polling service: {0}'.format(error)
            )

        raise IWorkflowException(
            "An unexpected HTTP response code = {} has been received"
            .format(code))

    def delete_service(self):
        delete_response = self._send_delete_request()

        code = delete_response.status_code

        if code == codes.ok:
            logger.info("Service {0} deleted".format(self.service_name))
            return
        else:
            raise IWorkflowException(
                "Cannot delete service {0}".format(self.service_name))

    def _send_create_request(self, data):
        url = self._create_url()
        logger.info(url)
        return requests.post(url=url,
                             json=data,
                             headers=self._get_headers(),
                             auth=self._get_auth(),
                             verify=self.sslVerify)

    def _send_get_request(self):
        url = self._get_url()
        logger.info(url)
        return requests.get(url=url,
                            headers=self._get_headers(),
                            auth=self._get_auth(),
                            verify=self.sslVerify)

    def _send_delete_request(self):
        url = self._get_url()
        logger.info(url)
        return requests.delete(url=url,
                               headers=self._get_headers(),
                               auth=self._get_auth(),
                               verify=self.sslVerify)

    def _create_url(self):
        endpoint = SERVICE_ENDPOINT.format(self.tenant_name)
        return "{0}://{1}:{2}{3}".format(
            self._get_proto(),
            self.connection_params.get("ip"),
            self.connection_params.get("port"),
            endpoint)

    def _get_url(self):
        endpoint = SERVICE_ENDPOINT.format(self.tenant_name)
        return "{0}://{1}:{2}{3}{4}".format(
            self._get_proto(),
            self.connection_params.get("ip"),
            self.connection_params.get("port"),
            endpoint,
            self.service_name)

    @staticmethod
    def _get_headers():
        return {
            'Content-Type': 'application/json',
            'Cache-Control': "no-cache"
        }

    def _get_auth(self):
        return HTTPBasicAuth(self.connection_params.get("user"),
                             self.connection_params.get("password"))

    @staticmethod
    def _retrive_error_message(resp, key):
        msg = ""
        try:
            json_response = resp.json()
            if json_response:
                msg = json_response.get(key)
        except Exception:
            logger.debug("No {0} key in the response".format(key))
            msg = 'no error message'
        return msg

    def _get_proto(self):
        if self.connection_params.get('use_ssl'):
            return 'https'
        return 'http'

    @staticmethod
    def sync(bigip_ip,
             sync_group,
             user,
             password,
             retry_timer):
        sync.do_sync(bigip_ip, sync_group, user, password, retry_timer)
