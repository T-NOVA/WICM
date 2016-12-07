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

import logging
import configparser
from flask import Flask, request, jsonify
from vtn import VtnWrapper
from database.database import db
import database.nap as nap
import database.nfvi as nfvi
import database.service as service
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=('%(asctime)s - '
                                                 '%(levelname)s - %(message)s'))

config = configparser.ConfigParser()
config.read('./wicm.ini')

if not config.getboolean('default', 'verbose'):
    logger.setLevel(logging.INFO)

logger.info('Starting..')

mysql_connect = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
    config.get('database', 'username'),
    config.get('database', 'password'),
    config.get('database', 'host'),
    config.getint('database', 'port'),
    config.get('database', 'name')
)

logger.debug('Database connection string: {}'.format(mysql_connect))

logger.debug('OpenDaylight connection {}:{}@{}:{}'.format(
    config.get('opendaylight', 'host'),
    config.getint('opendaylight', 'port'),
    config.get('opendaylight', 'username'),
    config.get('opendaylight', 'password')
))

vtn = VtnWrapper(
    config.get('opendaylight', 'host'),
    config.get('opendaylight', 'port'),
    config.get('opendaylight', 'username'),
    config.get('opendaylight', 'password')
)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mysql_connect
app.config['SQLALCHEMY_POOL_RECYCLE'] = 299  # compatibility with MariaDB
db.init_app(app)


@app.route('/nap', methods=['POST', 'GET', 'DELETE'], strict_slashes=False)
@app.route('/nap/<string:mkt_id>', methods=['GET', 'DELETE'],
           strict_slashes=False)
def nap_request(mkt_id=None):

    if request.method == 'POST':
        nap_request = request.json
        logger.info('Request to create NAP: {}'.format(nap_request))

        client_mkt_id = nap_request['nap']['client_mkt_id']
        mkt_id = nap_request['nap']['mkt_id']
        ce = (nap_request['nap']['switch'], nap_request['nap']['ce_port'],
              nap_request['nap']['ce_transport']['vlan_id'])
        pe = (nap_request['nap']['switch'], nap_request['nap']['pe_port'],
              nap_request['nap']['pe_transport']['vlan_id'])

        result = jsonify({'inserted': nap.put(client_mkt_id, mkt_id,
                                              ce, pe)}), 201

        vtn.nap_create(client_mkt_id, mkt_id, ce, pe)

    elif request.method == 'DELETE':
        logger.info('Request to delete NAP: {}'.format(
            'id -> {}'.format(mkt_id) if mkt_id else 'All NAPs'))

        nap_info = nap.get(mkt_id)
        result = nap.delete(mkt_id)
        vtn.nap_delete(nap_info[0]['client_mkt_id'],
                       nap_info[0]['mkt_id'])

        result = jsonify({'deleted': result}), 200
    else:
        logger.info('Request to get NAP: {}'.format(
            'id -> {}'.format(mkt_id) if mkt_id else 'All NAPs'))

        result = jsonify({'naps': nap.get(mkt_id)}), 200
    return result


@app.route('/nfvi', methods=['POST', 'GET', 'DELETE'], strict_slashes=False)
@app.route('/nfvi/<string:mkt_id>', methods=['GET', 'DELETE'],
           strict_slashes=False)
def nfvi_request(mkt_id=None):

    if request.method == 'POST':
        nfvi_request = request.json
        logger.info('Request to create NFVI-POP: {}'.format(nfvi_request))

        mkt_id = nfvi_request['nfvi']['mkt_id']
        port = (nfvi_request['nfvi']['switch'], nfvi_request['nfvi']['port'])

        result = jsonify({'inserted': nfvi.put(mkt_id, port)}), 201
    elif request.method == 'DELETE':

        #  TODO: Delete bridge @ ODL!
        logger.info('Request to delete NFVI-POP: {}'.format(
            'id -> {}'.format(mkt_id) if mkt_id else 'All NFVI-PoPs'))

        result = jsonify({'deleted': nfvi.delete(mkt_id)}), 200
    else:
        logger.info('Request to get NFVI-POP: {}'.format(
            'id -> {}'.format(mkt_id) if mkt_id else 'All NFVI-PoPs'))

        result = jsonify({'nfvis': nfvi.get(mkt_id)}), 200

    return result


