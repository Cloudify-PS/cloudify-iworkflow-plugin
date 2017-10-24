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

import logging
from functools import wraps

from cloudify import ctx as cfy_ctx
from cloudify.exceptions import NonRecoverableError

from iworkflow_sdk import LOGGER_NAME as SDK_LOGGER_NAME

CONNECTION_PARAMS = 'connection_params'
IWORKFLOW_NODE_TYPE = 'cloudify.iworkflow.iWorkflow'


class CfyLogHandler(logging.Handler):
    """
    A logging handler for Cloudify.
    A logger attached to this handler will result in logging being passed
    through to the Cloudify logger.
    """
    def __init__(self, ctx):
        """
        Constructor.
        :param ctx: current Cloudify context, may be any type of context
                    (operation, workflow...)
        """
        logging.Handler.__init__(self)
        self.ctx = ctx

    def emit(self, record):
        """
        Callback to emit a log record.
        :param record: log record to write
        :type record: logging.LogRecord
        """
        message = self.format(record)
        self.ctx.logger.log(record.levelno, message)


handler = CfyLogHandler(cfy_ctx)
logging.getLogger(SDK_LOGGER_NAME).addHandler(handler)


def get_relationships_by_type(ctx, type_name):
    return [rel for rel in ctx.instance.relationships
            if type_name in rel.type_hierarchy]


def get_connected_node(ctx):
    # >1 is not possible because the type that is looked for
    # inherits from contained_in type of relationship

    nodes = [rel.target.node
             for rel in
             get_relationships_by_type(
                 ctx,
                 'cloudify.relationships.contained_in')
             if IWORKFLOW_NODE_TYPE in rel.target.node.type_hierarchy]
    if not nodes:
        raise NonRecoverableError("The node must have a 'contained_in' "
                                  "relationship to a node of type '{0}'"
                                  .format(IWORKFLOW_NODE_TYPE))
    return nodes[0]


def load_connection_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs[CONNECTION_PARAMS] = get_connected_node(cfy_ctx).properties
        return func(*args, **kwargs)
    return wrapper
