#!/usr/bin/python

#
# This is the main script for the docker.
# It iterates recursively over /_nodes/stats and retrieves all numerical metrics
#
# Written by Roi Rav-Hon @ Logz.io (roi@logz.io)
#
# Params:
#   Mandatory:
#       GRAPHITE - The graphite server to send metrics to
#       ELASTICSEARCH_ADDR - The elasticsearch cluster to monitor
#
#   Optional:
#       ELASTICSEARCH_PROTOCOL: http or https. Defaults to http.
#       ELASTICSEARCH_USER_NAME: Elasticsearch user name to use for basic auth
#       ELASTICSEARCH_PASSWORD: Elasticsearch password to use for basic auth
#       GRAPHITE_PREFIX - The prefix under graphite the metrics should be placed in (Default: Elasticsearch)
#       GRAPHITE_PROTOCOL - The protocol used to send data to graphite (Default: pickle. Can be either pickle or plaintext)
#       GRAPHITE_PORT - Graphite port (Default: 2004)
#       INTERVAL_SECONDS - The sample interval (Default: 10)
#       BULK_SIZE - The amount of metrics to be sent in each bulk request (Default: 50)
#       MAX_RETRY_BULK - The number of repeated attempts to send a bulk upon IOError failure (Default: 3)


import os
import pickle
import re
import socket
import struct
import sys
from time import sleep, time

import requests

# Get mandatory variables
elasticsearchAddr = os.getenv('ELASTICSEARCH_ADDR')
graphite = os.getenv('GRAPHITE')

# Gets optional variables
elasticsearch_port = os.getenv('ELASTICSEARCH_PORT', '9200')
elasticsearch_protocol = os.getenv('ELASTICSEARCH_PROTOCOL', 'http').lower()
elasticsearch_user_name = os.getenv('ELASTICSEARCH_USER_NAME', '')
elasticsearch_password = os.getenv('ELASTICSEARCH_PASSWORD', '')
graphite_prefix = os.getenv('GRAPHITE_PREFIX', "Elasticsearch")
graphite_port = os.getenv('GRAPHITE_PORT', '2004')
graphite_protocol = os.getenv('GRAPHITE_PROTOCOL', 'pickle')
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

if elasticsearch_protocol not in ['http', 'https']:
    print ("#############################################################################################")
    print ("Please provide a valid elasticsearch protocol: http or https")
    print ("#############################################################################################")

    sys.exit(1)

if graphite_protocol not in ['pickle', 'plaintext']:
    print ("#############################################################################################")
    print ("Please provide a valid graphite protocol: pickle or plaintext")
    print ("#############################################################################################")

    sys.exit(1)


# Query the cluster root once, to get the cluster name
clusterRoot = requests.get("{0}://{1}:9200/".format(elasticsearch_protocol, elasticsearchAddr), auth=(elasticsearch_user_name, elasticsearch_password)).json()
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

def tuples_to_lines(metrics_tuples):
    lines = []
    for metric_tuple in metrics_tuples:
        lines.append("{0} {1} {2}".format(metric_tuple[0], metric_tuple[1][1], metric_tuple[1][0]))

    return lines

def send_to_graphite(metrics, sock):
    curr_try = 0
    while True:
        try:
            if graphite_protocol == 'pickle':
                payload = pickle.dumps(metrics, protocol=2)
                header = struct.pack("!L", len(payload))
                message = header + payload
            else:
                metricslines = tuples_to_lines(metrics)
                message = '\n'.join(metricslines) + '\n'

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
    nodesJson = requests.get("{0}://{1}:{2}/_nodes/stats".format(elasticsearch_protocol, elasticsearchAddr, elasticsearch_port),
                             auth=(elasticsearch_user_name, elasticsearch_password)).json()

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
