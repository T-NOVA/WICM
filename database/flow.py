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

class Flow(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)

	switch = db.Column(db.String(50)) # openflow id
	of_table = db.Column(db.Integer)
	of_id    = db.Column(db.Integer, nullable=False)

	
	updated = db.Column(db.TIMESTAMP, 
		server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

	created = db.Column(db.TIMESTAMP, default=db.func.now())

	__table_args__ = (
		db.UniqueConstraint('switch', 'of_table', 'of_id', name='flow_id'),
		{})

	def __init__(self, switch, of_table,of_id):
		self.switch = switch
		self.of_table = of_table
		self.of_id = of_id

class Flow_Service(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)
	flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'), nullable=False)
	service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)

	__table_args__ = (
		db.UniqueConstraint('flow_id','service_id', name='flow_service'),
		{})

	def __init__(self, flow_id, service_id):
		self.flow_id = flow_id
		self.service_id = service_id

class Flow_NAP(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)
	flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'), nullable=False)
	NAP_id = db.Column(db.Integer, db.ForeignKey('NAP.id'), nullable=False)
	
	__table_args__ = (
		db.UniqueConstraint('flow_id', 'NAP_id', name='flow_NAP'),
		{})

	def __init__(self, flow_id, NAP_id):
		self.flow_id = flow_id
		self.NAP_id = NAP_id
		