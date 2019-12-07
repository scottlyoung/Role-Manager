#!/bin/sh

docker build -t gcr.io/rolemanager-260813/master:$1 .
docker push gcr.io/rolemanager-260813/master:$1
kubectl set image deployment/master master=gcr.io/rolemanager-260813/master:$1