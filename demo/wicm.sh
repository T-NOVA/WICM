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

function del-tenant {
    curl --user "admin":"admin" -H "Content-type: application/json" -X POST \
	http://$ODL:8181/restconf/operations/vtn:remove-vtn \
	-d '{"input":{"tenant-name":"'"$1"'"}}'
}

ODL=localhost
wicm=localhost:5000

#del-tenant "c1"

#curl -X DELETE  ${wicm}/reset_db

curl -X POST ${wicm}/nap \
    -H "Content-type: application/json"  \
    -d '{"nap":{"mkt_id":"nap1","client_mkt_id":"c1","switch":"openflow:1","ce_port":1,"pe_port":2,"ce_transport":{"type":"vlan","vlan_id":100},"pe_transport":{"type":"vlan","vlan_id":100}}}'

curl -X POST ${wicm}/nap \
    -H "Content-type: application/json"  \
    -d '{"nap":{"mkt_id":"nap2","client_mkt_id":"c1","switch":"openflow:2","ce_port":1,"pe_port":2,"ce_transport":{"type":"vlan","vlan_id":200},"pe_transport":{"type":"vlan","vlan_id":200}}}'

curl -X POST ${wicm}/nfvi \
    -H "Content-type: application/json"  \
    -d '{"nfvi":{"mkt_id":"nfvi1","switch":"openflow:1","port":4}}'

curl -X POST ${wicm}/nfvi \
    -H "Content-type: application/json"  \
    -d '{"nfvi":{"mkt_id":"nfvi2","switch":"openflow:1","port":5}}'

curl -X POST ${wicm}/nfvi \
    -H "Content-type: application/json"  \
    -d '{"nfvi":{"mkt_id":"nfvi3","switch":"openflow:2","port":4}}'

curl -X POST ${wicm}/nfvi \
    -H "Content-type: application/json"  \
    -d '{"nfvi":{"mkt_id":"nfvi4","switch":"openflow:2","port":5}}'

curl -X POST ${wicm}/vnf-connectivity \
    -H "Content-type: application/json" \
    -d'{"service":{"ns_instance_id":"service1","client_mkt_id":"c1","nap_mkt_id":"nap1","ce_pe":["nfvi1","nfvi2"],"pe_ce":["nfvi1","nfvi3","nfvi4"]}}'

curl -X PUT ${wicm}/vnf-connectivity/service1 
#curl -X DELETE ${wicm}/vnf-connectivity/service1

curl -X POST ${wicm}/vnf-connectivity \
    -H "Content-type: application/json" \
    -d'{"service":{"ns_instance_id":"service2","client_mkt_id":"c1","nap_mkt_id":"nap2","ce_pe":["nfvi1","nfvi2","nfvi4"],"pe_ce":[]}}'

curl -X PUT ${wicm}/vnf-connectivity/service2 
#curl -X DELETE ${wicm}/vnf-connectivity/service2




