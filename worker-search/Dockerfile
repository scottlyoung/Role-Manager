FROM ubuntu:16.04
WORKDIR /worker
ADD worker-server.py /worker
RUN apt-get update
RUN apt-get install -y openalpr openalpr-daemon openalpr-utils libopenalpr-dev

RUN apt-get install -y python3 python3-pillow python3-openalpr python3-redis python3-pip
RUN pip3 install -U google-api-python-client pika jsonpickle google-auth-oauthlib
CMD python3 worker-server.py