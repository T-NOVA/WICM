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
from .port import Port
from .interface import Interface
from sqlalchemy.exc import IntegrityError


class NAP(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)  # internal id
    client_mkt_id = db.Column(db.String(50))  # client market id
    mkt_id = db.Column(db.String(50), unique=True, nullable=False)  # market id

    ce_interface_refid = db.Column(db.Integer, db.ForeignKey('interface.id'),
                                   nullable=False)
    pe_interface_refid = db.Column(db.Integer, db.ForeignKey('interface.id'),
                                   nullable=False)

    updated = db.Column(db.TIMESTAMP,
                        server_default=db.text(
                            'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    created = db.Column(db.TIMESTAMP, default=db.func.now())

    __table_args__ = (
        db.CheckConstraint('ce_interface_refid != pe_interface_refid',
                           name='_check_diferent_interface'),
    )

    def __init__(self, client_mkt_id, mkt_id, ce_interface_refid,
                 pe_interface_refid):
        self.mkt_id = mkt_id
        self.client_mkt_id = client_mkt_id
        self.ce_interface_refid = ce_interface_refid
        self.pe_interface_refid = pe_interface_refid


def put(client_mkt_id, mkt_id, ce, pe):

    ce_port = Port.query.filter_by(switch=ce[0], port=ce[1]).first()
    if not ce_port:
        ce_port = Port(ce[0], ce[1])
        db.session.add(ce_port)
        db.session.flush()

    pe_port = Port.query.filter_by(switch=pe[0], port=pe[1]).first()
    if not pe_port:
        pe_port = Port(pe[0], pe[1])
        db.session.add(pe_port)
        db.session.flush()

    ce_interface = Interface(ce_port.id, ce[2])
    db.session.add(ce_interface)
    pe_interface = Interface(pe_port.id, pe[2])
    db.session.add(pe_interface)
    db.session.flush()

    nap = NAP(client_mkt_id, mkt_id, ce_interface.id, pe_interface.id)
    db.session.add(nap)

    db.session.commit()
    return 1


def get(mkt_id=None):
    if mkt_id:
        query = NAP.query.filter_by(mkt_id=mkt_id).all()
    else:
        query = NAP.query.all()
    naps = []

    for nap in query:
        ce_interface = Interface.query.filter_by(id=nap.ce_interface_refid).\
            first()
        pe_interface = Interface.query.filter_by(id=nap.pe_interface_refid).\
            first()

        ce_vlan = ce_interface.vlan
        pe_vlan = pe_interface.vlan

        ce_port = Port.query.filter_by(id=ce_interface.port_refid).first()
        pe_port = Port.query.filter_by(id=pe_interface.port_refid).first()

        naps.append({
            'mkt_id': nap.mkt_id,
            'switch': ce_port.switch,
            'client_mkt_id': nap.client_mkt_id,
            'ce_port': ce_port.port,
            'pe_port': pe_port.port,
            'ce_transport': {
                'type': 'vlan',
                'vlan_id': ce_vlan
            },
            'pe_transport': {
                'type': 'vlan',
                'vlan_id': pe_vlan
            }
        })

    return naps


def delete(mkt_id=None):
    if mkt_id:
        query = NAP.query.filter_by(mkt_id=mkt_id).all()
    else:
        query = NAP.query.all()

    for nap in query:
        ce_interface = Interface.query.filter_by(id=nap.ce_interface_refid).\
            first()
        pe_interface = Interface.query.filter_by(id=nap.pe_interface_refid).\
            first()

        ce_port = Port.query.filter_by(id=ce_interface.port_refid).first()
        pe_port = Port.query.filter_by(id=pe_interface.port_refid).first()

        db.session.delete(nap)
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

    if query:
        db.session.commit()

    return len(query)
