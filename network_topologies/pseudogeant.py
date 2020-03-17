# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import json
import os
from .topology import Topology

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

class Pseudogeant(Topology):

    def __init__(self, node_dict={}, link_dict={}):

        topo_name = 'pseudogeant'

        current_dir = os.path.dirname(__file__)
        meta_path = os.path.join(current_dir, topo_name, 'pseudogeant_metadata.json')
        meta = read_from_json(meta_path)
        if not node_dict:
            node_dict = meta['nodes']
        if not link_dict:
            link_dict = meta['links']

        super().__init__(name=topo_name, node_dict=node_dict, link_dict=link_dict)     
