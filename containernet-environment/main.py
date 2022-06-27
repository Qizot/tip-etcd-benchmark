# import os

# os.environ["XTABLES_LIBDIR"] = "/home/qizot/iptables-tmp"
import sys
import json
import argparse

from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel, error
from mininet.clean import cleanup

def setup_etcd_instances(net, switch, config_file_path):
    configs = json.load(open(config_file_path))

    if type(configs) != list or len(configs) < 1:
        raise RuntimeError("The config file should be a json array containing at least one instance")


    print(config_file_path)
    initial_cluster = ",".join([f"etcd{idx}=http://{node['ip']}:2380" for idx, node in enumerate(configs)])

    instances = []

    for idx, instance_cfg in enumerate(configs): 
        name = f"etcd{idx}"
        ip = instance_cfg["ip"]
        # string representation of memory e.g. 100mb
        mem = instance_cfg["mem"]
        # fractional number of CPUs cores to use
        cpus = float(instance_cfg["cpus"])
        # bandwidth should be given in Mbps
        bandwidth = int(instance_cfg["bandwidth"])
        # a delay string e.g. '30ms'
        link_delay = instance_cfg["link_delay"]

        instance = net.addDocker(
            name,
            ip=ip,
            dimage="etcd_custom",
            environment={
                "ETCD_NAME": name, 
                "ALLOW_NONE_AUTHENTICATION": "yes",
                "ETCD_INITIAL_CLUSTER_TOKEN": "etcd-cluster",
                "ETCD_INITIAL_CLUSTER_STATE": "new",
                # ip related config variables
                "ETCD_ADVERTISE_CLIENT_URLS": f"http://{ip}:2379",
                "ETCD_INITIAL_ADVERTISE_PEER_URLS": f"http://{ip}:2380",
                "ETCD_LISTEN_PEER_URLS": "http://0.0.0.0:2380",
                "ETCD_LISTEN_CLIENT_URLS": "http://0.0.0.0:2379",
                "ETCD_INITIAL_CLUSTER": initial_cluster, 
            },
            ports=[2379, 2380],
            dcmd='/opt/bitnami/scripts/etcd/run.sh',
            cpus=cpus,
            memory=mem,
        )
        instances.append(instance)

        net.addLink(instance, switch, cls=TCLink, delay=link_delay, bw=bandwidth)


parser = argparse.ArgumentParser(
    description="Containernet ETCD benchmarking environment",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument("-c", "--config-file", type=str, required=True, help="etcd instances configuration file")
args = parser.parse_args()
print(args)

setLogLevel('info')

cleanup()

net = Containernet(controller=Controller)
info('*** Adding controller\n')
net.addController('c0')

info('*** Adding benchmark containers')

benchmark = net.addDocker(
    'benchmark', 
    ip='10.0.0.250', 
    dimage='etcd_benchmark',
    environment={
      "BENCHMARK_EXEC": "/bin/benchmark-client"
    },
    dcmd='/bin/benchmark-server &',
    ports=[8080],
    port_bindings={8080:8080}
)

info('*** Adding ETCD containers\n')


info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')

info("*** Creating ETCD instances\n")

setup_etcd_instances(net, s1, args.config_file)

info('*** Connecting switches\n')

net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, benchmark)

info('*** Starting network\n')
net.start()
print("Ready")
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()
