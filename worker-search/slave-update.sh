#!/bin/sh

docker build -t gcr.io/rolemanager-260813/slave:$1 .
docker push gcr.io/rolemanager-260813/slave:$1
kubectl set image deployment/slave slave=gcr.io/rolemanager-260813/slave:$1