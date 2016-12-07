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
from .database import db
from .nfvi import NFVI
from .nap import NAP
from .interface import Interface
from .port import Port
from sqlalchemy.exc import IntegrityError

available_vlans = set(range(400, 501))


class ServiceInterface(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    service_refid = db.Column(db.Integer, db.ForeignKey('service.id'),
                              nullable=False)

    index = db.Column(db.Integer, nullable=False)

    nfvi_refid = db.Column(db.Integer, db.ForeignKey('NFVI.id'), nullable=False)

    interface_refid = db.Column(db.Integer, db.ForeignKey('interface.id'),
                                nullable=False)

    ce_pe = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('service_refid', 'index', 'ce_pe',
                            name='_ns_instance_index_uc'),
    )

    def __init__(self, service_refid, index, nfvi_refid, interface_refid,
                 ce_pe):
        self.service_refid = service_refid
        self.index = index
        self.nfvi_refid = nfvi_refid
        self.interface_refid = interface_refid
        self.ce_pe = ce_pe


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


def post(client_mkt_id, ns_instance_id, nap_mkt_id, ce_pe_nfvi_mkt_ids,
         pe_ce_nfvi_mkt_ids):
    nap_id = NAP.query.filter_by(mkt_id=nap_mkt_id).first().id
    service = Service(client_mkt_id, ns_instance_id, 'ALLOCATED', nap_id)
    db.session.add(service)
    db.session.flush()

    def add_service_interface(service_id, nfvi_mkt_id, index, ce_pe):

        nfvi = NFVI.query.filter_by(mkt_id=nfvi_mkt_id).first()

        used_interfaces = Interface.query.\
            filter_by(port_refid=nfvi.port_refid).all()
        used_vlans = set([interface.vlan for interface in used_interfaces])
        vlan = list(available_vlans - used_vlans)[0]

        interface = Interface(nfvi.port_refid, vlan)
        db.session.add(interface)
        db.session.flush()

        service_interface = ServiceInterface(service_id, index, nfvi.id,
                                             interface.id, ce_pe)

        db.session.add(service_interface)
        db.session.flush()

        return vlan

    ce_pe = []
    for i in range(0, len(ce_pe_nfvi_mkt_ids)):
        vlan = add_service_interface(service.id, ce_pe_nfvi_mkt_ids[i], i, True)
        ce_pe.append({
            'nfvi_mkt_id': ce_pe_nfvi_mkt_ids[i],
            'vlan_id': vlan
        })

    pe_ce = []
    for i in range(0, len(pe_ce_nfvi_mkt_ids)):
        vlan = add_service_interface(service.id, pe_ce_nfvi_mkt_ids[i], i, False)
        pe_ce.append({
            'nfvi_mkt_id': pe_ce_nfvi_mkt_ids[i],
            'vlan_id': vlan
        })

    db.session.commit()

    return {'ce_pe': ce_pe, 'pe_ce': pe_ce}


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

        service_interfaces = ServiceInterface.query.filter_by(
            service_refid=service.id).order_by(ServiceInterface.index)

        ce_pe = []
        pe_ce = []
        for service_interface in service_interfaces:

            interface = Interface.query.filter_by(
                id=service_interface.interface_refid).first()
            nfvi_mkt_id = NFVI.query.filter_by(
                id=service_interface.nfvi_refid).first().mkt_id

            hop = {
                'nfvi_mkt_id': nfvi_mkt_id,
                'transport': {
                    'type': 'vlan',
                    'vlan_id':  interface.vlan,
                }}

            if service_interface.ce_pe:
                ce_pe.append(hop)
            else:
                pe_ce.append(hop)

        created = service.created
        updated = service.updated
        services.append({
            'ns_instance_id': ns_instance_id,
            'client_mkt_id': client_mkt_id,
            'status': status,
            'nap_mkt_id': nap_mkt_id,
            'ce_pe': ce_pe,
            'pe_ce': pe_ce,
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

            interface = Interface.query.filter_by(
                id=service_interface.interface_refid).first()

            port = Port.query.filter_by(id=interface.port_refid).first()

            db.session.delete(service_interface)
            db.session.flush()
            db.session.delete(interface)
            db.session.flush()

            try:
                with db.session.begin_nested():
                    db.session.delete(port)
                    db.session.flush()
            except IntegrityError:
                pass

        db.session.delete(service)
        db.session.commit()
