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