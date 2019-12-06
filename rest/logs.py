import pika
import sys

'''
import googleapiclient.discovery
import google.oauth2.service_account as service_account

credentials = service_account.Credentials.from_service_account_file(filename='key.json')
project = 'lab7-258019'
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

#Modified from code at https://www.rabbitmq.com/tutorials/tutorial-five-python.html

res2 = service.instances().get(project=project, zone='us-west1-a',instance='rabbitmq').execute()
rabbitmqip = res2['networkInterfaces'][0]['networkIP']
'''
rabbitmqip = 'rabbitmq'

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmqip))
channel = connection.channel()

channel.exchange_declare(exchange='log', exchange_type='topic')

result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

binding_keys = sys.argv[1:]
if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(
        exchange='log', queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))


channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()