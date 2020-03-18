# -*- coding: utf-8 -*-
from .dijkstra import dijkstra
from .dijkstra import calculate_path
from .dijkstra import set_spt
import time


def get_degree(node):
    """
    This function returns the degree of the node.
    
    Arguments:
        node {Node} -- Node.
    
    Returns:
        [int] -- Node degree, i.e. number of node's neighbors.
    """

    return len(node.neighbors_list)


def find_my_ER(node, topo, distances_matrix):
    """
    This function returns the nearest ER to a given IR node.
    The "nearest" ER is the ER node with the lowest Dijkstra metric from the given node. 

    Arguments:
        node {Node} -- Node.
        topo {Topology} -- Topology.
        distances_matrix {list} -- Matrix of Dijkstra's calculated distances between nodes.
    
    Returns:
        [Node] -- Nearest ER from a given IR node.
    """

    # Init distance_from_ER to 'infinity'
    distance_from_ER = float("inf")

    # For each neighbor of this node...
    for neighbor_name in node.neighbors_list:
        neighbor = topo.get_one_node(neighbor_name)
        
        # ...check if its role is 'ER'...
        if neighbor.role == 'ER':
                # ... if so, get its distance from this node.
                neighbor_index = topo.node_names.index(neighbor_name)
                node_index = topo.node_names.index(node.name)
                distance_from_neighbor = distances_matrix[node_index][neighbor_index]

                # Check if the distance of current neighbor ER is less than the currently known
                # smallest distance between this node and its neighbor ERs...                
                if distance_from_neighbor < distance_from_ER:
                    # ...if so, consider this neighbor as "myER"
                    distance_from_ER = distance_from_neighbor
                    myER = neighbor
    
    return myER

def spt2mpt(old_root, new_root):
    """
    This function calculates the MPT of 'new_root'.
    The MPT is calculated starting from the SPT of 'old_root', that is the nearest ER node to 'new_root'.

    Arguments:
        old_root {Node} -- [description]
        new_root {Node} -- [description]
    
    Returns:
        [list] -- [description]
    """

    spt = old_root.spt
    mpt = {}
    old_new_path_name = old_root.name+new_root.name
    new_old_path = spt[old_new_path_name].copy()
    new_old_path.reverse()
    new_old_path.pop()

    for path_name in spt:
        path = spt[path_name]
        if path_name == old_new_path_name:
            mpt_path = spt[path_name].copy()
            mpt_path.reverse()
        elif new_root.name in path:
            index = path.index(new_root.name)
            mpt_path = path[index:].copy()
        else:
            mpt_path = new_old_path + path
        
        mpt_path_name = mpt_path[0]+mpt_path[-1]
        mpt[mpt_path_name] = mpt_path
    
    return mpt

# Energy-Aware Routing
def ear(topo, thrs):

    # Get list of node names
    nodes = topo.node_names


    #### PHASE 1 : ER SELECTION

    # ER Condition: I am an ER if...
    # 
    # 1) There are no ER between my neighbors
    # 2) My degree is >= thrs
    #
    # N.B. The degree of a node is the number of links of the node.
    #

    #
    # IR Condition: I am an IR if at least one of my neighbors is an ER
    #

    #
    # NR Condition: I am a NR if...
    #
    # 1) There are no ER between my neighbors
    # 2) My degree is < thrs
    #
    # ATTENTION: by default all nodes are NR
    
    # Init degree_ranked_nodes
    degree_ranked_nodes = [None] * len(nodes)

    ## Calculate the degree of each node and rank (reverse order) them by this value
    for i in range(len(nodes)):
        node_i = topo.nodes[i]
        degree_ranked_nodes[i] = [get_degree(node_i), node_i.name]
    degree_ranked_nodes.sort(reverse=True)

    ## Define nodes' roles
    for element in degree_ranked_nodes:

        # Init notERneighbors for the current element
        notERneighbors = 0

        # Get a node, its degree and its neighbors
        node = topo.get_one_node(element[1])
        degree = element[0]
        neighbors = node.neighbors_list

        # For each neighbor of this node...
        for i in range(len(neighbors)):
            # get neighbor object
            neighbor = topo.get_one_node(neighbors[i])

            # Check if current node role is different from 'IR' and current neighbor role is 'ER'...
            if node.role != 'IR' and neighbor.role == 'ER':
                # ...if so, current node is an IR
                topo.change_node_role(node, 'IR')
                break
            else:
                # ...if not, increase notERneighbors
                notERneighbors += 1

        # Once checked all the neighbors, if notERneighbors is equal to the number of neighbors
        # and the degree is > thrs...
        if notERneighbors == len(neighbors) and degree > thrs:
            # ...current node is an ER
            topo.change_node_role(node, 'ER')
        # otherwise it remains an NR/IR            
    
    #### PHASE 2: MPT EVALUATION

    # Get distances_matrix
    distances_matrix = [None] * len(nodes)
    for i in range(len(nodes)):
        distances_matrix[i] = dijkstra(topo.node_names[i], topo=topo)
    
    # Get cost_matrix 
    cost_matrix = topo.dijkstra_cost_matrix()
    
    ## Shortest Path Tree (SPT) calculation for ER and NR nodes
    for i in range(len(nodes)):

        # Get the i-th node
        node_i = topo.nodes[i]

        ## Shortest Path Tree (SPT) calculation for ER and NR nodes
        # If it is an ER or a NR...
        if node_i.role != 'IR':
            
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
        """
        ## Modified Shortest Path Tree (MPT) calculation for IR nodes
        # If it is an IR...
        else:

            # ...find the nearest ER
            myER = find_my_ER(node_i, topo, distances_matrix)
            
            # ...and calculate the MPT.
            mpt = spt2mpt(myER, node_i)

            # Assign to node_i the calculated MPT (as if it was an SPT) 
            node_i.spt = mpt
        """
    ## Modified Shortest Path Tree (MPT) calculation for IR nodes
    for i in range(len(nodes)):

        # Get the i-th node
        node_i = topo.nodes[i]

        # If it is an IR...
        if node_i.role == 'IR':
            
            # ...find the nearest ER
            myER = find_my_ER(node_i, topo, distances_matrix)
            
            # ...and calculate the MPT.
            mpt = spt2mpt(myER, node_i)

            # Assign to node_i the calculated MPT (as if it was an SPT) 
            node_i.spt = mpt
    

    ## SWITCH OFF unused links
        
    # Init used_links
    used_links = []

    # Find used links
    for i in range(len(nodes)):

        # Get the i-th node
        node_i = topo.nodes[i]

        # For each path in node_i SPT..
        for path in node_i.spt:
            # Get link between node_i and the first next-hop in path
            nodeA = node_i.spt[path][0]  # = node_i
            nodeB = node_i.spt[path][1]
            link = topo.get_link_between_neighbors(nodeA, nodeB)

            # If this link is not in used_links yet...
            if link not in used_links:
                # ... add it to used_links
                used_links.append(link)
       
    # Find unused links
    used_links_set = set(used_links)
    # unused_links = all links that are in topo.links but not in used_links
    unused_links = [x for x in topo.links if x not in used_links_set]
    
    # Switch off all links that are in unused_links
    for link in unused_links:
        topo.switch_off_link(link)
    

    #### PHASE 3: ROUTING PATH OPTIMIZATION

    # Re-calculate SPT for all nodes on new topology
    set_spt(topo)
