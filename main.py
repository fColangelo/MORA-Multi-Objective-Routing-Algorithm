# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import os
import json
import time
# TOPOLOGIES
#from network_topologies.pseudogeant import Pseudogeant
from network_topologies.geant import Geant
#from network_topologies.topology import Topology
#from network_topologies.topology_preprocessing import preprocess_metadata
# ROUTING ALGORITHMS
#from routing_algorithms.dijkstra import dijkstra
#from routing_algorithms.dijkstra import calculate_path
from routing_algorithms.dijkstra import set_spt
from routing_algorithms.ear import ear
# SERVICES
from service_flows.traffic_generator import TrafficGenerator


def read_from_json(json_path):
    """
    Returns data read from json file at found at 'json_path' location.

    Arguments:
        json_path {str} -- relative path of json file to be read.

    Returns:
        [dict] -- Dictionary with data read from json.
    """

    # Read data
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
    
    return data

def write_to_json(data, filename, json_path):
    """
    Write 'data' to json file named 'filename' at 'json_path' location.

    Arguments:
        data {dict} -- data to be written.
        filename {str} -- name of file to be created/overwritten.
        json_path {str} -- relative path of json file to be created/overwritten.
    """

    # Get the complete path
    filepath = os.path.join(json_path, filename)

    # Write data
    with open(filepath + '.json', 'w+') as f:
            json.dump(data, f, sort_keys=True, indent=4)

def main():

    """
    ********* TOPOLOGY SELECTION *********
    """
    #########################################################
    # Uncomment next lines to work with GEANT 2020 Topology #
    #########################################################
    #
    start_time = time.time()
    #
    topo = Geant()
    #
    print("--- %s seconds to build GEANT Topology ---" % (time.time() - start_time))

    #####################################################
    # Uncomment next lines to work with SIMPLE Topology #
    #####################################################
    #
    #start_time = time.time()
    #
    #topo_name = 'simple_network'
    #preprocess_metadata(topo_name)
    #node_dict = read_from_json("network_topologies/simple_network/simple_networkDB/nodes.json")
    #link_dict = read_from_json("network_topologies/simple_network/simple_networkDB/links.json")
    #topo = Topology(node_dict=node_dict, link_dict=link_dict)
    #
    #print("--- %s seconds ---" % (time.time() - start_time))

    ##########################################################
    # Uncomment next lines to work with PSEUDOGEANT Topology #
    ##########################################################
    #
    #start_time = time.time()
    #
    #topo = Pseudogeant()
    #topo.save_topology_info()
    #
    #print("--- %s seconds ---" % (time.time() - start_time))

    """
    ********* ALGORITHM SELECTION *********
    """
    #####################################################
    #           SIMPLE DIJKSTRA (OSPF-like)             #
    #####################################################
    #
    #start_time = time.time()
    #
    #set_spt(topo)
    #
    #print("--- %s seconds to set up DIJKSTRA ---" % (time.time() - start_time))
    #
    #####################################################
    #            ENERGY AWARE ROUTING (EAR)             #
    #####################################################
    #
    start_time = time.time()
    #
    ER_degree_threshold = 2
    ear(topo, ER_degree_threshold)
    #
    print("--- %s seconds to set up DIJKSTRA ---" % (time.time() - start_time))
    
    """
    ********* SERVICES example *********
    """

    # INSTANTIATE TRAFFIC GENERATOR
    tg = TrafficGenerator(interval=300, topology=topo)  # 300 s = 5 minutes
    
    
    while True:
        pass


if __name__ == "__main__":
    main()
