from simulaqron.network import Network
from simulaqron.network import construct_topology_config
from simulaqron.network import get_random_connected
from cqc.pythonLib import CQCConnection

import network_viz
import subprocess
import json

# TODO implement and test teleportation
# TODO implement and test entanglement swapping
# TODO try out noisy network
# TODO implement and test swapping trees
# TODO make sense of latency metric

# GOAL: function that creates entanglement links in a network

'''
Generates dot file from network.json after starting the DEFAULT simulaqron network
'''
def generate_dot_file():
    CONFIG_PATH = "/home/justin/qnexus/simulaqron/config/"
    json_filename = CONFIG_PATH + "network.json"
    with open(json_filename) as json_file:
        network_json = json.load(json_file)
        network_json = network_json["default"]

    nodes = network_json["nodes"]
    topology = network_json["topology"]

    dot_content = "digraph Network {\n"

    for node, attributes in nodes.items():
        dot_content += f'    {node} [label="{node}"];\n'

    added = set()
    if topology is not None:
        for node, neighbors in topology.items():
                for neighbor in neighbors:
                    node_neighbor_pair = tuple(sorted((node, neighbor)))
                    if node_neighbor_pair not in added:
                        dot_content += f"   {node} -> {neighbor} [type=normal, dir=both];\n"
                        added.add(node_neighbor_pair)

    else: # fully connected
        for node, attributes in nodes.items():
            for neighbor, attributes in nodes.items():
                if node is not neighbor:
                    node_neighbor_pair = tuple(sorted((node, neighbor)))
                    if node_neighbor_pair not in added:
                        dot_content += f"   {node} -> {neighbor} [type=normal, dir=both];\n"
                        added.add(node_neighbor_pair)

    dot_content += "}\n"

    with open(CONFIG_PATH + "network.dot", "w") as dot_file:
        dot_file.write(dot_content)

'''
Returns simulaqron network object w/ random connected topology
'''
def get_rc_network(nr_nodes: int, nr_edges: int):
    nodes = []
    for i in range(0, nr_nodes):
        node = "node" + str(i)
        nodes.append(node)

    rc = get_random_connected(nodes, nr_edges=nr_edges)
    network = Network(nodes=nodes, topology=rc, force=True)
    return network


########################################################################################################################  

if __name__ == '__main__':
    network = get_rc_network(nr_nodes=10, nr_edges=20)
    network.start()
    network_viz.generate_dot_file()

    input("Enter to stop...")
    network.stop()
    print("Done.")

 
