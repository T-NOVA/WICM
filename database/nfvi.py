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
from .port import Port
from sqlalchemy.exc import IntegrityError


class NFVI(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    mkt_id = db.Column(db.String(50), unique=True, nullable=False)

    ce_port_refid = db.Column(db.Integer, db.ForeignKey('port.id'),
                              nullable=False)
    pe_port_refid = db.Column(db.Integer, db.ForeignKey('port.id'),
                              nullable=False)

    updated = db.Column(db.TIMESTAMP,
                        server_default=db.text(
                            'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    created = db.Column(db.TIMESTAMP, default=db.func.now())

    def __init__(self, mkt_id, ce_port_refid, pe_port_refid):
        self.mkt_id = mkt_id
        self.ce_port_refid = ce_port_refid
        self.pe_port_refid = pe_port_refid


def put(mkt_id, ce, pe):

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

    nfvi = NFVI(mkt_id, ce_port.id, pe_port.id)
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

        ce_port = Port.query.filter_by(id=nfvi.ce_port_refid).first()
        pe_port = Port.query.filter_by(id=nfvi.pe_port_refid).first()

        nfvis.append({
            'mkt_id': nfvi.mkt_id,
            'switch': ce_port.switch,
            'ce_port': ce_port.port,
            'pe_port': pe_port.port,
        })

    return nfvis


def delete(mkt_id=None):
    if mkt_id:
        query = NFVI.query.filter_by(mkt_id=mkt_id).all()
    else:
        query = NFVI.query.all()
    for nfvi in query:

        ce_port = Port.query.filter_by(id=nfvi.ce_port_refid).first()
        pe_port = Port.query.filter_by(id=nfvi.pe_port_refid).first()

        db.session.delete(nfvi)
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

class NFVI(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)
	mkt_id = db.Column(db.String(50), unique=True, nullable=False)

	switch = db.Column(db.String(50)) # openflow id ?
	ce_port= db.Column(db.Integer) # client edge port
	pe_port= db.Column(db.Integer) # provider edge port

	updated = db.Column(db.TIMESTAMP, 
		server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
	created = db.Column(db.TIMESTAMP, default=db.func.now())

	def __init__(self, mkt_id, switch, ce_port, pe_port):
		self.mkt_id = mkt_id
		self.switch = switch
		self.ce_port = ce_port
		self.pe_port = pe_port

#	__table_args__ = (
#		db.UniqueConstraint('switch', 'ce_port', 'pe_port', name='nfvi_uniqueness'),
#		{})

def put(request):
	request = request['nfvi']

	mkt_id = request['mkt_id']
	switch = request['switch']
	ce_port = request['ce_port']
	pe_port = request['pe_port']

	nfvi = NFVI(mkt_id, switch, ce_port, pe_port)
	db.session.add(nfvi)
	db.session.commit()

	return 1

def get(mkt_id=None):
	if mkt_id:
		query = NFVI.query.filter_by(mkt_id=mkt_id).all()
	else:
		query = NFVI.query.all()
	nfvis  = []
	for nfvi in query:
		nfvis.append({
			'mkt_id' : nfvi.mkt_id,
			'switch' : nfvi.switch,
			'ce_port': nfvi.ce_port,
			'pe_port': nfvi.pe_port,
			})

	return nfvis
def delete(mkt_id=None):
	if mkt_id:
		query = NFVI.query.filter_by(mkt_id=mkt_id).all()
	else:
		query = NFVI.query.all()
	for nfvi in query:
		db.session.delete(nfvi)
	
	if query:
		db.session.commit()
	
	return len(query)
>>>>>>> 229df9d5c1a5f68cdff4cd2ef2bd547cb9918610
