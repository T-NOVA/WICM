'''
<<<<<<< HEAD
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
from .database import db
from .nfvi import NFVI
from .nap import NAP
from .interface import Interface
from .port import Port
from sqlalchemy.exc import IntegrityError

available_vlans = set(range(400, 600))


class ServiceInterface(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    service_refid = db.Column(db.Integer, db.ForeignKey('service.id'),
                              nullable=False)

    index = db.Column(db.Integer, nullable=False)

    nfvi_refid = db.Column(db.Integer, db.ForeignKey('NFVI.id'), nullable=False)

    ce_interface_refid = db.Column(db.Integer, db.ForeignKey('interface.id'),
                                   nullable=False)
    pe_interface_refid = db.Column(db.Integer, db.ForeignKey('interface.id'),
                                   nullable=False)

    __table_args__ = (
        db.UniqueConstraint('service_refid', 'index',
                            name='_ns_instance_refid_index_uc'),
    )

    def __init__(self, service_refid, index, nfvi_refid, ce_interface_refid,
                 pe_interface_refid):
        self.service_refid = service_refid
        self.index = index
        self.nfvi_refid = nfvi_refid
        self.ce_interface_refid = ce_interface_refid
        self.pe_interface_refid = pe_interface_refid


class Service(db.Model):

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    ns_instance_id = db.Column(db.String(50), unique=True, nullable=False)
    client_mkt_id = db.Column(db.String(50))

    interfaces = db.relationship("ServiceInterface")

    status = db.Column(db.Enum('ALLOCATED', 'ACTIVE', 'ERROR', 'NOT AVAILABLE',
                               'TERMINATING', 'DELETED', name='service_status'))

    nap_refid = db.Column(db.Integer, db.ForeignKey('NAP.id'), unique=True,
                          nullable=True)

    updated = db.Column(db.TIMESTAMP,
                        server_default=db.text(
                            'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    created = db.Column(db.TIMESTAMP, default=db.func.now())

    def __init__(self, client_mkt_id, ns_instance_id, status, nap_refid):
        self.client_mkt_id = client_mkt_id
        self.ns_instance_id = ns_instance_id
        self.status = status
        self.nap_refid = nap_refid


def post(client_mkt_id, ns_instance_id, nap_mkt_id, nfvi_mkt_ids):
    nap_id = NAP.query.filter_by(mkt_id=nap_mkt_id).first().id
    service = Service(client_mkt_id, ns_instance_id, 'ALLOCATED', nap_id)
    db.session.add(service)
    db.session.flush()

    vlans_allocated = []
    for i in range(0, len(nfvi_mkt_ids)):
        nfvi_mkt_id = nfvi_mkt_ids[i]
        nfvi = NFVI.query.filter_by(mkt_id=nfvi_mkt_id).first()

        ce_used_interfaces = Interface.query.\
            filter_by(port_refid=nfvi.ce_port_refid).all()
        ce_used_vlans = set([interface.
                             vlan for interface in ce_used_interfaces])
        ce_vlan = list(available_vlans - ce_used_vlans)[0]

        ce_interface = Interface(nfvi.ce_port_refid, ce_vlan)
        db.session.add(ce_interface)
        db.session.flush()

        pe_used_interfaces = Interface.query.\
            filter_by(port_refid=nfvi.pe_port_refid).all()
        pe_used_vlans = set([interface.
                             vlan for interface in pe_used_interfaces])
        pe_vlan = list(available_vlans - pe_used_vlans)[0]

        pe_interface = Interface(nfvi.pe_port_refid, pe_vlan)
        db.session.add(pe_interface)
        db.session.flush()

        service_interface = ServiceInterface(service.id, i, nfvi.id,
                                             ce_interface.id, pe_interface.id)
        db.session.add(service_interface)
        db.session.flush()

        vlans_allocated.append((ce_vlan, pe_vlan))

    db.session.commit()

    return vlans_allocated


def get(ns_instance_id):
    if ns_instance_id:
        query = Service.query.filter_by(ns_instance_id=ns_instance_id).all()
    else:
        query = Service.query.all()

    services = []
    for service in query:
        ns_instance_id = service.ns_instance_id
        client_mkt_id = service.client_mkt_id
        status = service.status
        nap_mkt_id = NAP.query.filter_by(id=service.nap_refid).first().mkt_id

        service_interface = ServiceInterface.query.filter_by(
            service_refid=service.id).first()

        if service_interface:
            ce_interface = Interface.query.filter_by(
                id=service_interface.ce_interface_refid).first()
            pe_interface = Interface.query.filter_by(
                id=service_interface.pe_interface_refid).first()
            nfvi_mkt_id = NFVI.query.filter_by(
                id=service_interface.nfvi_refid).first().mkt_id

        created = service.created
        updated = service.updated
        services.append({
            'ns_instance_id': ns_instance_id,
            'client_mkt_id': client_mkt_id,
            'status': status,
            'nap_mkt_id': nap_mkt_id,
            'nfvi_mkt_id': nfvi_mkt_id if service_interface else None,
            'ce_transport': {
                'type': 'vlan',
                'vlan_id': ce_interface.vlan if service_interface else None
            },
            'pe_transport': {
                'type': 'vlan',
                'vlan_id': pe_interface.vlan if service_interface else None
            },
            'created': created,
            'updated': updated
            })

    return services


def set_status(ns_instance_id, status):
    Service.query.filter_by(ns_instance_id=ns_instance_id).\
        update({'status': status})
    db.session.commit()


def delete_service(ns_instance_id):

    service = Service.query.filter_by(ns_instance_id=ns_instance_id).first()
    if service:
        service_interfaces = ServiceInterface.query.filter_by(
            service_refid=service.id).all()
        for service_interface in service_interfaces:

            ce_interface = Interface.query.filter_by(
                id=service_interface.ce_interface_refid).first()
            pe_interface = Interface.query.filter_by(
                id=service_interface.pe_interface_refid).first()

            ce_port = Port.query.filter_by(id=ce_interface.port_refid).first()
            pe_port = Port.query.filter_by(id=pe_interface.port_refid).first()

            db.session.delete(service_interface)
            db.session.flush()
            db.session.delete(ce_interface)
            db.session.delete(pe_interface)
            db.session.flush()

            try:
                with db.session.begin_nested():
                    db.session.delete(ce_port)
                    db.session.flush()
            except IntegrityError:
                pass

            try:
                with db.session.begin_nested():
                    db.session.delete(pe_port)
                    db.session.flush()
            except IntegrityError:
                pass

        db.session.delete(service)
        db.session.commit()
=======
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
from database import db
from nfvi import NFVI
from nap import NAP
from flow import Flow, Flow_Service
from models import Vlan, Transport


class Service(db.Model):
	
	id = db.Column(db.Integer, primary_key=True, nullable=False) # internal id
	ns_instance_id = db.Column(db.String(50), unique=True, nullable=False) # market id
	client_mkt_id = db.Column(db.String(50)) # client market id

	
	status = db.Column(db.Enum('ALLOCATED', 'ACTIVE', 'ERROR', 'NOT AVAILABLE',
		'TERMINATING', 'DELETED', name='service_status'))

	NAP_id  = db.Column(db.Integer, db.ForeignKey('NAP.id'), nullable=False)
	NFVI_id = db.Column(db.Integer, db.ForeignKey('NFVI.id'), nullable=False)
	
	ce_transport_id = db.Column(db.Integer, db.ForeignKey('transport.id'), nullable=True)
	pe_transport_id = db.Column(db.Integer, db.ForeignKey('transport.id'), nullable=True)

	updated = db.Column(db.TIMESTAMP , 
		server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
	created = db.Column(db.TIMESTAMP, default=db.func.now())

	def __init__(self, ns_instance_id, client_mkt_id, status, NAP_id, NFVI_id, 
		ce_transport_id, pe_transport_id):
		self.ns_instance_id = ns_instance_id
		self.client_mkt_id = client_mkt_id
		self.status = status
		self.NAP_id  = NAP_id
		self.NFVI_id = NFVI_id
		self.ce_transport_id = ce_transport_id
		self.pe_transport_id = pe_transport_id


def post(request):
	request = request['service']

	ns_instance_id = request['ns_instance_id']
	client_mkt_id = request['client_mkt_id']

	nap_id = NAP.query.filter_by(mkt_id=request['nap_mkt_id']).first().id
	nfvi_id = NFVI.query.filter_by(mkt_id=request['nfvi_mkt_id']).first().id
	switch = NFVI.query.filter_by(mkt_id=request['nfvi_mkt_id']).first().switch

	used_vlans = Vlan.query.join(Service, db.or_(
		Service.ce_transport_id == Vlan.id, 
		Service.pe_transport_id == Vlan.id)
		).join(NFVI, Service.NFVI_id == NFVI.id).filter(
			db.and_(
				db.or_(Service.status == 'ALLOCATED', Service.status == 'ACTIVE'), 
				NFVI.switch==switch)).all()

	available_vlans = set(xrange(1, 4096))
	vlans = available_vlans - set([vlan.vlan_id for vlan in used_vlans])
	vlans = list(vlans)

	if len(vlans) > 1:
		vlans = vlans[0:2]
		status = 'ALLOCATED'
		ce_transport = Transport()
		pe_transport = Transport()
		db.session.add(ce_transport)
		db.session.add(pe_transport)
		db.session.flush()

		ce_vlan = Vlan(ce_transport.id, vlans[0])
		pe_vlan = Vlan(pe_transport.id, vlans[1])
		db.session.add(ce_vlan)
		db.session.add(pe_vlan)
		db.session.flush()
		service = Service(ns_instance_id, client_mkt_id, status, 
			nap_id, nfvi_id, ce_transport.id, pe_transport.id)
	else:
		vlans = []
		status = 'NOT AVAILABLE'
		service = Service(ns_instance_id, client_mkt_id, status, 
			nap_id, nfvi_id, None, None)
	
	db.session.add(service)
	db.session.commit()

	return [int(x) for x in vlans[0:2]]

def get(ns_instance_id):
	if ns_instance_id:
		query = Service.query.filter_by(ns_instance_id=ns_instance_id).all()
	else:
		query = Service.query.all()

	services = []
	for service in query:
		ns_instance_id = service.ns_instance_id
		client_mkt_id = service.client_mkt_id
		status = service.status
		nap_mkt_id = NAP.query.filter_by(id=service.NAP_id).first().mkt_id
		nfvi_mkt_id = NFVI.query.filter_by(id=service.NFVI_id).first().mkt_id

		ce_vlan = Vlan.query.filter_by(id=service.ce_transport_id).first()
		pe_vlan = Vlan.query.filter_by(id=service.pe_transport_id).first()

		flows = Flow.query.join(Flow_Service, Flow_Service.flow_id == Flow.id).\
			filter(Flow_Service.service_id == service.id)

		created = service.created
		updated = service.updated
		services.append({
			'ns_instance_id' : ns_instance_id,
			'client_mkt_id' : client_mkt_id,
			'status' : status,
			'nap_mkt_id' : nap_mkt_id,
			'nfvi_mkt_id' : nfvi_mkt_id,
			'ce_transport' : {
				'type' : 'vlan',
				'vlan_id' : ce_vlan.vlan_id if ce_vlan else None
				},
			'pe_transport' : {
				'type' : 'vlan',
				'vlan_id' : pe_vlan.vlan_id if pe_vlan else None
				},
			'flows' : [{
				'switch' : flow.switch, 
				'of_table' : flow.of_table, 
				'of_id':flow.of_id} 
				for flow in flows],
			'created' : created,
			'updated' : updated
			})

	return services
	
def create_service_flows(ns_instance_id, n=4):
	service = Service.query.filter_by(ns_instance_id=ns_instance_id).first()
	switch = NFVI.query.filter_by(id=service.NFVI_id).first().switch
	of_table = 0

	db.session.add(service)

	flows = []
	of_id = db.session.query(db.func.max(Flow.of_id)).filter(
		db.and_(Flow.switch==switch, Flow.of_table==of_table)).scalar()
	if of_id is None:
		of_id = 0

	for i in xrange(1,5):
		of_id += 1
		flow = Flow(switch, of_table, of_id)
		db.session.add(flow)
		db.session.flush()

		flow_service = Flow_Service(flow.id, service.id)
		db.session.add(flow_service)
		db.session.flush()

		flows.append({
			'id' : flow.id, 
			'switch' : flow.switch,
			'of_table' : flow.of_table, 
			'of_id': flow.of_id,
			})
	db.session.commit()

	return flows


def set_status(ns_instance_id, status):
	Service.query.filter_by(ns_instance_id=ns_instance_id).update({'status':status})
	db.session.commit()

def delete_flows(ns_instance_id):
	service = Service.query.filter_by(ns_instance_id=ns_instance_id).first()

	flows = Flow_Service.query.filter_by(service_id=service.id)
	
	for flow in flows:
		db.session.delete(Flow_Service.query.filter_by(id=flow.id).first())
		db.session.delete(Flow.query.filter_by(id=flow.flow_id).first())
	if flows:
		db.session.commit()
>>>>>>> 229df9d5c1a5f68cdff4cd2ef2bd547cb9918610
