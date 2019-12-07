#!/bin/sh

kubectl create deployment rest --image=gcr.io/rolemanager-260813/rest:0.1.4
kubectl expose deployment rest --type=LoadBalancer --port 5000 --target-port 5000