#!/bin/sh

curl http://$1:5000/groups-add/mmo

curl http://$1:5000/groups/mmo/members-add/dave
curl http://$1:5000/groups/mmo/members-add/bob
curl http://$1:5000/groups/mmo/members-add/eve
curl http://$1:5000/groups/mmo/members-add/alice
curl http://$1:5000/groups/mmo/members-add/joe

curl http://$1:5000/groups/mmo/roles-add/dps
curl http://$1:5000/groups/mmo/roles-add/tank
curl http://$1:5000/groups/mmo/roles-add/healer

curl http://$1:5000/groups/mmo/events-add/raid1
curl http://$1:5000/groups/mmo/events-add/raid2
curl http://$1:5000/groups/mmo/events-add/raid3

curl http://$1:5000/groups/mmo/events/raid1/requirements-add/dps/2
curl http://$1:5000/groups/mmo/events/raid1/requirements-add/tank/1
curl http://$1:5000/groups/mmo/events/raid1/requirements-add/healer/1

curl http://$1:5000/groups/mmo/events/raid2/requirements-add/dps/2
curl http://$1:5000/groups/mmo/events/raid2/requirements-add/tank/1
curl http://$1:5000/groups/mmo/events/raid2/requirements-add/healer/1

curl http://$1:5000/groups/mmo/events/raid3/requirements-add/dps/2
curl http://$1:5000/groups/mmo/events/raid3/requirements-add/tank/1
curl http://$1:5000/groups/mmo/events/raid3/requirements-add/healer/1


curl http://$1:5000/groups/mmo/events/raid1/members-add/dave
curl http://$1:5000/groups/mmo/events/raid1/members-add/bob
curl http://$1:5000/groups/mmo/events/raid1/members-add/eve
curl http://$1:5000/groups/mmo/events/raid1/members-add/alice
curl http://$1:5000/groups/mmo/events/raid1/members-add/joe

curl http://$1:5000/groups/mmo/events/raid2/members-add/dave
curl http://$1:5000/groups/mmo/events/raid2/members-add/bob
curl http://$1:5000/groups/mmo/events/raid2/members-add/eve
curl http://$1:5000/groups/mmo/events/raid2/members-add/alice

curl http://$1:5000/groups/mmo/events/raid3/members-add/dave
curl http://$1:5000/groups/mmo/events/raid3/members-add/bob
curl http://$1:5000/groups/mmo/events/raid3/members-add/eve
curl http://$1:5000/groups/mmo/events/raid3/members-add/alice
curl http://$1:5000/groups/mmo/events/raid3/members-add/joe

curl http://$1:5000/groups/mmo/members/joe/roles-add/dps/10
curl http://$1:5000/groups/mmo/members/joe/roles-add/tank/2

curl http://$1:5000/groups/mmo/members/alice/roles-add/dps/6
curl http://$1:5000/groups/mmo/members/alice/roles-add/healer/5

curl http://$1:5000/groups/mmo/members/eve/roles-add/dps/6
curl http://$1:5000/groups/mmo/members/eve/roles-add/tank/3

curl http://$1:5000/groups/mmo/members/bob/roles-add/dps/5

curl http://$1:5000/groups/mmo/members/dave/roles-add/dps/5
curl http://$1:5000/groups/mmo/members/dave/roles-add/healer/5
curl http://$1:5000/groups/mmo/members/dave/roles-add/tank/5

curl http://$1:5000/groups-add/tabletop
curl http://$1:5000/groups/tabletop/roles-add/dm
curl http://$1:5000/groups/tabletop/roles-add/player

curl http://$1:5000/groups/tabletop/members-add/dave
curl http://$1:5000/groups/tabletop/members-add/bob
curl http://$1:5000/groups/tabletop/members-add/carl
curl http://$1:5000/groups/tabletop/members-add/frank

curl http://$1:5000/groups/tabletop/events-add/oneshot

curl http://$1:5000/groups/tabletop/events/oneshot/members-add/dave
curl http://$1:5000/groups/tabletop/events/oneshot/members-add/bob
curl http://$1:5000/groups/tabletop/events/oneshot/members-add/carl
curl http://$1:5000/groups/tabletop/events/oneshot/members-add/frank