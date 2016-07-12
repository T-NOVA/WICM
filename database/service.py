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
