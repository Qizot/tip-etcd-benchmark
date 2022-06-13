# import os

# os.environ["XTABLES_LIBDIR"] = "/home/qizot/iptables-tmp"

from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.clean import cleanup

cleanup()
net = Containernet(controller=Controller)
info('*** Adding controller\n')
net.addController('c0')

info('*** Adding ETCD containers\n')
etcd1 = net.addDocker(
    'etcd1', 
    ip='10.0.0.251', 
    dimage="etcd_custom",
    environment={
        'ETCD_ADVERTISE_CLIENT_URLS': 'http://10.0.0.251:2379',
        "ALLOW_NONE_AUTHENTICATION": "yes",
        "ETCD_NAME": "etcd1",
        "ETCD_INITIAL_ADVERTISE_PEER_URLS": "http://10.0.0.251:2380",
        "ETCD_LISTEN_PEER_URLS": "http://0.0.0.0:2380",
        "ETCD_LISTEN_CLIENT_URLS": "http://0.0.0.0:2379",
        "ETCD_INITIAL_CLUSTER_TOKEN": "etcd-cluster",
        "ETCD_INITIAL_CLUSTER": "etcd1=http://10.0.0.251:2380,etcd2=http://10.0.0.253:2380,etcd3=http://10.0.0.254:2380",
        "ETCD_INITIAL_CLUSTER_STATE": "new"
    },
    ports=[2379, 2380],
    dcmd='/opt/bitnami/scripts/etcd/run.sh'
)

etcd2 = net.addDocker(
    'etcd2', 
    ip='10.0.0.253', 
    dimage="etcd_custom",
    environment={
        'ETCD_ADVERTISE_CLIENT_URLS': 'http://10.0.0.253:2379',
        "ALLOW_NONE_AUTHENTICATION": "yes",
        "ETCD_NAME": "etcd2",
        "ETCD_INITIAL_ADVERTISE_PEER_URLS": "http://10.0.0.253:2380",
        "ETCD_LISTEN_PEER_URLS": "http://0.0.0.0:2380",
        "ETCD_LISTEN_CLIENT_URLS": "http://0.0.0.0:2379",
        "ETCD_INITIAL_CLUSTER_TOKEN": "etcd-cluster",
        "ETCD_INITIAL_CLUSTER": "etcd1=http://10.0.0.251:2380,etcd2=http://10.0.0.253:2380,etcd3=http://10.0.0.254:2380",
        "ETCD_INITIAL_CLUSTER_STATE": "new"
    },
    ports=[2379, 2380],
    dcmd='/opt/bitnami/scripts/etcd/run.sh'
)

etcd3 = net.addDocker(
    'etcd3', 
    ip='10.0.0.254', 
    dimage="etcd_custom",
    environment={
        'ETCD_ADVERTISE_CLIENT_URLS': 'http://10.0.0.254:2379',
        "ALLOW_NONE_AUTHENTICATION": "yes",
        "ETCD_NAME": "etcd3",
        "ETCD_INITIAL_ADVERTISE_PEER_URLS": "http://10.0.0.254:2380",
        "ETCD_LISTEN_PEER_URLS": "http://0.0.0.0:2380",
        "ETCD_LISTEN_CLIENT_URLS": "http://0.0.0.0:2379",
        "ETCD_INITIAL_CLUSTER_TOKEN": "etcd-cluster",
        "ETCD_INITIAL_CLUSTER": "etcd1=http://10.0.0.251:2380,etcd2=http://10.0.0.253:2380,etcd3=http://10.0.0.254:2380",
        "ETCD_INITIAL_CLUSTER_STATE": "new"
    },
    ports=[2379, 2380],
    dcmd='/opt/bitnami/scripts/etcd/run.sh'
)


info('*** Adding benchmark containers')

benchmark1 = net.addDocker(
    'benchmark1', 
    ip='10.0.0.252', 
    dimage='etcd_benchmark',
    environment={
      "BENCHMARK_EXEC": "/bin/benchmark-client"
    },
    dcmd='/bin/benchmark-server &',
    ports=[8080],
    port_bindings={8080:8080}
)

info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(etcd1, s1)
net.addLink(etcd2, s1)
net.addLink(etcd3, s1)
net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, benchmark1)

info('*** Starting network\n')
net.start()
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()
