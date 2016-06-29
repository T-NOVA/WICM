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

class Transport(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)
	type = db.Column(db.String(50)) #onlForeignKeyy vlan

	updated = db.Column(db.TIMESTAMP, 
		server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

	created = db.Column(db.TIMESTAMP, default=db.func.now())

	__mapper_args__ = {
		'polymorphic_identity':'transport',
		'polymorphic_on':type
	}

	def __init__(self):
		pass

class Vlan(db.Model):
	id = db.Column(db.Integer, db.ForeignKey('transport.id'), 
		primary_key=True, nullable=False)
	vlan_id = db.Column(db.Integer, nullable=False)

	def __init__(self, id, vlan_id):
		self.id = id
		self.vlan_id = vlan_id

	__table_args__ = (
		db.CheckConstraint(('vlan_id > 0 and vlan_id < 4096'), name='check_vlan_id'),
		{})

	__mapper_args__ = {
		'polymorphic_identity':'Vlan',
	}


