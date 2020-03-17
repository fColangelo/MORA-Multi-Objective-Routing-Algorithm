import sys
sys.dont_write_bytecode
import os
import json
import time
# TOPOLOGIES
from network_topologies.pseudogeant import Pseudogeant
from network_topologies.geant import Geant
from network_topologies.topology import Topology
from network_topologies.topology_preprocessing import preprocess_metadata
# ROUTING ALGORITHMS
from routing_algorithms.dijkstra import dijkstra
from routing_algorithms.dijkstra import calculate_path
from routing_algorithms.dijkstra import set_spt
from routing_algorithms.ear import ear
from routing_algorithms.mora import *
# SERVICES
from service_flows.traffic_generator import TrafficGenerator
from itertools import permutations
import random
import numpy as np
from deap import algorithms, base, creator, tools, algorithms
import collections
import matplotlib.pyplot as plt
import import_ipynb


class Hop_by_hop_Path_cost_1():
    def __init__(self, topology, beta = 1.5): 
        #Paper values
        self.beta = beta
        self.topology = topology
        self.link_power_model = Power_consumption_model()
        
    def hops(self, path):
        return len(path)
    
        
    def get_x_0(self, path):
        d = path[-1]
        
        return self.topology.get_x_0(d)
    
    def get_link_power_cost(self, link, traffic_volume):
        return self.link_power_model.get_power_consumption(link.n_links, traffic_volume)
        
    def get_path_cost(path):
        cost = 0
        for idx in range(len(path)-1):
            x_0 = get_x_0(path)
            shortest_pt = self.topology.get_shortest(path[idx], path[-1])
            cost += get_link_power_cost(self.topology.get_links_n(path[idx], path[idx+1]), x_0 * np.power(beta, self.hops(shortest_pt)))
            
        return cost