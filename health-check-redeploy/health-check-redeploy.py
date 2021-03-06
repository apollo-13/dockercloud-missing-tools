#!/usr/bin/python

import dockercloud, getopt, json, requests, signal, socket, sys, time, websocket


class HealthCheckRedeploy:

    containers = []
    service = None
    websocket = None
    completedHealthChecks = 0

    healthCheck = 'off'
    healthCheckPort = 80
    healthCheckUrlPath = ''
    healthCheckTimeout = 600
    healthCheckContainersCount = None

    def __init__(self, stackName, serviceName):

        stacks = dockercloud.Stack.list(name=stackName)
        if len(stacks) == 0:
            raise Exception("Stack not found.")
        stack = stacks[0]

        services = dockercloud.Service.list(stack=stack.resource_uri, name=serviceName)
        if len(services) == 0:
            raise Exception("Service not found.")
        self.service = services[0]

    def start(self):

        print ">> starting redeploy"

        self.completedHealthChecks = 0
        self.containers = []

        for container in dockercloud.Container.list(service=self.service.resource_uri):
            if container.state in ['Running', 'Starting']:
                self.containers.append(container)

        self.containers.sort(key=lambda x: x.name)

        print "found containers %s" % ', '.join([container.name for container in self.containers])

        self.websocket = websocket.WebSocketApp(
            'wss://ws.cloud.docker.com/api/audit/v1/events',
            header=['Authorization: ' + dockercloud.auth.get_auth_header()['Authorization']],
            on_message=self.onMessage,
            on_error=self.onError,
            on_open=self.onOpen
        )
        self.websocket.run_forever()

    def redeployNext(self):
        if len(self.containers) == 0:
            print ">> redeploy finished successfully"
            self.websocket.close()
        else:
            container = self.containers.pop(0)
            print ">> redeploying " + container.name
            container.redeploy()

    def isNewContainer(self, containerMessage):
        for c in self.containers:
            if c.resource_uri == containerMessage['resource_uri']:
                return False
        return True

    def onMessage(self, ws, message):
        message = json.loads(message)
        if message['type'] == 'container' and message['state'] == 'Running' and self.service.resource_uri in message['parents']:
            if self.isNewContainer(message):
                container = dockercloud.Container.fetch(message['resource_uri'].strip('/').split('/')[-1])
                self.checkHealth(container)
                self.redeployNext()

    def onError(self, ws, error):
        ws.close()
        sys.exit(error)

    def onOpen(self, ws):
        self.redeployNext()

    def checkHealth(self, container):

        if self.healthCheckContainersCount is not None and self.completedHealthChecks >= self.healthCheckContainersCount:
            return

        if self.healthCheck in 'http':
            url = None
            for port in container.container_ports:
                if port['inner_port'] == self.healthCheckPort:
                    url = port['endpoint_uri']
            if not url:
                raise Exception("Port %d not found or not published, cannot perform HTTP health check." % self.healthCheckPort)
            url = url + self.healthCheckUrlPath.lstrip('/')
            print 'http health check on', url + ' ',
            self.checkHealthLoop(lambda: self.checkHealthHttp(url))

        elif self.healthCheck in 'tcp':
            outerPort = None
            for port in container.container_ports:
                if port['inner_port'] == self.healthCheckPort:
                    outerPort = port['outer_port']
            if not outerPort:
                raise Exception("Port %d not found or not published, cannot perform TCP health check." % self.healthCheckPort)
            print 'tcp health check on', container.public_dns + ':' + str(outerPort) + ' ',
            self.checkHealthLoop(lambda: self.checkHealthTcp(container.public_dns, outerPort))

        self.completedHealthChecks += 1;

    def checkHealthLoop(self, callback):

        startTimestamp = time.time()

        while (time.time() - startTimestamp) < self.healthCheckTimeout:

            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                if callback():                    
                    print ' OK'
                    return
            except Exception:
                pass
            time.sleep(1)

        sys.exit('Health check timeout')

    def checkHealthHttp(self, url):

        response = requests.get(url)
        return response.status_code == 200

    def checkHealthTcp(self, host, port):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock.connect_ex((host, port)) == 0

    def setHealthCheck(self, healthCheck):

        if healthCheck not in ['off', 'http', 'tcp']:
            sys.exit("Health check '%s' not implemented." % arg)

        self.healthCheck = healthCheck

    def setHealthCheckPort(self, healthCheckPort):
        
        self.healthCheckPort = healthCheckPort

    def setHealthCheckUrlPath(self, healthCheckUrlPath):

        self.healthCheckUrlPath = healthCheckUrlPath

    def setHealthCheckContainersCount(self, healthCheckContainersCount):

        self.healthCheckContainersCount = healthCheckContainersCount

    def setHealthCheckTimeout(self, healthCheckTimeout):
        
        self.healthCheckTimeout = healthCheckTimeout



def terminate(message):

    print 'Error:', message
    print
    print 'Usage: DOCKERCLOUD_USER=username DOCKERCLOUD_APIKEY=apikey ./zero-downtime-redeploy.py'
    print '    -t=|--stack=stack-name'
    print '    -s=|--service=service-name'
    print '    [-h=|--health-check=off|http|tcp]'
    print '    [-p=|--health-check-port=port-number]'
    print '    [-u=|--health-check-url-path=url-path]'
    print '    [-t=|--health-check-timeout=timeout]'
    print '    [-c=|--health-check-containers-count]'
    print '    [-m=|--maximum-execution-time=time]'
    sys.exit(1)


def onTimeout(signum, frame):

    sys.exit('Error: Script maximum execution time has been reached.')

service = None
stack = None

opts, args = getopt.getopt(
    sys.argv[1:],
    "s:k:h:p:u:t:c:m:",
    ["service=", "stack=", "health-check=", "health-check-port=", "health-check-url-path=", "health-check-timeout=", "health-check-containers-count", "maximum-execution-time="]
)

for opt, arg in opts:
    if opt in ('-s', '--service'):
        service = arg
    elif opt in ('-k', '--stack'):
        stack = arg

if service is None:
    terminate("Missing mandatory argument: --service")
if stack is None:
    terminate("Missing mandatory argument: --stack")

redeploy = HealthCheckRedeploy(stack, service)

for opt, arg in opts:
    if opt in ('-s', '--service'):
        pass
    elif opt in ('-k', '--stack'):
        pass
    elif opt in ('-h', '--health-check'):
        redeploy.setHealthCheck(arg)
    elif opt in ('-p', '--health-check-port'):
        redeploy.setHealthCheckPort(int(arg))
    elif opt in ('-u', '--health-check-url-path'):
        redeploy.setHealthCheckUrlPath(arg)
    elif opt in ('-t', '--health-check-timeout'):
        redeploy.setHealthCheckTimeout(int(arg))
    elif opt in ('-c', '--health-check-containers-count'):
        redeploy.setHealthCheckContainersCount(int(arg))
    elif opt in ('-m', '--maximum-execution-time'):
        signal.signal(signal.SIGALRM, onTimeout)
        signal.alarm(int(arg))
    else:
        terminate("Unknown option " + opt + ".")

redeploy.start()
