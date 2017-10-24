# F5 iWorkflow Plugin

This plugin provides functionality for interacting with F5 iWorkflow.

Currently available functionality:

* Creating and deleting iWorkflow services

## Node Types

### `cloudify.iworkflow.iWorkflow`

Represents an iWorkflow instance, and encapsulates all information required
in order to interact with it. This information is provided by the available
properties (`ip`, `user`, `password`) etc.

### `cloudify.iworkflow.Service`

Represents an iWorkflow service that needs to be orchestrated.

The node type's properties hold all immutable information about the service.

The `create` operation receives additional information required for the creation
of the service, such as `vars`, `tables` and `properties`.

## Topology

By design, a blueprint orchestrating iWorkflow services should define:

* A node template of type `cloudify.iworkflow.iWorkflow`
* A node template of type `cloudify.iworkflow.Service`, contained within the `cloudify.iworkflow.iWorkflow` node template

Of course, you can define multiple `cloudify.iworkflow.iWorkflow` node templates, and
multiple `cloudify.iworkflow.Service` node templates, and assign containment relationships
according to your desired topology.
