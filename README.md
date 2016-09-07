# Logzio es2graphite
This is the codebase for Logz.io's es2graphite docker image.
[Docker Hub](https://hub.docker.com/r/logzio/es2graphite/)

## Overview
This docker container will query your Elasticsearch cluster under /_node/stats and send any numerical metric found to graphite.

## Parameters
The following parameters need to be passed as environment variables to the container (-e ...=... -e ...=... ...)

|Name|Description|Mandatory|Default| 
|---|---|---|---|
|ELASTICSEARCH_ADDR|Your Elasticsearch cluster address to monitor (preferably, the ip/hostname of one of your client nodes) - the protocol and port are not required|Yes|-|
|GRAPHITE|The graphite server the metrics should end up in|Yes|-|
|GRAPHITE_PREFIX|The prefix under graphite you want your metrics in. We will add the cluster name, and the node name after that|No|Elasticsearch|
|GRAPHITE_PORT|Graphite pickle port|No|2004|
|INTERVAL_SECONDS|The frequency in which Elasticsearch is to be sampled (preferably, the same value as your graphite configured metrics interval)|No|10|
|BULK_SIZE|The amount of metrics to be sent in each bulk request|No|50|
|MAX_RETRY_BULK|The number of repeated attempts to send a bulk that failed on IOError (originated from graphite)|No|3|


## Path in graphite
This docker container will take the parameter GRAPHITE_PREFIX you supplied (or the default) and add the cluster name, and node name to the path.
For example:
```
Elasticsearch.prefix.MY_ES_CLUSTER.node1.jvm.mem.heap_used_percent
```

## Run Examples
```bash
docker run --restart=always -d --name="es2graphite" \
                        -e ELASTICSEARCH_ADDR="es-client.internal.domain.example" \
                        -e GRAPHITE="graphite.internal.domain.example" \
                        -e GRAPHITE_PREFIX="PROD.Elasticsearch" \
                        -e INTERVAL_SECONDS=20 \
                        -e BULK_SIZE=10 \
                        logzio/es2graphite
```


## Grafana Screenshots
![Dashboard prtscr 1](https://i.imgsafe.org/fe55084226.png)
![Dashboard prtscr 2](https://i.imgsafe.org/fe551c38d3.png)
![Dashboard prtscr 3](https://i.imgsafe.org/fe550e9a68.png)
![Dashboard prtscr 4](https://i.imgsafe.org/fe55159ae8.png)
