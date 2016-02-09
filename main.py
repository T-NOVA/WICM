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
from flask import Flask
from flask import request, jsonify

from database.database import db
import database.nfvi as nfvi
import database.nap as nap
import database.service as service
from openflow_odl.openflow_odl import Conf_odl
from odl_wrapper import nap_redirect,service_redirect

port = 12891
ip = "0.0.0.0"
odl_location = 'http://193.136.92.173:8080'
odl_auth = ('admin','admin')
mysql_connect = 'mysql://wicm:wicm@127.0.0.1:3306/wicm'


odl  = Conf_odl(odl_location, odl_auth)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mysql_connect
db.init_app(app)

@app.route('/reset_db',methods=['DELETE'])
def reset_db():
	db.drop_all()
	db.create_all()
	return 'ok', 200

@app.route('/reset_odl/<string:switch>',methods=['DELETE'])
def reset_odl(switch):
	odl.delete(switch)
	return 'ok', 200

@app.route('/nfvi', methods=['POST', 'GET', 'DELETE'], strict_slashes=False)
@app.route('/nfvi/<string:mkt_id>', methods=['GET', 'DELETE'], strict_slashes=False)
def nfvi_request(mkt_id=None):

	if request.method == 'POST':
		result = jsonify({'inserted' : nfvi.put(request.get_json())}), 201
	elif request.method == 'DELETE':
		result = jsonify({'deleted' : nfvi.delete(mkt_id)}), 200
	else:
		result = jsonify({'nfvis' : nfvi.get(mkt_id)}), 200

	return result

@app.route('/nap', methods=['POST', 'GET', 'DELETE'], strict_slashes=False)
@app.route('/nap/<string:mkt_id>', methods=['GET', 'DELETE'], strict_slashes=False)
def nap_request(mkt_id=None):

	if request.method == 'POST':
		result = jsonify({'inserted' : nap.put(request.get_json())}), 201
		mkt_id = request.get_json()['nap']['mkt_id']
		nap_redirect(odl, mkt_id)

	elif request.method == 'DELETE':
		result = jsonify({'deleted' : nap.delete(mkt_id)}), 200
	else:
		result = jsonify({'naps' : nap.get(mkt_id)}), 200

	return result

@app.route('/vnf-connectivity', methods=['POST'], strict_slashes=False)
def service_request_post():
	try:
		service.post(request.get_json())
	except KeyError, e:
		return jsonify({'error' : 'Request must include {:s}'.format(str(e))}), 400
	except AttributeError, e:
		raise e
		return jsonify({'error' : 'Bad value for nap_mkt_id or nfvi_mkt_id'}), 400

	ns_instance_id = request.get_json()['service']['ns_instance_id']

	service_info = service.get(ns_instance_id)[0]
	if service_info['status'] == 'ALLOCATED': 
		return jsonify(
			{'allocated' : {
				'ns_instance_id' : ns_instance_id,
				'ce_transport' : service_info['ce_transport'],
				'pe_transport' : service_info['pe_transport']
			}}) , 201
	else:
		return jsonify({'error' : 'Unable to alocate vlans!'}), 500

@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['PUT'], 
	strict_slashes=False)
def service_request_put(ns_instance_id=None):
	try:
		service_info = service.get(ns_instance_id)[0]
	except Exception, e:
		return jsonify({'error' : 'Service not found!'}), 400
	
	if service_info['status'] != 'ALLOCATED':
		return jsonify({'error' : 'Service is not in ALLOCATED state!'}), 400

	try:
		service_redirect(odl, ns_instance_id)
	except Exception, e:
		service.set_status(ns_instance_id, 'ERROR')
		return jsonify({'error' : 'Unable to put redirection in place!'}), 500

	nap_info = nap.get(service_info['nap_mkt_id'])[0]
	for flow in nap_info['flows']:
		odl.delete(flow['switch'], flow['of_table'], flow['of_id'])

	nap.delete_flows(service_info['nap_mkt_id'])

	service.set_status(ns_instance_id, 'ACTIVE')
	
	return jsonify({'activated' : {'ns_instance_id' : ns_instance_id}}), 201	

@app.route('/vnf-connectivity', methods=['GET'], strict_slashes=False)
@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['GET'], 
	strict_slashes=False)
def service_request_get(ns_instance_id=None):
	return jsonify({'services' : service.get(ns_instance_id)}), 200

@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['DELETE'], 
	strict_slashes=False)
def service_request_delete(ns_instance_id=None):
	try:
		service_info = service.get(ns_instance_id)[0]
	except Exception, e:
		return jsonify({'error' : 'Service not found!'}), 400

	if service_info['status'] not in ['ALLOCATED', 'ACTIVE']:
		return jsonify({'error' : 'Service is not in a deletable state!'}), 400

	if service_info['status'] == 'ACTIVE' :
		service.set_status(ns_instance_id, 'TERMINATING')
		nap_redirect(odl, service_info['nap_mkt_id'])
		
		for flow in service_info['flows']:
			odl.delete(flow['switch'], flow['of_table'], flow['of_id'])

		service.delete_flows(ns_instance_id)
	
	service.set_status(ns_instance_id, 'DELETED')

	return jsonify({'deleted' : {'ns_instance_id' : ns_instance_id}}), 200

if __name__ == '__main__':
	app.run(debug=True, host=ip, port=port) 