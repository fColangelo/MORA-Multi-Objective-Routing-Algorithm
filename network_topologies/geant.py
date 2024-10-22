# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import json
import os
from .topology import Topology
from .topology_preprocessing import preprocess_metadata


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

class Geant(Topology):
    
    def __init__(self, node_dict={}, link_dict={}, routing_method = 'Dijkstra'):
        """
        Initialization Method of Geant object.

        Args:
            node_dict (dict, optional): Dictionary of nodes and nodes' properties. Defaults to {}.
            link_dict (dict, optional): Dictionary of links and links' properties. Defaults to {}.
            routing_method (str, optional): Name of the routing method used by this Geant object. Defaults to 'Dijkstra'.
        """

        topo_name = "geant"
        #preprocess_metadata(topo_name)

        # Get nodes and links data
        current_dir = os.path.dirname(__file__)
        db_path = os.path.join(current_dir, topo_name , topo_name + "DB")
        node_dict = read_from_json(db_path + "/nodes.json")
        link_dict = read_from_json(db_path + "/links.json")

        super().__init__(name=topo_name, node_dict=node_dict, link_dict=link_dict, routing_method=routing_method)     
        