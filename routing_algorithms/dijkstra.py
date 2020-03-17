# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode
from .heap import build_min_heap

REFERENCE_BANDWIDTH = 300000.0  # 100 G


def dijkstra_cost(bandwidth, reference_bandwidth=REFERENCE_BANDWIDTH):
    """
    Returns link cost from its bandwidth.

    Arguments:
        bandwidth {float} -- Link Bandwidth in Mbps.
    
    Keyword Arguments:
        reference_bandwidth {float} -- Global reference bandwidth. (default: {REFERENCE_BANDWIDTH})
    
    Returns:
        [float] -- Link cost.
    """

    cost = reference_bandwidth/float(bandwidth)

    return cost


def dijkstra(root_name, topo):
    """
    Runs Dijkstra's algorithm on a given Topology.

    This function returns a list of the distances from 'root_node' to every other node of the network.

    Arguments:
        root_name {str} -- Name of root node.
        topo {Topology} -- Network Topology object.
    
    Returns:
        [list] -- List of distances from root node to every other node of the network.
    """

    ## INITIALIZATION PHASE
    
    # Get list of nodes and keep track of nodes' indices
    nodes = topo.node_names
    indices = [i for i in range(len(nodes))]

    # Create and initialize 'visited_node' to an empty set
    visited_nodes = set()

    # Get this topology cost matrix (metric -> link cost = bw/ref_bw)
    cost_matrix = topo.dijkstra_cost_matrix()
    
    # Create 'distances' and 'distance_node_matrix'
    distances = [None for i in range(len(nodes))]
    distance_node_matrix = [None] * len(nodes)
    #
    # distances -> [distance_0, distance_1, ..., distance_N] where N = len(nodes)
    #
    # distance_node_matrix[i] = [distance_i, node_name_i]
    # distance_node_matrix[i][0] = distance_i
    # distance_node_matrix[i][1] = node_name_i

    # Initialize all distance values to infinity.
    for i in range(len(nodes)):
        distances[i] = float("inf")
        distance_node_matrix[i] = [float("inf")]
        distance_node_matrix[i].append(nodes[i])

    # Get root index and set root distance to zero
    root_index = nodes.index(root_name)
    distances[root_index] = 0.0
    distance_node_matrix[root_index][0] = 0.0

    ## ITERATION PHASE
    while visited_nodes != set(nodes):  # While every node has not been visited yet
        
        # 1) Look for the node with the minimum known distance from root
        # At this iteration, The known distance of this node is the minimum possible from root.

        # Reorder distance_node_matrix and get the wanted node 
        build_min_heap(distance_node_matrix, indices)
        min_dist, min_node = distance_node_matrix[0][0], distance_node_matrix[0][1]

        # Remove this node from 'distance_node_matrix' and add it to 'visited_nodes'
        distance_node_matrix.pop(0)
        min_node_id = indices.pop(0)
        visited_nodes.add(min_node)

        # 2) Update this node's neighbors distance from root.
        #
        # ...
        min_node_obj = topo.get_one_node(min_node)
        neighbors = min_node_obj.neighbors_list

        for neighbor in neighbors:
            
            neighbor_id = nodes.index(neighbor)
            link_cost = cost_matrix[min_node_id][neighbor_id]
            
            if nodes[neighbor_id] not in visited_nodes:

                new_distance = min_dist + link_cost

                if distances[neighbor_id] > new_distance:
                    distances[neighbor_id] = new_distance
                    neighbor_index = indices.index(neighbor_id)
                    distance_node_matrix[neighbor_index][0] = distances[neighbor_id]

    return distances


