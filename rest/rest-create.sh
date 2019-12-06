#!/bin/sh

docker build -t gcr.io/rolemanager-260813/rest:$1 .
docker push gcr.io/rolemanager-260813/rest:$1
kubectl set image deployment/rest rest=gcr.io/rolemanager-260813/rest:$1