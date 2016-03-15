import dockercloud, time

dockercloud.user = "username"
dockercloud.apikey = "apikey"

unreachableCheckTimeout = 30
unreachableCheckInterval = 5

terminateCheckTimeout = 180
terminateCheckInterval = 5

def handler(event, context):

    nodes = dockercloud.Node.list(state='Unreachable')
    print "-- %d unreachable nodes found" % len(nodes)
    if not nodes:
        return

    nodes = monitorUnreachableNodes(nodes, unreachableCheckTimeout, unreachableCheckInterval)
    if not nodes:
        return

    node = nodes.pop(0)
    print "terminating node %s" % node.nickname
    node.delete()

    cluster = dockercloud.NodeCluster.fetch(node.node_cluster.strip('/').split('/')[-1])
    scaleUpCluster(cluster, terminateCheckTimeout, terminateCheckInterval)

    print "-- done"


def monitorUnreachableNodes(nodes, unreachableCheckTimeout, unreachableCheckInterval):

    startTimestamp = time.time()
    while (time.time() - startTimestamp) < unreachableCheckTimeout:
        print "check if nodes are still unreachable"
        nodes = [node for node in nodes if dockercloud.Node.fetch(node.uuid).state == 'Unreachable']
        if not nodes:
            print "-- nodes become reachable, not terminating them"
            break
        time.sleep(unreachableCheckInterval)
    return nodes


def scaleUpCluster(cluster, terminateCheckTimeout, terminateCheckInterval):

    print "scaling node cluster %s from %d to %d nodes" \
          % (cluster.name, cluster.target_num_nodes, cluster.target_num_nodes + 1)
    cluster.target_num_nodes += 1
    startTimestamp = time.time()
    while (time.time() - startTimestamp) < terminateCheckTimeout:

        try:
            cluster.save()
            break
        except dockercloud.api.exceptions.ApiError as e:
            messageTokens = str(e).split(' ')
            if len(messageTokens) < 2 or messageTokens[0] != 'Status' or messageTokens[1] != '422':
                raise e

        print "waiting for node termination"
        time.sleep(terminateCheckInterval)
