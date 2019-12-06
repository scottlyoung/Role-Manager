#
# Worker server
#

import redis
import jsonpickle
import pika
import copy
import os

'''
import googleapiclient.discovery
import google.oauth2.service_account as service_account
'''


machine_type = 'worker-master'


def log(mssge, tag):

    route_key = os.uname().nodename + '.' + machine_type + '.' + tag

    channel.basic_publish(exchange='log', routing_key=route_key, body=mssge)


rabbitmqip = 'rabbitmq'
redisip = 'redis'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmqip))

channel = connection.channel()

channel.exchange_declare(exchange='toWorker', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='toWorker', queue=queue_name, routing_key='work')


def solve(allocations, req, prefs):
    score = 0
    reqs = copy.deepcopy(req)
    for allocation in allocations:
        reqs[allocation[1]] -= 1
        score += prefs[allocation[0]][0][allocation[1]]*(1.1**prefs[allocation[0]][1])
    for key in reqs:
        if reqs[key] > 0:
            return (None, 0)
    return (allocations, score)


def search(body):
    allocations = body[0]
    requirments = body[1]
    prefs = body[2]

    best = (None, 0)
    stack = []

    n = len(allocations)
    while stack:
        case = stack.pop()
        if case >= int(n/2):
            res = solve(copy.deepcopy(case), requirments, prefs)
            if res[1] > best[1]:
                best = res
        else:
            ind = 0
            ind_found = False
            while not ind_found:
                if case[ind][1] is None:
                    ind_found = True
                ind += 1
            member = case[ind][1]
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case)
                alloc[ind][1] = role
                stack.append((alloc, case + 1))

    return best


def callback(ch, method, properties, body):
    ID = body.decode('utf-8')

    log('Recived request ' + ID, 'record')

    db_events = redis.Redis(host='redis', db=5)
    mem = db_events.hkeys(ID)

    allocations = []
    for member in mem:
        allocations.append([member, None])

    db_req = redis.Redis(host='redis', db=4)
    req = db_req.hgetall(ID)

    requirments = {}
    n = len(req)
    for i in range(int(n/2)):
        requirments[req[i*2]] = int(req[i*2 + 1])

    db_mem_roles = redis.Redis(host='redis', db=4)
    db_mem_hist = redis.Redis(host='redis', db=5)

    prefs = {}
    for member in mem:
        prefs[member] = ({}, db_mem_hist.get(member))
        roles = db_mem_roles.hgetall(member)
        n = len(roles)
        for i in range(int(n/2)):
            prefs[member][0][roles[i*2]] = roles[i*2+1]

    stack = [(allocations,0)]

    best = (None,0)

    n = len(allocations)
    while stack:
        case = stack.pop()
        if case[1] >= int(n/2):
            res = search((copy.deepcopy(case[0]), requirments, prefs))
            if res[1] > best[1]:
                best = res
        else:
            ind = 0
            ind_found = False
            while not ind_found:
                if case[0][ind][1] == None:
                    ind_found = True
                ind += 1
            member = case[0][ind][1]
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case[0])
                alloc[ind][1] = role
                stack.append((alloc, case[1] + 1))

    db_events = redis.Redis(host='redis', db=5)
    if best[0]:
        for allocation in best[0]:
            db_events.hset(ID, allocation[0], allocation[1])

    ch.basic_ack(delivery_tag=method.delivery_tag)
    log('Request ' + ID + 'finished', 'record')
    return


channel.basic_consume(queue_name, callback)

channel.start_consuming()
