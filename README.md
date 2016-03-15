# Docker Cloud Missing Tools

Docker Cloud Missing Tools is a set of tools providing additional functionality that is required
for production level deployment inside the [Docker Cloud](http://cloud.docker.com/)
(formerly [Tutum](http://www.tutum.co/)).

## Redeploy with Health Check (health-check-redeploy)

This script sequentially redeploys a service, waiting for a successful health check pass on
the redeployed container before redeploying the next container in the sequence. This
effectively provides zero-downtime redeployment, provided that the service is deployed into
multiple containers.

## Terminate Unreachable Nodes for AWS Lambda (terminate-unreachable-nodes)

This script terminates unreachable node in the cluster and scales the cluster back to the
original number of nodes afterwards. This in effect causes the service from the unreachable
node to be redeployed on another reachable node. The script should be executed periodically
(e.g. from AWS Lambda) to automatically restore cluster operation in case a node suddenly
becomes inoperable.
