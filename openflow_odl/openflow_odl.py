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

import sys
from json import dumps, loads
from requests import delete, put, get

class Conf_odl():

	def __init__(self, address, auth):
		self.address = address
		self.auth = auth
		self.headers = {
			'accept' : 'application/json', 
			'content-type': 'application/json'
		}

	def redirect(self, switch,table_id, flow_id, 
		flow_name,in_port, vlan_in, out_port, vlan_out,
		cookie=0xc001beef, priority=100, timeout=0):

		link = make_link(switch, table_id, flow_id)
		payload = redirect_payload(
			switch, table_id, flow_id, flow_name,
			in_port, vlan_in, out_port, vlan_out,
			cookie, priority, timeout)

		resp = put(self.address + link, auth=self.auth, headers=self.headers, data=dumps(payload))

		resp.raise_for_status()

	def delete(self, switch=None, table_id=None, flow_id=None):
		link = make_link(switch, table_id, flow_id)
		resp = delete(self.address + link, auth=self.auth, headers=self.headers)

		resp.raise_for_status()
def make_link(switch=None, table_id=None, flow_id=None):
	link = '/restconf/config/opendaylight-inventory:nodes'

	if switch is None:
		return link
	else:
		link = '{:s}/node/{:}'.format(link, switch)

	if table_id is None:
		return link
	else:
		link = '{:s}/table/{:}'.format(link, str(table_id))
	
	if flow_id is None:
		return link		
	else:
		link = '{:s}/flow/{:}'.format(link, flow_id)


	return link

def redirect_payload(switch,table_id, flow_id, 
	flow_name,in_port, vlan_in, out_port, vlan_out,
	cookie, priority, timeout):

	payload = {}

	payload['table_id'] = int(table_id)
	payload['id'] = int(flow_id)
	payload['flow-name'] = flow_name
	payload['cookie'] = cookie
	payload['priority'] = priority
	payload['hard-timeout'] = timeout

	payload['match'] = {
		'in-port': switch + ':' + str(in_port),
		'vlan-match': {
			'vlan-id': {
				'vlan-id': int(vlan_in),
				'vlan-id-present': True
			}
		}
	}

	payload['instructions'] = {'instruction': [
			{'apply-actions': {'action': 
			[
				{'order': 1,'output-action': {'max-length': 0,'output-node-connector': str(out_port)}},
				{'order': 0,'set-field': {'vlan-match': {'vlan-id': {'vlan-id': int(vlan_out),'vlan-id-present': True}}}},			
			]},
			'order': 0}]}

	payload = {'flow-node-inventory:flow' : payload}

	return payload

def main(argv):

	auth = ('admin', 'admin')
	headers = {'accept' : 'application/json', 'content-type': 'application/json'}
	cookie = 0xc001beef

	switches = ['openflow:1']
	switch = switches[0]
	table = 0
	address = 'http://193.136.92.184:8080'

	link = '/restconf/config/opendaylight-inventory:nodes/node/' + switch + '/table/' + str(table)
	delete(address + link, auth=auth, headers=headers)

	flow_id = 1
	payload = dumps(redirect_port_port(switch, table, flow_id, 'redirect_P1_P3', cookie, 10, 0, 1, 3))
	put(address + link + '/flow/' + str(flow_id), auth=auth, headers=headers, data=payload)

	flow_id = 2
	payload = dumps(redirect_port_port(switch, table, flow_id, 'redirect_P3_P1', cookie, 10, 0, 3, 1))
	put(address + link + '/flow/' + str(flow_id), auth=auth, headers=headers, data=payload)

	flow_id = 3
	payload = dumps(redirect_port_port(switch, table, flow_id, 'redirect_P2_P4', cookie, 10, 0, 2, 4))
	put(address + link + '/flow/' + str(flow_id), auth=auth, headers=headers, data=payload)

	flow_id = 4
	payload = dumps(redirect_port_port(switch, table, flow_id, 'redirect_P4_P2', cookie, 10, 0, 4, 2))
	put(address + link + '/flow/' + str(flow_id), auth=auth, headers=headers, data=payload)

	sleep(2.5)

	#link = link.replace('config', 'operational')

	switch_config = get(address + link, auth=auth, headers=headers).json()
	pprint(switch_config)



if __name__ == '__main__':
	main(sys.argv)