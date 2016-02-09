'''
	Copyright 2014-2016 PTIN

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License. 
'''

def redirect_all(table_id, flow_id, flow_name, cookie, priority, timeout, out_port):

	payload = {'flow-node-inventory:flow' : {}}
	payload['flow-node-inventory:flow'] = {}
	payload['flow-node-inventory:flow']['table_id'] = table_id
	payload['flow-node-inventory:flow']['id'] = flow_id
	payload['flow-node-inventory:flow']['flow-name'] = flow_name
	payload['flow-node-inventory:flow']['cookie'] = cookie
	payload['flow-node-inventory:flow']['priority'] = priority
	payload['flow-node-inventory:flow']['hard-timeout'] = timeout
	payload['flow-node-inventory:flow']['match'] = {}

	payload['flow-node-inventory:flow']['instructions'] = {'instruction': [
			{'apply-actions': {'action': 
			[
				{'order': 0,'output-action': {'max-length': 0,'output-node-connector' : out_port}},
			]},
			'order': 0}]}

	return payload

def redirect_vlan_port(switch,table_id, flow_id, flow_name, cookie, priority, timeout, vlan, in_port,out_port):
	
	payload = {'flow-node-inventory:flow' : {}} 
	payload['flow-node-inventory:flow']['table_id'] = table_id
	payload['flow-node-inventory:flow']['id'] = flow_id
	payload['flow-node-inventory:flow']['flow-name'] = flow_name
	payload['flow-node-inventory:flow']['cookie'] = cookie
	payload['flow-node-inventory:flow']['priority'] = priority
	payload['flow-node-inventory:flow']['hard-timeout'] = timeout
	payload['flow-node-inventory:flow']['match'] = {
		'in-port': switch + ':' + str(in_port),
		'vlan-match': {
			'vlan-id': {
				'vlan-id': vlan,
				'vlan-id-present': True
			}
		}
	}

	payload['flow-node-inventory:flow']['instructions'] = {'instruction': [
			{'apply-actions': {'action': 
			[
				{'order': 0,'output-action': {'max-length': 0,'output-node-connector': out_port}},
				{'order': 1,'output-action': {'max-length': 0,'output-node-connector': out_port}},
			]},
			'order': 0}]}

	return payload


def redirect_vlan_vid(table_id, flow_id, flow_name, cookie, priority, timeout, vlan_in, vlan_out,out_port):

	payload = {'flow-node-inventory:flow' : {}} 
	payload['flow-node-inventory:flow']['table_id'] = table_id
	payload['flow-node-inventory:flow']['id'] = flow_id
	payload['flow-node-inventory:flow']['flow-name'] = flow_name
	payload['flow-node-inventory:flow']['cookie'] = cookie
	payload['flow-node-inventory:flow']['priority'] = priority
	payload['flow-node-inventory:flow']['hard-timeout'] = timeout
	payload['flow-node-inventory:flow']['match'] = {
		'vlan-match': {
			'vlan-id': {
				'vlan-id': vlan_in,
				'vlan-id-present': True
			}
		}
	}

	return payload