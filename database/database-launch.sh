#!/bin/sh
#
# This is the script you need to provide to launch a redis instance
# and and service
#

kubectl create deployment redis --image=redis:5.0.6
kubectl expose deployment/redis --port 6379 --target-port 6379