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

import database.nap as nap
import database.service as service
import database.nfvi as nfvi

def nap_redirect(odl, mkt_id):

	nap_info = nap.get(mkt_id)[0]
	flows = nap.create_nap_flows(mkt_id)

	flow = flows[0]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'NAP_{:}_CE_PE'.format(mkt_id),
		nap_info['ce_port'], nap_info['ce_transport']['vlan_id'],  
		nap_info['pe_port'], nap_info['pe_transport']['vlan_id'])

	flow = flows[1]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'NAP_{:}_CE_PE'.format(mkt_id),
		 nap_info['pe_port'], nap_info['pe_transport']['vlan_id'],
		 nap_info['ce_port'], nap_info['ce_transport']['vlan_id'])

def service_redirect(odl, mkt_id):

	service_info = service.get(mkt_id)[0]
	nap_info = nap.get(service_info['nap_mkt_id'])[0]
	nfvi_info = nfvi.get(service_info['nfvi_mkt_id'])[0]

	#request new ids
	flows = service.create_service_flows(mkt_id)

	flow = flows[0]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'SERVICE_{:}_CE_NFVI'.format(mkt_id),
		nap_info['ce_port'], nap_info['ce_transport']['vlan_id'], 
		nfvi_info['ce_port'], service_info['ce_transport']['vlan_id'],
		priority=1000, cookie=0xc01dbabe)

	flow = flows[1]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'SERVICE_{:}_NFVI_CE'.format(mkt_id),
		nfvi_info['ce_port'], service_info['ce_transport']['vlan_id'], 
		nap_info['ce_port'], nap_info['ce_transport']['vlan_id'],
		priority=1000, cookie=0xc01dbabe)

	flow = flows[2]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'SERVICE_{:}_PE_NFVI'.format(mkt_id),
		nap_info['pe_port'], nap_info['pe_transport']['vlan_id'], 
		nfvi_info['pe_port'], service_info['pe_transport']['vlan_id'],
		priority=1000, cookie=0xc01dbabe)

	flow = flows[3]
	odl.redirect(
		flow['switch'], flow['of_table'], flow['of_id'], 
		'SERVICE_{:}_NFVI_PE'.format(mkt_id),
		nfvi_info['pe_port'], service_info['pe_transport']['vlan_id'], 
		nap_info['pe_port'], nap_info['pe_transport']['vlan_id'],
		priority=1000, cookie=0xc01dbabe)