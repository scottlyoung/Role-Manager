#!/bin/sh

gcloud config set compute/zone us-west1-b
gcloud container clusters create --preemptible mykube