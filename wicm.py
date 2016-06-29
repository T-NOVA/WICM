import logging
from flask import Flask, request, jsonify
from vtn import VtnWrapper
from database.database import db
import database.nap as nap
import database.nfvi as nfvi
import database.service as service
from sqlalchemy.exc import IntegrityError

mysql_connect = 'mysql+mysqlconnector://wicm:wicm@biker:3300/wicm'

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=('%(asctime)s - '
                                                 '%(levelname)s - %(message)s'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mysql_connect
db.init_app(app)

vtn = VtnWrapper('biker', 8181)


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
        ce = (nfvi_request['nfvi']['switch'], nfvi_request['nfvi']['ce_port'])
        pe = (nfvi_request['nfvi']['switch'], nfvi_request['nfvi']['pe_port'])

        result = jsonify({'inserted': nfvi.put(mkt_id, ce, pe)}), 201
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
        nfvi_id = service_request['service']['nfvi_mkt_id']

        result = service.post(client_mkt_id, ns_instance_id, nap_id, [nfvi_id])
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

    logger.info('Allocated vlans ce:{} and pe:{} for ns: {}'.format(
        result[0][0], result[0][1], ns_instance_id))

    return jsonify(
        {'allocated': {
            'ns_instance_id': ns_instance_id,
            'ce_transport': {
                'type': 'vlan',
                'vlan_id':  result[0][0],
            },
            'pe_transport': {
                'type': 'vlan',
                'vlan_id':  result[0][1],
            }
        }}), 201


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

        nfvi_info = nfvi.get(service_info['nfvi_mkt_id'])[0]

        interfaces = [((nfvi_info['switch'],
                        nfvi_info['ce_port'],
                        service_info['ce_transport']['vlan_id']),
                       (nfvi_info['switch'],
                        nfvi_info['pe_port'],
                        service_info['pe_transport']['vlan_id']))]

        vtn.chain_create(service_info['client_mkt_id'],
                         service_info['ns_instance_id'],
                         service_info['nap_mkt_id'],
                         interfaces)
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
    vtn.chain_delete(service_info['client_mkt_id'], ns_instance_id)
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

if __name__ == "__main__":
    app.run(debug=True)
