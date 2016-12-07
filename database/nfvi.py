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
from sqlalchemy.exc import IntegrityError


class NFVI(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    mkt_id = db.Column(db.String(50), unique=True, nullable=False)

    port_refid = db.Column(db.Integer, db.ForeignKey('port.id'),
                           nullable=False)

    updated = db.Column(db.TIMESTAMP,
                        server_default=db.text(
                            'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    created = db.Column(db.TIMESTAMP, default=db.func.now())

    def __init__(self, mkt_id, port_refid):
        self.mkt_id = mkt_id
        self.port_refid = port_refid


def put(mkt_id, nfvi_port):

    port = Port.query.filter_by(switch=nfvi_port[0], port=nfvi_port[1]).first()
    if not port:
        port = Port(nfvi_port[0], nfvi_port[1])
        db.session.add(port)
        db.session.flush()

    nfvi = NFVI(mkt_id, port.id)
    db.session.add(nfvi)
    db.session.commit()

    return 1


def get(mkt_id=None):
    if mkt_id:
        query = NFVI.query.filter_by(mkt_id=mkt_id).all()
    else:
        query = NFVI.query.all()
    nfvis = []

    for nfvi in query:

        port = Port.query.filter_by(id=nfvi.port_refid).first()

        nfvis.append({
            'mkt_id': nfvi.mkt_id,
            'switch': port.switch,
            'port': port.port,
        })

    return nfvis


def delete(mkt_id=None):
    if mkt_id:
        query = NFVI.query.filter_by(mkt_id=mkt_id).all()
    else:
        query = NFVI.query.all()
    for nfvi in query:

        port = Port.query.filter_by(id=nfvi.port_refid).first()

        db.session.delete(nfvi)
        db.session.flush()

        try:
            with db.session.begin_nested():
                db.session.delete(port)
                db.session.flush()
        except IntegrityError:
            pass

    if query:
        db.session.commit()

    return len(query)
