#!/bin/sh

curl http://$1:5000/groups-add/group1
curl http://$1:5000/groups-add/group2

for i in {1..10}
do
    curl http://$1:5000/groups/group1/members-add/member$i
    curl http://$1:5000/groups/group2/members-add/member$i
done

for i in {1..4}
do
    curl http://$1:5000/groups/group1/roles-add/role$i
    curl http://$1:5000/groups/group2/roles-add/role$i
done

curl http://$1:5000/groups/group1/events-add/event1
curl http://$1:5000/groups/group2/events-add/event1
curl http://$1:5000/groups/group1/events-add/event2

for i in {1..4}
do
    curl http://$1:5000/groups/group1/events/event1/requirements-add/role$i/2
    curl http://$1:5000/groups/group2/events/event1/requirements-add/role$i/2
    curl http://$1:5000/groups/group1/events/event2/requirements-add/role$i/2
done

for i in {1..9}
do
    curl http://$1:5000/groups/group1/events/event1/members-add/member$i
done

for i in {1..9}
do
    curl http://$1:5000/groups/group1/events/event2/members-add/member$i
done

for i in {1..9}
do
    curl http://$1:5000/groups/group2/events/event1/members-add/member$i
done

for i in {1..10}
do
    for j in {1..3}
    do
        curl http://$1:5000/groups/group1/members/member$i/roles-add/role$j/$(( RANDOM % 9 + 2))
        curl http://$1:5000/groups/group2/members/member$i/roles-add/role$j/$(( RANDOM % 9 + 2))
    done
    curl http://$1:5000/groups/group1/members/member$i/roles-add/role4/1
    curl http://$1:5000/groups/group2/members/member$i/roles-add/role4/1
done