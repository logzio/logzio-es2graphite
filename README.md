# Logzio es2graphite
This is the codebase for Logz.io's es2graphite docker.

## Overview
This docker will query your Elasticsearch cluster under /_node/stats and send any numerical metric found to graphite.

## Parameters
The following parameters need to be passed as environment variables to the container (-e ...=... -e ...=... ...)

|Name|Description|Mandatory|Default| 
|---|---|---|---|
|ELASTICSEARCH_ADDR|Your Elasticsearch cluster address to monitor (preferably, the ip/hostname of one of your client nodes) - the protocol and port are not required|Yes|-|
|GRAPHITE|The graphite server the metrics should end up in|Yes|-|
|GRAPHITE_PREFIX|The prefix under graphite you want your metrics in. We will add the cluster name, and the node name after that|No|Elasticsearch|
|GRAPHITE_PORT|Graphite pickle port|No|2004|
|INTERVAL_SECONDS|The frequency in which Elsaticsearch is to be sampled (preferably, the same value as your graphite configuration)|No|10|
|BULK_SIZE|The amount of metrics to be sent in each bulk request|No|50|
|MAX_RETRY_BULK|The number of repeated attempts to send a bulk that failed on IOError (originated from graphite)|No|3|
