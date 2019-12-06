FROM debian:bullseye
RUN apt-get update
RUN apt-get install -y python3 python3-pip git
RUN pip3 install pillow jsonpickle redis pika
RUN pip3 install Flask google-api-python-client
WORKDIR /rest
ADD rest-server.py /rest
ADD logs.py /rest
EXPOSE 5000
CMD python3 rest-server.py