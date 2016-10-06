#!/bin/bash

#    Copyright 2014-2016 PTIN
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

mn --clean

 screen -dmS mininet python /wicm/demo/vxlan_vtn_test.py

sleep 10s


 docker-compose -f /wicm/docker-compose.yml build
 docker-compose -f /wicm/docker-compose.yml up -d 

while [ "$( netstat -anp | grep 6633 -c)"  -lt 6 ]
do
    echo "Waiting for ODL to start up!"
    sleep 10s
done


while [ "$(curl -s -XDELETE localhost:12891/reset_db)"  != "ok" ]
do
    echo "Waiting for WICM start up!"
    sleep 10s
done

echo 'Done!'
