
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


class Interface(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    port_refid = db.Column(db.Integer, db.ForeignKey('port.id'), nullable=False)
    vlan = db.Column(db.Integer, nullable=False)

    updated = db.Column(db.TIMESTAMP,
                        server_default=db.text(
                            'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    created = db.Column(db.TIMESTAMP, default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('port_refid', 'vlan', name='_portrefid_vlan_uc'),
    )

    def __init__(self, port_refid, vlan):
        self.port_refid = port_refid
        self.vlan = vlan
