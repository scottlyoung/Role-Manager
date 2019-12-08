#
# Worker server
#

import redis
import jsonpickle
import pika
import copy
import os
import uuid
import pickle

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

channel.queue_declare(queue='toMaster', durable=True)


def solve(allocations, req, prefs):
    score = 0
    reqs = copy.deepcopy(req)
    log("checking allocation: " + str(allocations), 'debug')
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
    for role in requirments:
        requirments[role] = float(requirments[role])
    prefs = body[2]
    for mem in prefs:
        prefs[mem] = (prefs[mem][0], float(prefs[mem][1]))
        for role in prefs[mem][0]:
            prefs[mem][0][role] = float(prefs[mem][0][role])
    log('search Prefs: ' + str(prefs), 'debug')

    best = (None, 0)
    stack = [copy.deepcopy(allocations)]

    n = len(allocations)
    log("n: " + str(n), 'debug')
    while stack:
        case = stack.pop()
        ind = 0
        ind_found = False
        while not ind_found:
            if ind == n:
                res = solve(copy.deepcopy(case), requirments, prefs)
                log('search Result: ' + str(res), 'debug')
                if res[1] > best[1]:
                    best = res
                break
            if case[ind][1] is None:
                ind_found = True
            else:
                ind += 1
        if ind_found:
            member = case[ind][0]
            log('search Member: ' + str(member), 'debug')
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case)
                alloc[ind][1] = role
                stack.append(alloc)

    return best


def task_callback(ch, method, properties, body, best, tasks):
    task_id, res = pickle.loads(body)
    if res[1] > best[0][1]:
        best[0] = res

    tasks[task_id] = True
    ch.basic_ack(delivery_tag=method.delivery_tag)
    if False not in tasks.values():
        ch.stop_consuming()
    return


def callback(ch, method, properties, body):
    ID = body.decode('utf-8')

    log('Recived request ' + ID, 'record')

    db_events = redis.Redis(host='redis', db=5)
    mem = db_events.hkeys(ID)

    allocations = []
    for member in mem:
        allocations.append([member, None])

    db_req = redis.Redis(host='redis', db=4)
    requirments = db_req.hgetall(ID)

    db_mem_roles = redis.Redis(host='redis', db=6)
    db_mem_hist = redis.Redis(host='redis', db=7)

    prefs = {}
    for member in mem:
        prefs[member] = ({}, db_mem_hist.get(member))
        roles = db_mem_roles.hgetall(member)
        #log("Roles: " + str(roles), 'debug')
        n = len(roles)
        for role in roles:
            prefs[member][0][role] = roles[role]

    stack = [(allocations, 0)]

    best = [(None, 0)]

    tasks = {}

    #log('Prefs: ' + str(prefs), 'debug')

    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue='toSlave', durable=True)

    channel.exchange_declare(exchange='fromSlave', exchange_type='direct')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='fromSlave', queue=queue_name, routing_key=str(ID))

    n = len(allocations)
    while stack:
        case = stack.pop()
        if case[1] >= int(n/2):
            #log('Requesting Search for case: ' + str(case), 'debug')
            task_id = uuid.uuid4().hex
            tasks[task_id] = False
            mssge = (ID, task_id, (copy.deepcopy(case[0]), requirments, prefs))
            log("Sending: " + str(mssge), 'debug')
            message = pickle.dumps(mssge)
            channel.basic_publish(exchange='', routing_key='toSlave', body=message, properties=pika.BasicProperties(delivery_mode=2))
        else:
            ind = 0
            ind_found = False
            while not ind_found:
                if case[0][ind][1] is None:
                    ind_found = True
                else:
                    ind += 1
            #log('Ind: ' + str(ind), 'debug')
            #log('Case: ' + str(case), 'debug')
            member = case[0][ind][0]
            #log('Member: ' + str(member), 'debug')
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case[0])
                alloc[ind][1] = role
                stack.append((alloc, case[1] + 1))

    # accept responses
    channel.basic_consume(queue_name, lambda ch, method, properties, body: task_callback(ch, method, properties, body, best, tasks))
    channel.start_consuming()

    db_events = redis.Redis(host='redis', db=5)
    db_mem_hist = redis.Redis(host='redis', db=7)
    if best[0][0]:
        for allocation in best[0][0]:
            mean = 0
            tot = 0
            for role in prefs[allocation[0]][0]:
                mean += float(prefs[allocation[0]][0][role])
                tot += 1
            #log("Allocation: " + str(allocation), 'debug')
            val = float(prefs[allocation[0]][1]) + mean/tot - float(prefs[allocation[0]][0][allocation[1]])
            db_mem_hist.set(allocation[0], val)
            log("Updated member: " + str(allocation[0]) + "priority to " + str(val), 'record')
            db_events.hset(ID, allocation[0], allocation[1])
            log("Updated member: " + str(allocation[0]) + "for event: " + str(ID) + " to role: " + str(allocation[1]), 'record')

    channel.close()
    ch.basic_ack(delivery_tag=method.delivery_tag)
    log('Request ' + ID + ' finished', 'record')
    return


channel.basic_consume(queue='toMaster', on_message_callback=callback)

channel.start_consuming()
