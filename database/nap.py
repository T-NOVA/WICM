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
from database import db
from flow import Flow, Flow_NAP
from models import Vlan, Transport

class NAP(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False) # internal id
	mkt_id = db.Column(db.String(50), unique=True, nullable=False) # market id
	client_mkt_id = db.Column(db.String(50)) # client market id

	switch = db.Column(db.String(50)) # openflow id ?

	ce_port= db.Column(db.Integer) # client edge port
	pe_port= db.Column(db.Integer) # provider edge port

	ce_transport_id = db.Column(db.Integer, db.ForeignKey('transport.id'), nullable=False)
	pe_transport_id = db.Column(db.Integer, db.ForeignKey('transport.id'), nullable=False)

	updated = db.Column(db.TIMESTAMP, 
		server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

	created = db.Column(db.TIMESTAMP, default=db.func.now())

	def __init__(self, mkt_id, client_mkt_id, switch, ce_port, pe_port,
		ce_transport_id, pe_transport_id):
		self.mkt_id = mkt_id
		self.client_mkt_id = client_mkt_id
		self.switch = switch
		self.ce_port= ce_port
		self.pe_port= pe_port
		self.ce_transport_id = ce_transport_id
		self.pe_transport_id = pe_transport_id


def put(request):
	request = request['nap']

	mkt_id = request['mkt_id']
	client_mkt_id = request['client_mkt_id']

	switch = request['switch']

	ce_port= request['ce_port']
	pe_port= request['pe_port']


	ce_transport = Transport()
	pe_transport = Transport()
	db.session.add(ce_transport)
	db.session.add(pe_transport)
	db.session.flush()

	ce_vlan = Vlan(ce_transport.id, request['ce_transport']['vlan_id'])
	pe_vlan = Vlan(pe_transport.id, request['pe_transport']['vlan_id'])
	db.session.add(ce_vlan)
	db.session.add(pe_vlan)
	db.session.flush()

	nap = NAP(mkt_id, client_mkt_id, switch, ce_port, pe_port, 
		ce_vlan.id, pe_vlan.id)

	db.session.add(nap)
	db.session.commit()

	return 1

def get(mkt_id=None):
	if mkt_id:
		query = NAP.query.filter_by(mkt_id=mkt_id).all()
	else:
		query = NAP.query.all()
	naps  = []
	for nap in query:
		ce_vlan = Vlan.query.filter_by(id=nap.ce_transport_id).first().vlan_id
		pe_vlan = Vlan.query.filter_by(id=nap.pe_transport_id).first().vlan_id
		
		flows = Flow.query.join(Flow_NAP, Flow_NAP.flow_id == Flow.id).\
			filter(Flow_NAP.NAP_id == nap.id)

		naps.append({
			'mkt_id' : nap.mkt_id,
			'switch' : nap.switch,
			'client_mkt_id': nap.client_mkt_id,
			'ce_port': nap.ce_port,
			'pe_port': nap.pe_port,
			'ce_transport':{
				'type':'vlan',
				'vlan_id': ce_vlan
			},
			'pe_transport':{
				'type':'vlan',
				'vlan_id': pe_vlan
			},
			'flows' : [{
				'switch' : flow.switch, 
				'of_table' : flow.of_table, 
				'of_id':flow.of_id} 
				for flow in flows]			
		})

	return naps

def delete(mkt_id=None):
	if mkt_id:
		query = NAP.query.filter_by(mkt_id=mkt_id).all()
	else:
		query = NAP.query.all()

	for nap in query:
		ce_transport = Transport.query.filter_by(id=nap.ce_transport_id).first()
		pe_transport = Transport.query.filter_by(id=nap.pe_transport_id).first()
	
		ce_vlan = Vlan.query.filter_by(id=nap.ce_transport_id).first()
		pe_vlan = Vlan.query.filter_by(id=nap.pe_transport_id).first()

		db.session.delete(ce_vlan)
		db.session.delete(pe_vlan)
		db.session.delete(ce_transport)
		db.session.delete(pe_transport)
		db.session.delete(nap)
	if query:
		db.session.commit()
	
	return len(query)

def create_nap_flows(mkt_id, n=2):
	nap = NAP.query.filter_by(mkt_id=mkt_id).first()
	switch = nap.switch
	of_table = 0
	
	of_id = db.session.query(db.func.max(Flow.of_id)).filter(
		db.and_(Flow.switch==switch, Flow.of_table==of_table)).scalar()
	if of_id is None:
		of_id = 0

	flows = []

	for i in xrange(1,n+1):
		of_id += 1
		flow = Flow(switch, of_table, of_id)
		db.session.add(flow)
		db.session.flush()

		flow_nap = Flow_NAP(flow.id, nap.id)
		db.session.add(flow_nap)
		db.session.flush()

		flows.append({
			'id' : flow.id, 
			'switch' : flow.switch,
			'of_table' : flow.of_table, 
			'of_id': flow.of_id,
			})
	db.session.commit()

	return flows

def delete_flows(mkt_id):
	nap = NAP.query.filter_by(mkt_id=mkt_id).first()

	flows = Flow_NAP.query.filter_by(NAP_id=nap.id)
	
	for flow in flows:
		db.session.delete(Flow_NAP.query.filter_by(id=flow.id).first())
		db.session.delete(Flow.query.filter_by(id=flow.flow_id).first())
	if flows:
		db.session.commit()
