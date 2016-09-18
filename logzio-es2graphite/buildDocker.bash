#!/bin/bash

TAG=logzio/es2graphite

docker build -t $TAG ./

echo "----------------------------------------"
echo "Built: $TAG"
echo "----------------------------------------"
