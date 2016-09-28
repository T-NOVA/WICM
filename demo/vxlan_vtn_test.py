#!/usr/bin/python
from mininet.net import Mininet
from mininet.node import Host, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
import apt

#  Note Vlan package check only work with ubuntu
#  Please comment the package check if your running the script other than ubuntu
#  package check Start

cache = apt.Cache()
if cache['vlan'].is_installed:
    print("Vlan installed")
else:
    print("ERROR:VLAN package not  installed please run sudo"
          "apt-get install vlan")
    exit(1)
#  package check End


class VLANHost(Host):
        def config(net, vlan=100, **params):
                """Configure VLANHost according to (optional) parameters:
                        vlan: VLAN ID for default interface"""
                r = super(Host, net).config(**params)
                intf = net.defaultIntf()
#  remove IP from default, "physical" interface
                net.cmd('ifconfig %s inet 0' % intf)
#  create VLAN interface
                net.cmd('vconfig add %s %d' % (intf, vlan))
#  assign the host's IP to the VLAN interface
                net.cmd('ifconfig %s.%d inet %s' % (intf, vlan, params['ip']))
#  update the intf name and host's intf map
                newName = '%s.%d' % (intf, vlan)
#  update the (Mininet) interface to refer to VLAN interface name
                intf.name = newName
#  add VLAN interface to host's name to intf map
                net.nameToIntf[newName] = intf
                return r


def vlan_loop(sw, vlan_in, vlan_out):
    fmt = ('-Oopenflow13'
           ' dl_vlan={},actions=set_field:{}-\\>vlan_vid,OUTPUT:IN_PORT')
    sw.dpctl('add-flow', fmt.format(vlan_in, vlan_out + 4096))


def main(odl_ip='127.0.0.1'):
    "Create custom topo."
    net = Mininet(topo=None, build=False)

    host1 = net.addHost('h1', cls=VLANHost, vlan=100)
    host2 = net.addHost('h2', cls=VLANHost, vlan=100)

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')

    net.addLink(s1, host1)
    net.addLink(s1, host2)
    net.addLink(s1, s3)
    net.addLink(s1, s2)
    net.addLink(s2, s4)

    odl_ctrl = net.addController('c0', controller=RemoteController,
                                 ip=odl_ip, port=6633)

    net.build()

    s1.start([odl_ctrl])
    s2.start([odl_ctrl])
    s3.start([])
    s4.start([])

    # Preconfig the switches
    for i in range(400, 403, 2):
        vlan_loop(s3, i, i+1)
        vlan_loop(s3, i+1, i)
        vlan_loop(s4, i, i+1)
        vlan_loop(s4, i+1, i)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
