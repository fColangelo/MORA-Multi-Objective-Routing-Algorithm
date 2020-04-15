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
# NETWORK OBJECTS
from utils.network_objects import *
# PA SERVICES
from service_flows.traffic_generator import TrafficGenerator
from itertools import permutations
import random
import numpy as np
from deap import algorithms, base, creator, tools, algorithms
import collections
#import matplotlib.pyplot as plt
import import_ipynb
import operator
import pandas as pd

topo = Geant(routing_method='EAR')
topo.save_topology_info()

def lol(s, d, max_hops, current_prefix = [], pts = []):
    current_prefix.append(s)
    N = topo.get_valid_links(current_prefix[-1])
    N = [x for x in N if x not in current_prefix]
    for n in N:
        if d == n:
            new = current_prefix.copy()
            new.append(d)
            pts.append(new)
            continue
        if len(current_prefix) <= max_hops-1:
            pts = lol(n, d, max_hops, current_prefix, pts)
    current_prefix.pop(-1)
    return pts         

lol('UK', 'DE', 3)