@app.route('/vnf-connectivity', methods=['POST'], strict_slashes=False)
def service_request_post():
    try:

        service_request = request.json
        logger.info('Request to create service: {}'.format(service_request))

        ns_instance_id = service_request['service']['ns_instance_id']
        client_mkt_id = service_request['service']['client_mkt_id']
        nap_id = service_request['service']['nap_mkt_id']
        ce_pe_nfvi_ids = service_request['service']['ce_pe']
        pe_ce_nfvi_ids = service_request['service']['pe_ce']

        allocated = service.post(client_mkt_id, ns_instance_id, nap_id,
                                 ce_pe_nfvi_ids, pe_ce_nfvi_ids)
    except KeyError as ex:
        logger.error('Request to create service failed: must include {}'
                     .format(str(ex)))
        return jsonify({'error': 'Request must include {:s}'.
                        format(str(ex))}), 400

    except AttributeError:
        logger.error('Request to create service failed: Bad value for '
                     'nap_mkt_id or nfvi_mkt_id')
        return jsonify({'error': 'Bad value for nap_mkt_id or nfvi_mkt_id'}),\
            400
    except IndexError:
        logger.error('Request to create service failed: No Vlans!')
        return jsonify({'error': 'No vlans available'}), 500

    except IntegrityError:
        logger.error('Request to create service failed:'
                     'ns_instance_id {} already in use!'.format(ns_instance_id))
        return jsonify({'error': 'ns_instance_id "{}" already in use!'
                        .format(ns_instance_id)}), 400
    log_string = ''
    result = {'allocated': {
        'ns_instance_id': ns_instance_id,
        'ce_pe': [],
        'pe_ce': [],
    }}

    log_string += 'ce_pe: '

    for hop in allocated['ce_pe']:
        log_string += 'nfvi_id: "{}" vlan_id: "{}"'.\
            format(hop['nfvi_mkt_id'], hop['vlan_id'])

        result['allocated']['ce_pe'].append({
            'nfvi_id': hop['nfvi_mkt_id'],
            'transport': {
                'type': 'vlan',
                'vlan_id':  hop['vlan_id'],
            }})

    log_string += 'pe_ce: '
    for hop in allocated['pe_ce']:
        log_string += 'nfvi_id: "{}" vlan_id: "{}"'.\
            format(hop['nfvi_mkt_id'], hop['vlan_id'])

        result['allocated']['pe_ce'].append({
            'nfvi_id': hop['nfvi_mkt_id'],
            'transport': {
                'type': 'vlan',
                'vlan_id':  hop['vlan_id'],
            }})

    logger.info('Allocated vlans\n{}\n'.format(log_string))

    return jsonify(result), 201


@app.route('/vnf-connectivity', methods=['GET'], strict_slashes=False)
@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['GET'],
           strict_slashes=False)
def service_request_get(ns_instance_id=None):
    logger.info('Request to get Service: {}'.format('id -> {}'.format(
        ns_instance_id) if ns_instance_id else 'All Services'))

    return jsonify({'services': service.get(ns_instance_id)}), 200


@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['PUT'],
           strict_slashes=False)
def service_request_put(ns_instance_id=None):
    try:
        logger.info('Request enable Service: {}'.format(ns_instance_id))

        service_info = service.get(ns_instance_id)[0]
    except Exception:
        logger.error('Request enable Service {} failed : Service not found'
                     .format(ns_instance_id))

        return jsonify({'error': 'Service {} not found!'
                        .format(ns_instance_id)}), 400

    if service_info['status'] != 'ALLOCATED':
        logger.error(('Request enable Service {} failed : Service '
                      'not in ALLOCATED state').format(ns_instance_id))

        return jsonify({'error': 'Service {} is not in ALLOCATED state!'
                        .format(ns_instance_id)}), 400
    try:
        ce_pe = []
        for hop in service_info['ce_pe']:
            nfvi_info = nfvi.get(hop['nfvi_mkt_id'])[0]

            ce_pe.append(((nfvi_info['switch'], nfvi_info['port'],
                           hop['transport']['vlan_id'])))

        pe_ce = []
        for hop in service_info['pe_ce']:
            nfvi_info = nfvi.get(hop['nfvi_mkt_id'])[0]

            pe_ce.append(((nfvi_info['switch'], nfvi_info['port'],
                           hop['transport']['vlan_id'])))


        vtn.chain_create(service_info['client_mkt_id'],
                         service_info['ns_instance_id'],
                         service_info['nap_mkt_id'],
                         ce_pe, pe_ce)
    except Exception as ex:
        logger.error('Request enable Service {} failed VTN Manager: {}'
                     .format(ns_instance_id, ex))
        return jsonify({'error': 'Unable to put redirection in place!'}), 500

    logger.info('Service: {} enabled!'.format(ns_instance_id))
    service.set_status(ns_instance_id, 'ACTIVE')

    return jsonify({'activated': {'ns_instance_id': ns_instance_id}}), 201


@app.route('/vnf-connectivity/<string:ns_instance_id>', methods=['DELETE'],
           strict_slashes=False)
def service_request_delete(ns_instance_id=None):
    try:
        logger.info('Request delete Service: {}'.format(ns_instance_id))

        service_info = service.get(ns_instance_id)[0]
    except Exception:
        logger.error('Request delete Service {} failed : Service not found'
                     .format(ns_instance_id))
        return jsonify({'error': 'Service {} not found!'
                        .format(ns_instance_id)}), 400

    if service_info['status'] not in ['ALLOCATED', 'ACTIVE']:

        logger.error(('Request delete Service {} failed : Service'
                     'not in deletable state').format(ns_instance_id))

        return jsonify({'error': 'Service {} is not in deletable state!'
                        .format(ns_instance_id)}), 400

    service.set_status(ns_instance_id, 'TERMINATING')

    if service_info['status'] == 'ACTIVE':
        vtn.chain_delete(service_info['client_mkt_id'], ns_instance_id,
                         service_info['nap_mkt_id'])

    service.delete_service(ns_instance_id)
    logger.info('Service: {} deleted!'.format(ns_instance_id))
    return jsonify({'deleted': {'ns_instance_id': ns_instance_id}}), 200


@app.route('/reset_db', methods=['DELETE'])
def reset_db():
    logger.info('Request to delete the database!')

    db.drop_all()
    db.create_all()
    return 'ok', 200


@app.route("/")
def hello():
    logger.info('ola!')
    return "WICM!!"
