from flask import Flask, request, Response
import redis
import pika
import jsonpickle
import os
import uuid


machine_type = 'rest'


def log(mssge, tag):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

    route_key = os.uname().nodename + '.' + machine_type + '.' + tag

    channel = connection.channel()
    channel.exchange_declare(exchange='log', exchange_type='topic')
    channel.basic_publish(exchange='log', routing_key=route_key, body=mssge)
    channel.close()


# Initialize the Flask application
app = Flask(__name__)

# route http posts to this method
@app.route('/groups-add/<string:group_name>', methods=['GET'])
def add_group(group_name):

    log('Request: add group: ' + group_name, 'record')

    db = redis.Redis(host='redis', db=0)
    exists = db.exists(group_name)
    if exists:
        status = 403
        response = "Group already exists\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.set(group_name, "")

    status = 201
    response = "Group created\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/members-add/<string:member_name>', methods=['GET'])
def add_member(group_name, member_name):

    log('Request: add member: ' + member_name + ' to group: ' + group_name, 'record')

    if member_name == "__score__":
        status = 404
        response = "__score__ is a disallowed name\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_hist = redis.Redis(host='redis', db=7)
    db = redis.Redis(host='redis', db=1)
    db_id = redis.Redis(host='redis', db=8)
    exists = db.hexists(group_name, member_name)
    if exists:
        status = 403
        response = "Member already exists in group\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = uuid.uuid4().hex

    db.hset(group_name, member_name, ID)
    db_hist.set(ID, 0)
    db_id.set(ID, member_name)

    status = 200
    response = "Member created in group\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/roles-add/<string:role_name>', methods=['GET'])
def add_role(group_name, role_name):

    log('Request: add role: ' + role_name + ' to group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db = redis.Redis(host='redis', db=2)
    exists = db.sismember(group_name, role_name)
    if exists:
        status = 403
        response = "Role already exists in group\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.sadd(group_name, role_name)
    status = 200
    response = "Role created in group\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/events-add/<string:event_name>', methods=['GET'])
def add_event(group_name, event_name):

    log('Request: add event: ' + event_name + ' to group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db = redis.Redis(host='redis', db=3)
    exists = db.hexists(group_name, event_name)
    if exists:
        status = 403
        response = "Event already exists in group\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.hset(group_name, event_name, uuid.uuid4().hex)
    status = 200
    response = "Event created in group\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/events/<string:event_name>/requirements-add/<string:role>/<int:needed>', methods=['GET'])
def add_requirment(group_name, event_name, role, needed):

    log('Request: add requirment: ' + role + " >= " + str(needed) +
        ' to event: ' + event_name + ' in group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_events = redis.Redis(host='redis', db=3)
    exists = db_events.hexists(group_name, event_name)
    if not exists:
        status = 404
        response = "Event not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = db_events.hget(group_name, event_name)

    db = redis.Redis(host='redis', db=4)
    exists = db.hexists(ID, role)
    if exists:
        status = 403
        response = "Role already required for event\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.hset(ID, role, needed)
    status = 200
    response = "Requirment added to event\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/events/<string:event_name>/members-add/<string:member_name>', methods=['GET'])
def add_attendance(group_name, event_name, member_name):

    log('Request: add member: ' + member_name + ' to event: ' + event_name +
        ' in group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_groups_mem = redis.Redis(host='redis', db=1)
    mem_ID = db_groups_mem.hget(group_name, member_name)

    db_events = redis.Redis(host='redis', db=3)
    exists = db_events.hexists(group_name, event_name)
    if not exists:
        status = 404
        response = "Event not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = db_events.hget(group_name, event_name)

    db = redis.Redis(host='redis', db=5)
    exists = db.hexists(ID, mem_ID)
    if exists:
        status = 403
        response = "Member already attending event\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.hset(ID, mem_ID, "")
    status = 200
    response = "Member added to event\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/members/<string:member_name>/roles-add/<string:role>/<int:pref>', methods=['GET'])
def add_job(group_name, member_name, role, pref):

    log('Request: add role: ' + role + " with pference " + str(pref) +
        ' to member: ' + member_name + ' in group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_roles = redis.Redis(host='redis', db=2)
    exists = db_roles.sismember(group_name, role)
    if not exists:
        status = 404
        response = "Role not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_members = redis.Redis(host='redis', db=1)
    exists = db_members.hexists(group_name, member_name)
    if not exists:
        status = 404
        response = "Member not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = db_members.hget(group_name, member_name)

    db = redis.Redis(host='redis', db=6)
    exists = db.hexists(ID, role)
    if exists:
        status = 403
        response = "Member already has role\n"
        return Response(response=response, status=status, mimetype="application/json")

    if pref < 1 or pref > 10:
        status = 403
        response = "Preference must be in range [0-10]\n"
        return Response(response=response, status=status, mimetype="application/json")

    db.hset(ID, role, pref)
    status = 200
    response = "Role added to member\n"
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/events/<string:event_name>', methods=['GET'])
def get_allocation(group_name, event_name):

    log('Request: retirve allocations for event: ' + event_name + ' in group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_events = redis.Redis(host='redis', db=3)
    exists = db_events.hexists(group_name, event_name)
    if not exists:
        status = 404
        response = "Event not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = db_events.hget(group_name, event_name)

    db = redis.Redis(host='redis', db=5)

    status = 200
    response = db.hgetall(ID)
    return Response(response=response, status=status, mimetype="application/json")


@app.route('/groups/<string:group_name>/events/<string:event_name>/compute', methods=['GET'])
def calc_allocation(group_name, event_name):

    log('Request: compute allocations for event: ' + event_name + ' in group: ' + group_name, 'record')

    db_groups = redis.Redis(host='redis', db=0)
    exists = db_groups.exists(group_name)
    if not exists:
        status = 404
        response = "Group not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    db_events = redis.Redis(host='redis', db=3)
    exists = db_events.hexists(group_name, event_name)
    if not exists:
        status = 404
        response = "Event not found\n"
        return Response(response=response, status=status, mimetype="application/json")

    ID = db_events.hget(group_name, event_name)

    message = ID

    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    channel.queue_declare(queue='toMaster', durable=True)

#    channel.exchange_declare(exchange='toWorker', exchange_type='direct')
#    channel.basic_publish(exchange='toWorker', routing_key='work', body=message)

    channel.basic_publish(exchange='', routing_key='toMaster', body=message, properties=pika.BasicProperties(delivery_mode=2))

    channel.close()

    status = 200
    response = "Procedure Started"
    return Response(response=response, status=status, mimetype="application/json")


# start flask app
app.run(host="0.0.0.0", port=5000)
