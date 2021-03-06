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

import json
import logging
from requests import post, get


logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class VtnException(Exception):
    pass


class TenantNotCreated(Exception):
    pass


class TenantNotFound(Exception):
    pass


class BridgeAlreadyExists(VtnException):
    pass


class BridgeNotCreated(VtnException):
    pass


class BridgeNotFound(VtnException):
    pass


class TerminalNotCreated(VtnException):
    pass


class TerminalNotFound(VtnException):
    pass


class InterfaceNotCreated(VtnException):
    pass


class InterfaceNotFound(VtnException):
    pass


class InterfaceAlreadyExists(VtnException):
    pass


class MappingConflict(VtnException):
    pass


class MappingFailed(VtnException):
    pass


class ConditionNotCreated(VtnException):
    pass


class RedirectionNotCreated(VtnException):
    pass


class RedirectionNotDeleted(VtnException):
    pass


def _headers():
    return {'content-type': 'application/json'}


class VtnWrapper:
    '''Wrappes the OpenDaylight Virtual Tenant plugin to handle
    the WICMs needs'''

    def __init__(self, host, port, username='admin', password='admin'):
        self.host = host
        self.port = port
        self.auth = (username, password)

        logger.debug(('OpenDaylight client created!'
                      'Adress "{}:{}".'
                      'Auth "{}:{}"').format(self.host, self.port, self.auth[0],
                                             self.auth[1]))
        self.condition_create()

    def _vtenant_exists(self, tenant):
        url_check = '{}:{}/restconf/operational/vtn:vtns/vtn/'

        logger.debug(('Checking if tenant "{}" exists. url: "{}"').format(
            tenant, url_check))

        r = get(url_check, auth=self.auth)

        if r.ok:
            logger.debug('Found tenant "{}": {}'.format(tenant, r.json()))
        else:
            logger.debug('Not found tenant "{}": {}'.format(tenant, r.text))

        return r.ok

    def _vbrige_exists(self, tenant, vbridge):

        if not self._tenant_exists(tenant):
            logger.error(('Failed to check for vbridge "{}" in tenant "{}" '
                         'because the tenant does not exist').format(vbridge,
                                                                     tenant))
            raise TenantNotFound(tenant)

        url_check = ('{}:{}/restconf/operational/vtn:vtns/vtn/{}/vbridge/{}'.
                     format(self.host, self.port, tenant, vbridge))

        logger.debug(('Checking if a vbridge "{}" already exists for tenant "{}'
                      '". url: "{}"').format(vbridge, tenant, url_check))

        r = get(url_check, auth=self.auth)
        if r.ok:
            logger.debug('Found vbridge "{}" for tenant "{}": {}'.
                         format(vbridge, tenant, r.json()))
        else:
            logger.debug('Not found vbridge "{}" for tenant "{}": {}'.
                         format(vbridge, tenant, r.text))

        return r.ok

    def _vinterface_exists(self, tenant, vbridge, vinterface):
        if not self._vbrige_exists(tenant, vbridge):
            logger.error(('Failed to check for vinterface "{}" in vbridge "{}" '
                          'for tenant "{}" because the bridge doesnot exist').
                         format(vinterface, vbridge, tenant))
            raise BridgeNotFound(vbridge)

        url_check = ('{}:{}/restconf/operational/vtn:vtns/vtn/{}/vbridge/{}/'
                     'vinterface/{}').format(self.host, self.port, tenant,
                                             vbridge, vinterface)

        logger.debug(('Checking if vinterface {} in vbridge "{}" exists for '
                      'tenant "{}". url: "{}"').format(vbridge, tenant,
                                                       url_check))

        r = get(url_check, auth=self.auth)
        if r.ok:
            logger.debug(('Found vinterface "{}" in vbridge "{}" for tenant "{}'
                          '": {}').format(vinterface, vbridge, tenant,
                                          r.json()))
        else:
            logger.debug(('Not found vinterface "{}" in vbridge "{}" for tenant'
                          ' "{}": {}').format(vinterface, vbridge, tenant,
                                              r.json()))
        return r.ok

    def _vtenant_create(self, tenant):
        url = 'http://{}:{}/restconf/operations/vtn:update-vtn'.format(
            self.host, self.port)

        data = json.dumps({'input': {'tenant-name': tenant}})

        logger.info('Creating tenant "{}"'.format(tenant))
        logger.debug('Creating new tenant url:"{}" data:"{}"'.format(url, data))

        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug('Success creating tenant "{}": {}'.format(tenant,
                                                                   r.json()))
        else:
            logger.error('Failed to create tenant "{}": {}'.format(tenant,
                                                                   r.text))
            raise TenantNotCreated(tenant)

    def _vbrige_delete(self, tenant, vbridge):
        url = ('http://{}:{}/restconf/operations/vtn-vbridge:'
               'remove-vbridge').format(self.host, self.port)
        data = json.dumps({'input':
                           {'tenant-name': tenant,
                            'bridge-name': vbridge}})

        logger.info('Deleting vbridge "{}" for tenant "{}"'.format(vbridge,
                                                                   tenant))
        logger.debug('Deleting vbridge url:"{}" data:"{}"'.format(url, data))

        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug('Success deleting vbridge "{}" for "{}"'.format(
                         vbridge, tenant))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed to delete vbridge "{}" for tenant "{}":'
                          ' tenant does not exist.').format(vbridge, tenant))
            raise TenantNotFound(tenant)
        else:
            logger.error('Failed to delete vbridge "{}" for tenant "{}": {}'.
                         format(vbridge, tenant, r.text))
            raise BridgeNotCreated(vbridge)

    def _vbridge_create(self, tenant, vbridge, description=''):
        url = ('http://{}:{}/restconf/operations/vtn-vbridge:'
               'update-vbridge').format(self.host, self.port)
        data = json.dumps({'input':
                           {'tenant-name': tenant,
                            'bridge-name': vbridge,
                            'description': description}})

        logger.info('Creating vbridge "{}" for tenant "{}"'.format(vbridge,
                                                                   tenant))
        logger.debug('Creating new vbridge url:"{}" data:"{}"'.format(url,
                                                                      data))
        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug('Success creating vbridge "{}" for "{}": {}'.format(
                vbridge, tenant, r.json()))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed to create vbridge "{}" for tenant "{}":'
                          ' tenant does not exist.').format(vbridge, tenant))
            raise TenantNotFound(tenant)
        else:
            logger.error('Failed to create vbridge "{}" for tenant "{}": {}'.
                         format(vbridge, tenant, r.text))
            raise BridgeNotCreated(vbridge)

    def _vinterface_create(self, tenant, vbridge, vinterface, vterminal=False):
        url = ('http://{}:{}/restconf/operations/vtn-vinterface:'
               'update-vinterface').format(self.host, self.port)
        data = {'input': {'tenant-name': tenant,
                          'interface-name': vinterface}}

        if vterminal:
            data['input']['terminal-name'] = vbridge
        else:
            data['input']['bridge-name'] = vbridge

        data = json.dumps(data)

        logger.info('Creating vinterface "{}" in "{}" for tenant "{}"'.
                    format(vinterface, vbridge, tenant))

        logger.debug('Creating new vinterface url:"{}" data:"{}"'.format(url,
                                                                         data))
        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug(('Success creating vinterface "{}" in "{}"'
                          ' for tenant "{}": {}').format(vinterface, vbridge,
                                                         tenant, r.json()))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed creating vinterface "{}" in "{}"'
                          ' for tenant "{}": vbridge not found').format(
                              vinterface, vbridge, tenant))
            if vterminal:
                raise TerminalNotFound(vbridge)
            else:
                raise BridgeNotFound(vbridge)
        else:
            logger.error(('Failed creating vinterface "{}" in vbridge "{}"'
                          ' for tenant "{}": {}').format(vinterface, vbridge,
                                                         tenant, r.text))
            raise InterfaceNotCreated(vinterface)

    def _vinterface_map(self, tenant, vbridge, vinterface, interface,
                        vterminal=False):
        url = ('http://{}:{}/restconf/operations/vtn-port-map:set-port-map'
               .format(self.host, self.port))
        data = {'input': {'tenant-name': tenant,
                          'interface-name': vinterface,
                          'node': interface[0],
                          'port-id': interface[1]}}

        if vterminal:
            data['input']['terminal-name'] = vbridge
        else:
            data['input']['bridge-name'] = vbridge

        if len(interface) >= 3:
            data['input']['vlan-id'] = interface[2]

        data = json.dumps(data)

        logger.info('Mapping vinterface "{}" in "{}" for tenant "{}"'.
                    format(vinterface, vbridge, tenant))

        logger.debug('Mapping vinterface url:"{}" data:"{}"'.format(url, data))

        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug(('Success mapping vinterface "{}" in "{}"'
                          ' for tenant "{}": {}').format(vinterface, vbridge,
                                                         tenant, r.json()))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed mapping vinterface "{}" in "{}"'
                          ' for tenant "{}": vinterface not found').format(
                              vinterface, vbridge, tenant))
            raise InterfaceNotFound(vbridge)
        elif r.status_code == 409:  # CONFLICT
            logger.error(('Failed mapping vinterface "{}" in "{}"'
                          ' for tenant "{}" Conflict: {}').format(
                              vinterface, vbridge, tenant, r.text))
            raise MappingConflict(vinterface)
        else:
            logger.error(('Failed creating vinterface "{}" in "{}"'
                          ' for tenant "{}": {}').format(vinterface, vbridge,
                                                         tenant, r.text))
            raise MappingFailed(vinterface)

    def _vterminal_create(self, tenant, vterminal):
        url = ('http://{}:{}/restconf/operations/vtn-vterminal:'
               'update-vterminal').format(self.host, self.port)
        data = json.dumps({'input':
                           {'tenant-name': tenant, 'terminal-name': vterminal}})

        logger.info('Creating vterminal "{}" for tenant "{}"'.format(vterminal,
                                                                     tenant))
        logger.debug('Creating new vterminal url:"{}" data:"{}"'.format(url,
                                                                        data))
        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug('Success creating vterminal "{}" for "{}": {}'.format(
                vterminal, tenant, r.json()))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed to create vterminal {} for tenant "{}":'
                          ' tenant does not exist.').format(vterminal, tenant))
            raise TenantNotFound(tenant)
        else:
            logger.error('Failed to create vterminal {} for tenant "{}": {}'.
                         format(vterminal, tenant, r.text))
            raise TerminalNotCreated(vterminal)

    def _redirect_create(self, tenant, from_vbridge, from_vinterface,
                         to_vbridge, to_vinterface):
        url = ('http://{}:{}/restconf/operations/vtn-flow-filter:'
               'set-flow-filter').format(self.host, self.port)

        data = json.dumps({'input':
                           {'output': 'false',
                            'tenant-name': tenant,
                            'bridge-name': from_vbridge,
                            'interface-name': from_vinterface,
                            'vtn-flow-filter': [
                                {'condition': 'cond_1',
                                 'index': 10,
                                 'vtn-redirect-filter':
                                 {'redirect-destination':
                                  {'bridge-name': to_vbridge,
                                   'interface-name': to_vinterface},
                                  'output': 'true'}}]}})

        logger.info('Creating redirection for tenant "{}" from {}@{} to {}@{}'
                    .format(tenant, from_vbridge, from_vinterface, to_vbridge,
                            to_vinterface))

        logger.debug('Creating new redirection url:"{}" data:"{}"'.format(url,
                                                                          data))
        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug(('Success creating redirection for tenant "{}"'
                          'from {}@{} to {}@{}')
                         .format(tenant, from_vbridge, from_vinterface,
                                 to_vbridge, to_vinterface))
        else:
            logger.error(('Failed creating redirection for tenant "{}"'
                          'from {}@{} to {}: {}')
                         .format(tenant, from_vbridge, from_vinterface,
                                 to_vbridge, to_vinterface, r.text))

            raise RedirectionNotCreated()

    def nap_create(self, client_id, mkt_id, ce_interface, pe_interface):
        self._vtenant_create(client_id)
        self._vbridge_create(client_id, mkt_id + '_NAP')
        self._vinterface_create(client_id, mkt_id + '_NAP', 'ce')
        self._vinterface_map(client_id, mkt_id + '_NAP', 'ce', ce_interface)
        self._vinterface_create(client_id, mkt_id + '_NAP', 'pe')
        self._vinterface_map(client_id, mkt_id + '_NAP', 'pe', pe_interface)

    def nap_delete(self, client_id, mkt_id):
        self._vbrige_delete(client_id, mkt_id + '_NAP')

    def chain_create(self, client_id, ns_instance_id, nap_mkt_id, ce_pe, pe_ce):
        self._vbridge_create(client_id, ns_instance_id + '_NS')
        ce_pe_path = [(nap_mkt_id + '_NAP', 'ce')]
        pe_ce_path = [(nap_mkt_id + '_NAP', 'pe')]

        try:
            for i in range(0, len(ce_pe)):
                self._vinterface_create(client_id, ns_instance_id + '_NS',
                                        'ce_pe' + str(i))

                self._vinterface_map(client_id, ns_instance_id + '_NS',
                                     'ce_pe' + str(i), ce_pe[i])

                ce_pe_path.append((ns_instance_id + '_NS', 'ce_pe' + str(i)))

            for i in range(0, len(pe_ce)):
                self._vinterface_create(client_id, ns_instance_id + '_NS',
                                        'pe_ce' + str(i))

                self._vinterface_map(client_id, ns_instance_id + '_NS',
                                     'pe_ce' + str(i), pe_ce[i])

                pe_ce_path.append((ns_instance_id + '_NS', 'pe_ce' + str(i)))

            ce_pe_path.append((nap_mkt_id + '_NAP', 'pe'))
            pe_ce_path.append((nap_mkt_id + '_NAP', 'ce'))

            redirections = zip(ce_pe_path, ce_pe_path[1:])
            for if0, if1 in redirections:
                self._redirect_create(client_id, if0[0], if0[1], if1[0], if1[1])

            redirections = zip(pe_ce_path, pe_ce_path[1:])
            for if0, if1 in redirections:
                self._redirect_create(client_id, if0[0], if0[1], if1[0], if1[1])

        except Exception as ex:
            self._vbrige_delete(client_id, ns_instance_id + '_NS')
            self._redirect_delete(client_id, nap_mkt_id + '_NAP', 'ce')
            self._redirect_delete(client_id, nap_mkt_id + '_NAP', 'pe')
            raise ex

    def _redirect_delete(self, tenant, vbridge, vinterface):
        url = ('http://{}:{}/restconf/operations/vtn-flow-filter:'
               'remove-flow-filter').format(self.host, self.port)
        data = json.dumps({'input':
                           {'tenant-name': tenant,
                            'bridge-name': vbridge,
                            'interface-name': vinterface}})

        logger.info('Deleting redirection "{}" at vbridge "{}" for tenant "{}"'
                    .format(vinterface, vbridge, tenant))

        logger.debug('Deleting redirection at vbridge url:"{}" data:"{}"'
                     .format(url, data))

        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug(('Success deleting redirection "{}" at vbridge "{}" '
                          'for "{}"').format(vinterface, vbridge, tenant))
        elif r.status_code == 404:  # NOT FOUND
            logger.error(('Failed to delete redirection "{}" at vbridge "{}" '
                          'for tenant "{}": tenant does not exist.')
                         .format(vinterface, vbridge, tenant))
            raise TenantNotFound(tenant)
        else:
            logger.error(('Failed to delete redirection "{}" at vbridge "{}" '
                          'for tenant "{}": {}')
                         .format(vinterface, vbridge, tenant, r.text))
            raise RedirectionNotDeleted(vbridge)

    def chain_delete(self, client_id, ns_instance_id, nap_mkt_id):
        self._vbrige_delete(client_id, ns_instance_id + '_NS')
        self._redirect_delete(client_id, nap_mkt_id + '_NAP', 'ce')
        self._redirect_delete(client_id, nap_mkt_id + '_NAP', 'pe')

    def nfvi_create(self, mkt_id, ce_atachment, pe_atachment):
        self._vtenant_create('TeNOR')
        description = json.dumps({'ce_atachment': ce_atachment,
                                  'pe_atachment': pe_atachment,
                                  'range_min': 100,
                                  'range_max': 400})

        self._vbridge_create('TeNOR', mkt_id, description=description)

    def condition_create(self):
        url = ('http://{}:{}/restconf/operations/vtn-flow-condition:'
               'set-flow-condition').format(self.host, self.port)
        data = json.dumps({'input': {'operation': 'SET',
                                     'present': 'false',
                                     'name': 'cond_1',
                                     'vtn-flow-match': [{
                                         'index': 1,
                                         'vtn-ether-match': {
                                             'ether-type': '0x0800'},
                                         'vtn-inet-match': {}}]}})

        logger.info('Creating flow condition for IP filtering')
        logger.debug('Creating new condition url:"{}" data:"{}"'.format(url,
                                                                        data))

        r = post(url, data=data, auth=self.auth, headers=_headers())

        if r.ok:
            logger.debug('Success creating IP filter condition: {}'.format(
                r.json()))
        else:
            logger.error('Failed to create IP filter condition: {}'.
                         format(r.text))
            raise ConditionNotCreated('IP Filter')
