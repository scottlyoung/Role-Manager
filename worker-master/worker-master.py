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
            #log("search case: " + str(case), 'debug')
            #log("search Ind: " + str(ind), 'debug')
            member = case[ind][0]
            log('search Member: ' + str(member), 'debug')
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case)
                alloc[ind][1] = role
                stack.append(alloc)

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
    requirments = db_req.hgetall(ID)

    db_mem_roles = redis.Redis(host='redis', db=6)
    db_mem_hist = redis.Redis(host='redis', db=7)

    prefs = {}
    for member in mem:
        prefs[member] = ({}, db_mem_hist.get(member))
        roles = db_mem_roles.hgetall(member)
        log("Roles: " + str(roles), 'debug')
        n = len(roles)
        for role in roles:
            prefs[member][0][role] = roles[role]

    stack = [(allocations,0)]

    best = (None,0)

    log('Prefs: ' + str(prefs), 'debug')

    n = len(allocations)
    while stack:
        case = stack.pop()
        if case[1] >= int(n/2):
            log('Requesting Search for case: ' + str(case), 'debug')
            res = search((copy.deepcopy(case[0]), requirments, prefs))
            log('Result: ' + str(res), 'debug')
            if res[1] > best[1]:
                best = res
        else:
            ind = 0
            ind_found = False
            while not ind_found:
                if case[0][ind][1] is None:
                    ind_found = True
                else:
                    ind += 1
            log('Ind: ' + str(ind), 'debug')
            log('Case: ' + str(case), 'debug')
            member = case[0][ind][0]
            log('Member: ' + str(member), 'debug')
            roles = prefs[member][0].keys()
            for role in roles:
                alloc = copy.deepcopy(case[0])
                alloc[ind][1] = role
                stack.append((alloc, case[1] + 1))

    db_events = redis.Redis(host='redis', db=5)
    db_mem_hist = redis.Redis(host='redis', db=7)
    if best[0]:
        for allocation in best[0]:
            mean = 0
            tot = 0
            for role in prefs[allocation[0]][0]:
                mean += float(prefs[allocation[0]][0][role])
                tot += 1
            val = float(prefs[allocation[0]][1]) + mean/tot - prefs[allocation[0]][0][allocation[1]]
            db_mem_hist.set(allocation[0], val)
            log("Updated member: " + str(allocation[0]) + "priority to " + str(val), 'record')
            db_events.hset(ID, allocation[0], allocation[1])
            log("Updated member: " + str(allocation[0]) + "for event: " + str(ID) + " to role: " + str(allocation[1]), 'record')

    ch.basic_ack(delivery_tag=method.delivery_tag)
    log('Request ' + ID + ' finished', 'record')
    return


channel.basic_consume(queue='toMaster', on_message_callback=callback)

channel.start_consuming()
