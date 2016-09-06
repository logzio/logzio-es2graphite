#!/usr/bin/python

#
# This is the main script for the docker.
# It iterate recursively over /_nodes/stats and get all numerical metrics
#
# Written by Roi Rav-Hon @ Logz.io (roi@logz.io)
#
# Params:
#   Mandatory:
#       GRAPHITE - The graphite server to send metrics to
#       ELASTICSEARCH_ADDR - The elasticsearch cluster to monitor
#
#   Optional:
#       GRAPHITE_PREFIX - The prefix under graphite the metrics should be placed (Default: Elasticsearch)
#       GRAPHITE_PORT - Graphite pickle port (Default: 2004)
#       INTERVAL_SECONDS - What is the sample interval (Default: 10)
#       BULK_SIZE - How many metrics should each bulk to graphite holds (Default: 50)
#       MAX_RETRY_BULK - How many times should we re-try each bulk in case of IOError (Default: 3)


import os
import socket
import struct
import requests
import sys
import re
import pickle
from time import time, sleep

# Get mandatory variables
elasticsearchAddr = os.getenv('ELASTICSEARCH_ADDR')
graphite = os.getenv('GRAPHITE')

# Gets optional variables
graphite_prefix = os.getenv('GRAPHITE_PREFIX', "Elasticsearch")
graphite_port = os.getenv('GRAPHITE_PORT', '2004')
interval = os.getenv('INTERVAL_SECONDS', 10)
bulk_size = os.getenv('BULK_SIZE', 50)
max_retry_bulk = os.getenv('MAX_RETRY_BULK', 3)


# Check if both mandatory are set
if not all([elasticsearchAddr, graphite]):
    print ("#############################################################################################")
    print ("You must supply your ElasticSearch ip/hostname and Graphite server")
    print ("docker run .... -e ELASTICSEARCH_ADDR=<Elasticsearch Address> -e GRAPHITE=<Graphite address>....")
    print ("#############################################################################################")

    sys.exit(1)

# Query the cluster root once, to get the cluster name
clusterRoot = requests.get("http://{0}:9200/".format(elasticsearchAddr)).json()
clusterName = clusterRoot["cluster_name"]


def normalize_leaf(value):
    temp_value = value
    temp_value = re.sub(r'\.', '_', temp_value)
    temp_value = re.sub(r'=', '_', temp_value)
    temp_value = re.sub(r',', '_', temp_value)
    temp_value = re.sub(r'\"', '_', temp_value)

    return temp_value


def get_nested_values(values, path, graphite_list):
    if not (isinstance(values, dict)):

        try:
            graphite_list.append((path, (int(time()), float(values))))
        except (ValueError, TypeError):
            pass
        return

    for sub_node in values:
        get_nested_values(values[sub_node], path + "." + normalize_leaf(sub_node), graphite_list)


def send_to_graphite(metrics, sock):
    curr_try = 0
    while True:
        try:
            payload = pickle.dumps(metrics, protocol=2)
            header = struct.pack("!L", len(payload))
            message = header + payload
            sock.send(message)
            break

        except IOError, e:
            if e.errno == 32:

                # Socket closed, trying again..
                curr_try += 1
                sock = socket.socket()
                sock.connect((graphite, int(graphite_port)))

                if curr_try % max_retry_bulk == 0:
                    print "Gave up bulk after {} retries".format(curr_try)
                    break
            else:
                # Cant handle other things..
                raise IOError


# Looping until the end of times. or the containers at least.
while True:

    to_graphite = []

    # Getting nodes JVM usage
    nodesJson = requests.get("http://{0}:9200/_nodes/stats".format(elasticsearchAddr)).json()

    # Iterate over the nodes
    for currNode in nodesJson["nodes"]:
        get_nested_values(nodesJson["nodes"][currNode],
                          "{0}.{1}.{2}".format(graphite_prefix, clusterName, nodesJson["nodes"][currNode]["name"]),
                          to_graphite)

    curr_bulk = []

    try:
        sock = socket.socket()
        sock.connect((graphite, int(graphite_port)))

        for metric in to_graphite:
            curr_bulk.append(metric)

            if len(curr_bulk) % int(bulk_size) == 0:
                send_to_graphite(curr_bulk, sock)
                curr_bulk = []

        # Send the remaining bulk (if any)
        if len(curr_bulk) != bulk_size:
            send_to_graphite(curr_bulk, sock)

        sock.close()

    except Exception as e:
        print "Got exception while sending to graphite"
        print e

        try:
            sock.close()
        except:
            pass

    # Remove all lists, so we wont consume ram until next iteration
    del nodesJson
    del to_graphite
    del curr_bulk

    # Sleeps for interval!
    sleep(float(interval))
