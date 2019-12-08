FROM ubuntu:16.04
RUN apt-get update
RUN apt-get install -y python3 python3-pillow python3-openalpr python3-redis python3-pip
RUN pip3 install -U google-api-python-client pika jsonpickle google-auth-oauthlib
WORKDIR /worker
ADD worker-slave.py /worker
CMD python3 worker-slave.py