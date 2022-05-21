from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

net = Containernet(controller=Controller)
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding ETCD containers\n')
etcd1 = net.addDocker(
    'etcd1', 
    ip='10.0.0.200', 
    dimage="bitnami/etcd",
    environment={
        'ETCD_LISTEN_CLIENT_URLS': 'http://10.0.0.200:2379',
        'ETCD_ADVERTISE_CLIENT_URLS': 'http://10.0.0.200:2379',
    }
)

info('*** Adding benchmark containers')

benchmark1 = net.addDocker(
    'benchmark1', 
    ip='10.0.0.240', 
    dimage='etcd_benchmark',
    dcmd='/bin/benchmark put --endpoints 10.0.0.200:2379'
)

info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(etcd1, s1)
net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, benchmark1)

info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([etcd1, benchmark1])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()