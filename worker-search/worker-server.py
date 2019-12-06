#
# Worker server
#

import redis
import jsonpickle
import pika
from openalpr import Alpr
import os

'''
import googleapiclient.discovery
import google.oauth2.service_account as service_account
'''

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

#
# Sample code from: https://gist.github.com/moshekaplan/5330395
#


def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for gps_tag in value:
                    sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                    gps_data[sub_decoded] = value[gps_tag]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data


def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    deg_num, deg_denom = value[0]
    d = float(deg_num) / float(deg_denom)

    min_num, min_denom = value[1]
    m = float(min_num) / float(min_denom)

    sec_num, sec_denom = value[2]
    s = float(sec_num) / float(sec_denom)

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(exif_data, debug=False):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = gps_info.get("GPSLatitude")
        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":                     
                lat *= -1

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon *= -1
    else:
        if debug:
            print("No EXIF data")

    return lat, lon


def getLatLon(filename, debug=False):
    try:
        image = Image.open(filename)
        exif_data = get_exif_data(image)
        return get_lat_lon(exif_data, debug)
    except:
        return None


machine_type = 'worker'


def log(mssge, tag):

    route_key = os.uname().nodename + '.' + machine_type + '.' + tag

    channel.basic_publish(exchange='log', routing_key=route_key, body=mssge)

'''
credentials = service_account.Credentials.from_service_account_file(filename='key.json')
project = 'lab7-258019'
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

res1 = service.instances().get(project=project, zone='us-west1-a', instance='redis').execute()
redisip = res1['networkInterfaces'][0]['networkIP']
res2 = service.instances().get(project=project, zone='us-west1-a', instance='rabbitmq').execute()
rabbitmqip = res2['networkInterfaces'][0]['networkIP']
'''
rabbitmqip = 'rabbitmq'
redisip = 'redis'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmqip))

channel = connection.channel()

channel.exchange_declare(exchange='toWorker', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='toWorker', queue=queue_name, routing_key='work')


def callback(ch, method, properties, body):
    try:
        body = jsonpickle.decode(body.decode('utf-8'))

        log('Recived request ' + body['hash'], 'info')

        f = open('image.jpg', 'wb')
        f.write(body['img'])
        f.close()
        log('Wrote Image', 'debug')
        alpr = Alpr('us', '/etc/openalpr/openalpr.conf', '/usr/share/openalpr/runtime_data')
        res = getLatLon('image.jpg')
        log('Got lat lon', 'debug')
        if res is None:
            log('Error getting lat lon', 'debug')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log('Completion Acknowledged', 'debug')
            return

        lat, lon = res

        if lat is None:
            log('No lat lon', 'debug')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log('Completion Acknowledged', 'debug')
            return

        results = alpr.recognize_file('image.jpg')
        log('Alpr Ran', 'debug')
        if len(results['results']) == 0:
            log('No Plates Found', 'debug')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log('Completion Acknowledged', 'debug')
            return

        s = redis.Redis(host=redisip, db=1)
        for plate in results['results'][0]['candidates']:
            data = plate['plate'] + ':' + str(plate['confidence']) + ':' + str(lat) + ':' + str(lon)
            s.sadd(body['hash'], data)
            log('Stored ' + data, 'info')

        s = redis.Redis(host=redisip, db=3)
        for plate in results['results'][0]['candidates']:
            log('Stored ' + plate['plate'] + ' ' + body['hash'], 'info')
            s.sadd(plate['plate'], body['hash'])

        ch.basic_ack(delivery_tag=method.delivery_tag)
        log('Completion Acknowledged', 'debug')
        return
    except:
        log('An error has occured', 'error')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log('Completion Acknowledged', 'debug')
        return


channel.basic_consume(queue_name, callback)

channel.start_consuming()
