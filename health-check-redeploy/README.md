# Docker Cloud Redeploy with Health Check

This script sequentially redeploys a service, waiting for a successful health check pass on
the redeployed container before redeploying the next container in the sequence. This
effectively provides zero-downtime redeployment, provided that the service deployed in
multiple containers.

## Requirements

The script requires [python-docker-cloud]() Python library. It can be installed with:

    pip install python-dockercloud

## Usage

The script synopsis is:

```
DOCKERCLOUD_USER=username DOCKERCLOUD_APIKEY=apikey ./zero-downtime-redeploy.py
    -t=|--stack=stack-name
    -s=|--service=service-name
    [-h=|--health-check=off|http|tcp]
    [-p=|--health-check-port=port-number]
    [-u=|--health-check-url-path=url-path]
    [-t=|--health-check-timeout=timeout]
    [-m=|--maximum-execution-time=time]
```

The script expects Docker Cloud authentication details in DOCKERCLOUD_USER and
DOCKERCLOUD_APIKEY environment variables.

### Options

-k=stack-name, --stack=stack-name
: Stack name (required).

-s=service-name, --stack=service-name
: Service name (required).

-h=health-check-type, --health-check=health-check-type
: One of the following values: *off* (default) for no health check, *http* for
HTTP health check or *tcp* for TCP health check. HTTP health check performs GET
request, any response code other that 200 is considered unhealthy. TCP health check
attempts to open a TCP connection, failure to connect is considered unhealthy. 

-p=port-number, --health-check-port=port-number
: Inner port number (default 80) to perform TCP or HTTP health check on. The health check is
performed on the corresponding outer port.

-u=url-path, --health-check-url-path=url-path
: URL path to perform the HTTP health check on (default /). If you have a subpage for performing
the health check, specify its path here.

-t=timeout, --health-check-timeout=timeout
: Maximum time to perform the health check on single container for.
 
## Examples

Redeploy service *api-gateway* from stack *my-project* and perform HTTP health check
on the default port 80:

    ./zero-downtime-redeploy.py --stack=my-project --service=api-gateway --health-check=http