def calculate_path(src, dst, topo, cost_matrix, distances_matrix):
    """
    Returns all the Equal-Cost Multi-Path (ECMP) between source and destination on a given topology.

    Arguments:
        src {str} -- Source node.
        dst {str} -- Destination node.
        topo {Topo} -- Topology.
        cost_matrix {list} -- Matrix of Dijkstra's cost metric between links.
        distances_matrix {list} -- Matrix of Dijkstra's calculated distances between nodes.
    
    Returns:
        [list] -- Matrix of Equal-Cost Multi-Paths between source and destination.
    """
    # Init Variables
    path = []
    ecmp = []
    
    # Get calculated minimum distance between src and dst
    nodes = topo.node_names
    src_i = nodes.index(src)
    dst_i = nodes.index(dst)
    min_dist = distances_matrix[src_i][dst_i]

    # Check if it is different from zero..
    # N.B. if it is zero, it means that src = dst
    if min_dist != 0:
        # ...if so, init variables and look for ECMPs between src and dst
        path.append(src)
        path_cost = 0
        spf_iteration(cost_matrix, min_dist, path, path_cost, nodes, dst, ecmp)
    
    # Check if ecmp is empty...
    if ecmp == []:
        # If so, it means that min_dist = 0 and that path is empty.
        # Add path to ecmp
        ecmp.append(path)
    
    return ecmp


def spf_iteration(cost_matrix, min_dist, path, path_cost, nodes, dst, ecmp):
    """
    This function look for Equal-Cost Multi-Path between source and destination.

    Each iteration look for possible valid paths between source and destination,
    evaluate them and finally add them to ecmp matrix only if their path cost is
    equal to the minimum distance calculated with Dijkstra's algorithm.
    
    Arguments:
        cost_matrix {list} -- Matrix of Dijkstra's cost metric between links.
        min_dist {float} -- Dijkstra's minimum distance between source and destination.
        path {list} -- Ordered list of nodes between source and destination at this iteration.
        path_cost {float} -- Cumulative metrics of links between nodes in path at this iteration.
        nodes {list} -- Topology nodes.
        dst {str} -- Destination.
        ecmp {list} -- Matrix of Equal-Cost Multi-Paths between source and destination, known at this iteration.
    """

    # Current node is the last node in path:
    current_node = path[-1]
    current_node_i = nodes.index(current_node)

    # Check if current node is the destination and path_cost is equal to minimum distance...
    if current_node == dst and path_cost == min_dist:
        # ...if so, it is a minimum distance path: add it to ecmp.
        ecmp.append(path)
    else:
        # ...if not, look for a minimum distance path:
        # 1) Visit current node neighbors
        neighbors = []
        neighbor_costs = []

        for i in range(len(nodes)):
            n = nodes[i]  # possible neighbor
            n_cost = cost_matrix[current_node_i][i]  # cost to get from current node to possible neighbor
        
            # Check if it is a real neighbor and if this neighbor has not been visited yet...
            if n_cost != float("inf") and n not in path:
                # ...if both are true, this possible neighbor is a real and valid neighbor
                neighbors.append(n)
                neighbor_costs.append(n_cost)

        # 2) Evaluate if this neighbor can be part of a minimum distance path: 
        for i in range(len(neighbors)):
            # Check if the cost of the path, adding this valid neighbor, is less than
            # or equal to the minimm distance between source and destination
            new_cost = path_cost + neighbor_costs[i]
            if new_cost <= min_dist:
                # ... if so, this new path could be a minimum distance path.
                new_path = path.copy() + [neighbors[i]]
                # Iterate to see if it is a minimum distance path.
                spf_iteration(cost_matrix, min_dist, new_path, new_cost, nodes, dst, ecmp)


def set_spt(topo):
    # TODO: write docstrings
    """
    
    Arguments:
        topo {[type]} -- [description]
    """

    # Get list of node names
    nodes = topo.node_names

    # Get distances_matrix
    distances_matrix = [None] * len(nodes)
    for i in range(len(nodes)):
        distances_matrix[i] = dijkstra(topo.node_names[i], topo=topo)
    
    # Get cost_matrix 
    cost_matrix = topo.dijkstra_cost_matrix()
    
    # Shortest Path Tree (SPT) calculation
    for i in range(len(nodes)):

        # Get the i-th node
        node_i = topo.nodes[i]
           
        # Init spt
        spt = {}
        # ...get the j-th node of the topology and calculate a path beween node_i and node_j (i != j)
        for j in range(len(nodes)):
            if i != j:
                node_j = topo.nodes[j]
                # ..add this path to spt.
                spt[node_i.name + node_j.name] = calculate_path(node_i.name, node_j.name, topo, cost_matrix, distances_matrix)[0]
        
        # Assign to node_i the calculated SPT
        node_i.spt = spt
        