#!/bin/bash

mn --clean

 screen -dmS mininet python /wicm/demo/vxlan_vtn_test.py

sleep 10s


 docker-compose -f /wicm/docker-compose.yml build
 docker-compose -f /wicm/docker-compose.yml up -d 

while [ "$( netstat -anp | grep 6633 -c)"  -lt 6 ]
do
    echo "Wainting for ODL to start up!"
    sleep 10s
done


while [ "$(curl -s -XDELETE localhost:12891/reset_db)"  != "ok" ]
do
    echo "Wainting for WICM start up!"
    sleep 10s
done

echo 'Done!'
