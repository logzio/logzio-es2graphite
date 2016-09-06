# Logzio es2graphite
This is the codebase of Logz.io's es2graphite docker.

## Overview
This docker will query your Elasticsearch cluster under /_node/stats and send to graphite every numerical metric it finds.

## Parameters
Need to be passed as environment variables to the container (-e ...=... -e ...=... ...)
|Name|Description|Mandatory|Default| 
|---|---|---|---|
|ELASTICSEARCH_ADDR|Your Elasticsearch cluster address to monitor (Preferably the ip/hostname of one of your client nodes) - No protocol nor port required|Yes|-|
|GRAPHITE|The graphite server the metrics should end up in|Yes|-|
|GRAPHITE_PREFIX|The prefix under graphite you want you metrics in. We will add the cluster name, and the node name after that|No|Elasticsearch|
|GRAPHITE_PORT|Graphite pickle port|No|2004|
|INTERVAL_SECONDS|How frequent we should sample Elasticsearch. Preferably the same value as your graphite configured|No|10|
|BULK_SIZE|How many metrics we should send in each bulk request|No|50|
|MAX_RETRY_BULK|How many time we should retry to send a bulk that failed on IOError (originated from graphite)|No|3|
