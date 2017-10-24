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


TENANT_TEMPLATE_REFERENCE_ENDPOINT = "/mgmt/cm/cloud/tenant/templates/iapp/"
TENANT_REFERENCE_ENDPOINT = "/mgmt/cm/cloud/tenants/"

PAYLOAD_KEY_NAME = "name"
PAYLOAD_KEY_TENANT_TEMPLATE = "tenantTemplateReference"
PAYLOAD_KEY_TENANT_REFERENCE = "tenantReference"
PAYLOAD_KEY_VARS = "vars"
PAYLOAD_KEY_TABLES = "tables"
PAYLOAD_KEY_PROPERTIES = "properties"
PAYLOAD_KEY_LINK = "link"


def create_payload(tenant_name,
                   service_name,
                   template_name,
                   vars,
                   tables,
                   properties,
                   proto,
                   reference_hostname,
                   reference_port):

    result = dict()

    result.update(_service_name(service_name))
    result.update(_tenant_template_reference(template_name, proto,
                                             reference_hostname,
                                             reference_port))
    result.update(_tenant_reference(tenant_name,
                                    proto,
                                    reference_hostname,
                                    reference_port))
    result.update(_vars(vars))
    result.update(_tables(tables))
    result.update(_properties(properties))

    return result


def _service_name(service_name):
    return {PAYLOAD_KEY_NAME: service_name}


def _tenant_template_reference(template_name,
                               proto,
                               reference_hostname,
                               reference_port):
    template_url = "{0}://{1}{2}{3}".format(
        proto,
        reference_hostname,
        TENANT_TEMPLATE_REFERENCE_ENDPOINT,
        template_name)
    template_reference = {
        PAYLOAD_KEY_LINK: template_url
    }

    return {
        PAYLOAD_KEY_TENANT_TEMPLATE: template_reference
    }


def _tenant_reference(tenant_name, proto, reference_hostname, reference_port):
    tenant_url = "{0}://{1}{2}{3}".format(
        proto,
        reference_hostname,
        TENANT_REFERENCE_ENDPOINT,
        tenant_name)
    tenat_reference = {
        PAYLOAD_KEY_LINK: tenant_url
    }

    return {PAYLOAD_KEY_TENANT_REFERENCE: tenat_reference}


def _vars(vars):
    return {PAYLOAD_KEY_VARS: vars}


def _tables(tables):
    return {PAYLOAD_KEY_TABLES: tables}


def _properties(properties):
    return {PAYLOAD_KEY_PROPERTIES: properties}
