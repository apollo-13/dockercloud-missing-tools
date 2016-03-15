# Terminate Unreacahble Docker Cloud Nodes for AWS Lambda)

This script terminates unreachable node in the cluster and scales the cluster back to the
original number of nodes afterwards. This in effect causes the service from the unreachable
node to be redeployed on another reachable node. The script should be executed periodically
(e.g. from AWS Lambda) to automatically restore cluster operation in case a node suddenly
becomes inoperable.

If unreachable node is found, the script then performs further checks if the node is still
unreachable. If the node is unreachable for more than 30 seconds, the script terminates the
node, and after successful termination scales up the node cluster by one node. The script
never terminates more than one node during single execution, so that the script can be
deployed in time restricted environments, such as AWS Lambda.

## Requirements

The script requires [python-docker-cloud]() Python library. It can be installed with:

    pip install python-dockercloud

To build a bundle zip file for deployment in AWS Lambda, you need *virtualenv*. It can
be installed in Debian based Linux distributions using the following command:

    sudo apt-get install python-virtualenv

## Usage

Docker Cloud credentials are set up inside the script code:

    dockercloud.user = "username"
    dockercloud.apikey = "apikey"

The script is designed to be executed from inside AWS lambda environment. To deploy
the script in AWS lambda, ensure the *virtualenv* in installed (see Requirements),
run *build.sh*, and deploy resulting terminate-unreachable-nodes.zip in AWS Lamdba using
the following configuration:

* Runtime: Python 2.7
* Handler: terminate-unreachable-nodes.handler
* Timeout: 5 min 0 sec
