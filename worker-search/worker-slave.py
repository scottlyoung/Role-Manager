#
# Worker server
#

import redis
import jsonpickle
import pika
import copy
import os
import pickle

'''
import googleapiclient.discovery
import google.oauth2.service_account as service_account
'''


machine_type = 'worker-slave'


def log(mssge, tag):

    route_key = os.uname().nodename + '.' + machine_type + '.' + tag

    channel.basic_publish(exchange='log', routing_key=route_key, body=mssge)


rabbitmqip = 'rabbitmq'
redisip = 'redis'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmqip))

channel = connection.channel()

channel.queue_declare(queue='toSlave', durable=True)


def solve(allocations, req, prefs):
    score = 0
    reqs = copy.deepcopy(req)
    #log("checking allocation: " + str(allocations), 'debug')
    for allocation in allocations:
        reqs[allocation[1]] -= 1
        score += prefs[allocation[0]][0][allocation[1]]*(1.1**prefs[allocation[0]][1])
    for key in reqs:
        if reqs[key] > 0:
            return (None, 0)
    #log('Allocation: ' + str(allocations), 'dump')
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
    #log('search Prefs: ' + str(prefs), 'debug')

    best = (None, 0)
    stack = [copy.deepcopy(allocations)]

    n = len(allocations)
    #log("n: " + str(n), 'debug')
    while stack:
        case = stack.pop()
        ind = 0
        ind_found = False
        while not ind_found:
            if ind == n:
                res = solve(copy.deepcopy(case), requirments, prefs)
                #log('search Result: ' + str(res), 'debug')
                if res[1] > best[1]:
                    best = res
                break
            if case[ind][1] is None:
                ind_found = True
            else:
                ind += 1
        if ind_found:
            member = case[ind][0]
            #log('search Prefs: ' + str(prefs), 'debug')
            #log('search Member: ' + str(member), 'debug')
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case)
                alloc[ind][1] = role
                stack.append(alloc)

    return best


def callback(ch, method, properties, body):
    body = pickle.loads(body)
    log("Decoded: " + str(body), 'debug')

    prob_id = body[0]
    task_id = body[1]
    task = body[2]

    log('Recived task: ' + str(task_id) + " for problem: " + str(prob_id), 'record')

    res = search(task)

    message = pickle.dumps((task_id, res))

    channel.basic_publish(exchange='fromSlave', routing_key=str(prob_id), body=message)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    log('Task: ' + task_id + ' finished', 'record')
    return


channel.basic_consume(queue='toSlave', on_message_callback=callback)

channel.start_consuming()
