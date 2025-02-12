# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import json
import os, operator
import numpy as np
from deap import algorithms, base, creator, tools, algorithms

## ROUTING ALGORITHMS
# MORA
from routing_algorithms.mora_v2 import *
# DIJKSTRA
from routing_algorithms.dijkstra import dijkstra_cost
from routing_algorithms.dijkstra import set_spt
# EAR
from routing_algorithms.ear import ear


def write_to_json(data, filename, json_path):
    """
    Write 'data' to json file named 'filename' at 'json_path' location.

    Arguments:
        data {dict} -- data to be written.
        filename {str} -- name of file to be created/overwritten.
        json_path {str} -- relative path of json file to be created/overwritten,
    """

    # Get the complete path
    filepath = os.path.join(json_path, filename)

    # Write data
    with open(filepath + '.json', 'w+') as f:
            json.dump(data, f, sort_keys=True, indent=4)

class Topology:

    def __init__(self, name='topology', node_dict={}, link_dict={}, routing_method = 'Dijkstra', MORA_max_hops = 3):
        """
        Initialization Method of Topology object.

        Keyword Arguments:
            name {str} -- Name of this Topology (default: {'topology'}).
            node_dict {dict} -- Dictionary of nodes and nodes' properties (default: {{}}).
            link_dict {dict} -- Dictionary of links and links' properties (default: {{}}).
        
        N.B. There are no consistency checks between input node_dict and input link_dict.
        """

        self.name = name            # this Topology name
        self.nodes=[]               # list of Node objects belonging to this Topology
        self.links=[]               # list of Link objects belonging to this Topology
        self.node_names=[]          # list of node names
        self.link_names=[]          # list of link ids
        self.node_dict = {}         # dictionary of nodes and nodes' properties
        self.link_dict = {}         # dictionary of links and links' properties
        self.current_flows = []     # list of currently applied flows on this Topology
        self.faulty_node_list = []  # list of faulty nodes
        
        # Create this Topology nodes and links 
        self.create_topology(node_dict, link_dict)
        self.reset()

        # Setup routing method
        self.reachability_matrix = self.get_reachability_matrix()  # this Topology reachability matrix
        self.routing_method = routing_method
        self.init_routing_method(routing_method)

    # ************ GENERAL PURPOSE METHODS ************

    def create_topology(self, node_dict, link_dict):
        """
        Create nodes and links.
        Arguments:
            node_dict {dict} -- Dictionary of nodes and nodes' properties (default: {{}}).
            link_dict {dict} -- Dictionary of links and links' properties (default: {{}}).
        """

        # Create nodes
        for node_info in node_dict:
            self.create_node(info=node_dict[node_info])

        # Create links
        for link_info in link_dict:
            self.create_link(info=link_dict[link_info])

    def reset(self):
        """
        Resets all topology nodes and links status.
        Node/Link status attribute is set to 'on'.
        """

        print("Resetting network topology... ", end='')
        
        for node in self.nodes:
            node.status = 'on'
        for link in self.links:
            link.status = 'off'
            link.status = 'on'
        
        print("OK!")
        
        return

    def is_reachable(self, src_node, dst_node):
        """
        This function states if dst_node is reachable from src_node based on the current network operational status.
        
        Arguments:
            src_node {str} -- Source node name.
            dst_node {str} -- Destination node name.
        
        Returns:
            [boolean] -- True if dst_node is reachable; False vice versa.
        """

        src_index = self.nodes.index(src_node)
        dst_index = self.nodes.index(dst_node)

        return self.reachability_matrix[src_index][dst_index]

    def clear_flow_from_network(self, flow):
        """Remove a flow from every link in the network
        
        Arguments:
            flow {[dict]} -- dictionary containing the flow information
        """
       
        for link in self.links:
            if link.status == 'on' and flow['_id'] in link.service_flows:
                link.remove_service_from_link(flow)

    ## NODES

    def create_node(self, info):
        """
        Create a node to be added to this Topology.

        Keyword Arguments:
            info {dict} -- Dictionary of node properties. (default: {{}})
            name {str} -- Node name. (default: {''})
        """
        
        # Create node object
        node = Node(info)

        # Add node to this Topology
        self.add_node(node)

    def add_node(self,node):
        """
        Add 'node' to this Topology.

        Arguments:
            node {Node} -- node to be added.
            info {dict} -- Dictionary of node properties.
        """
        
        # Add node object to this Topology node list 'nodes'
        self.nodes.append(node)

        # Add node name to this Topology node name list 'node_names'
        self.node_names.append(node.name)
        
        # ...add it to this Topology node info dictionary 'node_dict'
        self.node_dict['node{}'.format(len(self.node_dict) + 1)] = node.info

    def get_one_node(self, node_name):
        """
        Return Node object with name 'node_name'.
        
        Arguments:
            node_name {str} -- Name of Node object.
        
        Raises:
            Exception: node not in this Topology.
        
        Returns:
            [Node] -- Node object with name 'node_name'
        """
        
        for node in self.nodes:
            if node.name == node_name:
                return node
        
        raise Exception('*** NODE {} IS NOT IN THIS TOPOLOGY! ***'.format(node_name))

    def update_node_info(self, node):
        """
        Update node information.

        Args:
            node (Node): node to be updated.
        """

        node_name = node.name
        for n in self.node_dict:
            if  node_name in self.node_dict[n]['_id']:
                self.node_dict[n] = node.info
                break

    def shutdown_node(self, node_name):
        """
        Shuts down node named 'node_name', i.e. its status attribute is set to 'off'.
        
        When a node is shut down, all the links having this node as endpoint are shut down too.
        All the traffic flows coupled to these links are considered 'disrupted flows'.

        Args:
            node_name (string): node name.

        Returns:
            [list]: list of disrupted flows.
        """
        node = self.get_one_node(node_name)

        node.status = 'off'
        self.update_node_info(node)

        disrupted_flows_ids = []

        # Get currently active node's links and shutdown them
        links_to_shut = node.active_links_list.copy()
        for link in links_to_shut:
            # Get this link object
            link_obj = self.get_one_link(link)
            # Get flows that are going to be disrupted by this link switching off
            disrupted_flows_ids.extend(link_obj.service_flows)
            # Switch off this link
            self.switch_off_link(link_obj)
        
        # Remove duplicate elements from disrupted_flows_ids and return it
        return list(set(disrupted_flows_ids))

    ## LINKS

    def create_link(self, info={}):
        """
        Create a link between two nodes of this Topology.

        Keyword Arguments:
            info {dict} -- Dictionary of links and links' properties (default: {{}}) 
        """

        # Create link object
        link = Link(info)
        
        # Add link to this Topology
        self.add_link(link)

    def add_link(self, link):
        """
        Add 'link' to this Topology.

        Arguments:
            info {dict} -- Dictionary of link properties.
        """
        
        # Add link object to this Topology link list 'links'
        self.links.append(link)
        
        # Add link name to this Topology link name list 'link_names'
        self.link_names.append(link.id)
        
        # ... add it to this Topology link info dictionary 'link_dict'
        self.link_dict['link{}'.format(len(self.link_dict) + 1)] = link.info

    def get_one_link(self, link_name):
        """
        Return Link object with id 'link_name'.

        Arguments:
            link_name {str} -- ID of Link object.
        
        Raises:
            Exception: link not in this Topology.
        
        Returns:
            [Link] -- Link object with ID 'link_name'
        """

        for link in self.links:
            if link.id == link_name:
                return link
        
        raise Exception('*** LINK {} IS NOT IN THIS TOPOLOGY! ***'.format(link_name))
    
    def update_link_info(self, link):
        """
        Update link information.

        Args:
            link (Link): link to be updated.
        """

        link_id = link.id
        for l in self.link_dict:
            if  link_id in self.link_dict[l]['_id']:
                self.link_dict[l] = link.info
                break
    
    def get_link_between_neighbors(self, nodeA_name, nodeB_name):
        """
        Returns the Link object between two nodes.

        Arguments:
            nodeA_name {string} -- Name of link's endpoint A.
            nodeB_name {string} -- Name of link's endpoint B.
        
        Raises:
            Exception: endpoints A and B are not neighbors.
            Exception: endpoints A and B are neighbors but no link between them was found.
        
        Returns:
            [Link] -- Link object between nodeA and nodeB.
        """

        nodeA = self.get_one_node(nodeA_name)
        nodeB = self.get_one_node(nodeB_name)

        # Check if node A and node B are real neighbors
        nodeA_neighbors = nodeA.neighbors_list
        nodeB_neighbors = nodeB.neighbors_list

        if nodeA.name not in nodeB_neighbors:
            raise Exception("*** {} IS NOT {}'s NEIGHBOR! ***".format(nodeA_name,nodeB_name))
        if nodeB.name not in nodeA_neighbors:
            raise Exception("*** {} IS NOT {}'s NEIGHBOR! ***".format(nodeB_name,nodeA_name))
        
        # Find and return the link between A and B
        nodeA_links = nodeA.links_list
        for l in nodeA_links:
            link = self.get_one_link(l)
            if link.node1 == nodeA_name and link.node2 == nodeB_name:
                return link
        
        raise Exception("*** UNEXPECTED ERROR: {} AND {} ARE NEIGHBORS BUT NO LINK BETWEEN THEM WAS FOUND!".format(nodeA_name, nodeB_name))

    def update_link_status(self):
        for l in self.links:
            if l.consumed_bandwidth == 0:
                l.status('off')
            else:
                l.status('on')
        return

    ## SERVICES

    def get_shortest_path(self, flow):
        """
        Returns the shortest path between source and destination nodes of a given flow.

        Args:
            flow (dict): service flow attributes.

        Returns:
            [list]: ordered list of nodes that compose the shortest path between source and destination. 
        """

        src_name = flow['node1']
        dst_name = flow['node2']
        src = self.get_one_node(src_name)

        # Look for the path in the 'spt' list of source node that terminates at the destination node.
        for _, path in src.spt.items():
            if path[0] == src_name and path[-1] == dst_name:
                return path

    def get_current_flows(self):
        return self.current_flows

    def apply_service_on_network(self, service_flow, path):
        """
        Applies a service flow on the links along the path. 

        Args:
            service_flow (dict): service flow attributes.
            path (list): list of nodes between flow source and destination.
        """

        # Update current flows
        self.current_flows.append(service_flow)

        for i in range(len(path)-1):
            link = self.get_link_between_neighbors(path[i], path[i+1])
            link.apply_service_on_link(service_flow)
            self.update_link_info(link)
        self.save_topology_info()

    def remove_service_from_network(self, service_flow, path):
        """
        Removes a service flow from the links along the path. 

        Args:
            service_flow (dict): service flow attributes.
            path (list): list of nodes between flow source and destination.
        """

        # Update current flows
        self.current_flows.remove(service_flow)

        for i in range(len(path)-1):
            link = self.get_link_between_neighbors(path[i], path[i+1])
            link.remove_service_from_link(service_flow)
            self.update_link_info(link)
        self.save_topology_info()        

    def get_reliability_score(self):
        # Return the max reliability score (for the most used link) 
        # and the mean reliability score over the network the network, for logging purposes

        reliabilities = [eval_bandwidth_single_link(x.bandwidth_usage) for x in self.links if x.status == 'on']
        above_threshold = len([x for x in reliabilities if x > 0.6])
        return np.max(reliabilities), above_threshold

    def get_power_consumption(self):
        # Return the overall power consumption of the network, for logging purposes
        powers = [x.power_consumption_MORA for x in self.links if x.status == 'on']
        return np.sum(powers)

    def get_link_usages(self):
        # Return the list of link percentage usage over all the network, for logging purposes
        return [x.bandwidth_usage for x in self.links]

    ## TOPO OBJECT

    def save_topology_info(self):
        """
        Saves topology info.
        
        'node_dict' and 'link_dict' are saved in folder ."self.name"/"self.name"DB/
        respectively in the files nodes.json and links.json.

        """

        # Build up database_path
        current_dir = os.path.dirname(__file__)
        database_folder = self.name + 'DB'
        database_path = os.path.join(current_dir, self.name, database_folder)
        
        # If it doesn't exists, create it
        if not os.path.exists(database_path):
            os.mkdir(database_path)

        # Save nodes and links data
        write_to_json(self.node_dict, 'nodes', database_path)
        write_to_json(self.link_dict, 'links', database_path)
    
    ## REACHABILITY MATRIX

    def depth_first_search(self, current_node, reachable_nodes):
        """
        Depth-First Search (DFS) recursive function.

        Arguments:
            current_node {Node} -- [description]....
            reachable_nodes {List} -- List of Boolean values....
        """

        # Label current_node as reachable
        current_node_index = self.nodes.index(current_node)
        reachable_nodes[current_node_index] = True

        # For all current node's active neighbors...
        for node in current_node.active_neighbors_list:
            # ...if they are not already labeled as reachable...
            current_neighbor = self.get_one_node(node)
            current_neighbor_index = self.nodes.index(current_neighbor)
            if not reachable_nodes[current_neighbor_index]:
                # ...recuresively call depth_first_search
                self.depth_first_search(current_neighbor, reachable_nodes)

    def get_reachability_matrix(self):
        """
        Creates and returns the Reachability Matrix.

        Reachability Matrix is a square matrix of degree N, where N is the number of nodes in a network.
        The element a_ij is equal to True if node j is reachable from node i, and False otherwise.
        N.B. "reachable" means that a path exists between node i and node j.

        Returns:
            [list] -- Reachability Matrix.
        """

        reachablity_matrix = []

        for node in self.nodes:

            reachable_nodes = [False] * len(self.nodes)
            
            self.depth_first_search(node, reachable_nodes)
            
            reachablity_matrix.append(reachable_nodes)
        
        return reachablity_matrix

    def print_reachability_matrix(self):
        """
        Prints the Reachability Matrix on screen.
        """

        if self.reachability_matrix is None:
            self.reachability_matrix = self.get_reachability_matrix()
        for row in self.reachability_matrix:
            print(row)
        return

    ## ADJACENCY MATRICES

    def get_adjacency_matrix(self):
        """
        Creates and returns the Adjacency Matrix.

        Adjacency Matrix is a square matrix of degree N, where N is the number of nodes in a network.
        The element a_ij is equal to 1 if node j is adjacent to node i, and 0 otherwise.
        N.B. "adjacent" means that a link exists between node i and node j.

        Returns:
            [list] -- Adjacency Matrix. 
        """

        adj_matrix = [[ 0 for i in range(len(self.nodes))] for j in range(len(self.nodes))]
        sorted_nodes = sorted(self.node_names)
        for i in range(len(self.nodes)):
            node_i = sorted_nodes[i]
            for j in range(len(self.nodes)):
                node_j = sorted_nodes[j]
                if self.is_connection_possible(node_i, node_j):
                    adj_matrix[sorted_nodes.index(node_i)][sorted_nodes.index(node_j)] = 1
        
        return adj_matrix

    def get_operational_adjacency_matrix(self):
        """
        Creates and returns the Operational Adjacency Matrix.

        Operational Adjacency Matrix is a square matrix of degree N, where N is the number of nodes in a network.
        The element a_ij is equal to 1 if node j is operationally adjacent to node i, and 0 otherwise.
        N.B. "operationally adjacent" means that an active (i.e. switched on) link exists between node i and node j.

        Returns:
            [list] -- Operational Adjacency Matrix. 
        """
        
        # Initialize adj_matrix (i: rows index, j: columns index)
        op_adj_matrix = [[ 0 for i in range(len(self.nodes))] for j in range(len(self.nodes))]

        # Consider i-th row:
        for i in range(len(self.nodes)):
            # get i-th node from node_names..
            node_i = self.node_names[i]

            for j in range(len(self.nodes)):
                # ..and get j-th node from node_names too.
                node_j = self.node_names[j]
                
                # Consider the following link id:
                link_name = node_i + node_j

                # If it is in 'link_names' list..
                if link_name in self.link_names:
                    # ..link exists...
                    
                    link = self.get_one_link(link_name)

                    if link.status == 'on':
                        op_adj_matrix[i][j] = 1  # ..and it is turned on: 1
                    else:
                        op_adj_matrix[i][j] = 0  # ..but it is switched off: 0
                
                else:
                    op_adj_matrix[i][j] = 0  #..otherwise, link doesn't exists: 0.
        
        return op_adj_matrix

    def __repr__(self):
        # Print a readable version of the adjacency matrix
        adj_matrix=self.get_adjacency_matrix()        
        rep = '**** ADJACENCY MATRIX ****\n'  
        rep += '\n' 
        node_names = sorted(self.node_names)
        rep += '     '
        for i in range(len(adj_matrix)):
            rep += node_names[i] + '    '
        rep +=  '\n'    
        for i in range(len(adj_matrix)):
            rep +=' ' + node_names[i]
            for j in range(len(adj_matrix)):
                if adj_matrix[i][j] == 1:
                    rep += ' [xx] '
                else:
                    rep += ' [  ] '
            rep +=  '\n'
        
        rep += '**************************'
        
        return rep

    def pretty_print_adjacency_matrix(self, adj_matrix):
        """
        Print adjacency matrix in a human readable form.

        Arguments:
            adj_matrix {list} -- Adjacency Matrix.

        N.B. Node names must be all of the same length. 
        """

        print('**** ADJACENCY MATRIX ****')
        print('')

        for i in range(len(adj_matrix)):
            begin_of_row = ' ' + self.node_names[i] + ' '
            print(begin_of_row, end='')
            for j in range(len(adj_matrix)):
                if adj_matrix[i][j] == 1:
                    print(' [xx] ', end='')
                else:
                    print(' [  ] ', end='')
            print('\n')
        
        print('**************************')

    # ************ GENERAL ROUTING METHODS ************

    def init_routing_method(self, routing_method):

        if routing_method == 'Dijkstra':
            self.init_Dijkstra()
            self.get_path = self.get_shortest_path
        elif routing_method == 'EAR':
            self.init_EAR()
            self.get_path = self.get_shortest_path
        elif routing_method == 'MORA':
            self.init_MORA(max_hops = 3, favored_attr = 'Power consumption')
            self.get_path = get_optimize_route(self, self.toolbox)
        elif routing_method == 'Hop_by_hop':
            self.init_Hop_by_hop()
            self.get_path = self.get_path_hop_by_hop
        else:
            raise NotImplementedError

    # ************ DIJKSTRA ANCILLARY METHODS ************

    def init_Dijkstra(self):
        """
        Dijkstra initialization method.
        """

        set_spt(self)

    def dijkstra_cost_matrix(self):
        """
        Creates and returns the Cost Matrix.
        Cost Matrix is a square matrix of degree N, where N is the number of nodes in a network.
        The element a_ij is equal to the cost of the link between nodes i and j.
        If a link between nodes i and j does not exist -> a_ij = infinity

        Returns:
            [list] -- Cost Matrix.
        """

        # Initialize cost_matrix (i: rows index, j: columns index)
        cost_matrix = self.get_operational_adjacency_matrix()

        # Consider i-th row:
        for i in range(len(self.nodes)):
            # get i-th node from node_names..
            node_i = self.node_names[i]

            for j in range(len(self.nodes)):
                # ..and get j-th node from node_names too.
                node_j = self.node_names[j]

                # Check if node_i and node_j are neighbors...
                if cost_matrix[i][j] == 1:
                    # ..if so, get the cost of the link between them..
                    link_ij = self.get_link_between_neighbors(node_i, node_j)
                    cost_ij = dijkstra_cost(link_ij.total_bandwidth)
                    # ..and update cost matrix [i][j] with the actual cost.
                    cost_matrix[i][j] = cost_ij
                else:
                    # .., otherwise, link doesn't exists: set cost to infinity.
                    cost_matrix[i][j] = float("inf")

        return cost_matrix

    # ************ EAR ANCILLARY METHODS ******************

    def init_EAR(self):
        """
        EAR initialization method.
        """

        ER_degree_threshold = 2
        ear(self, ER_degree_threshold)

    def switch_off_link(self, link):
        """
        Switches off a topology link.

        Args:
            link (Link): link to be switched off.
        """

        link.status = 'off'
        self.update_link_info(link)
        
        # UPDATE NODE 1
        node1_obj = self.get_one_node(link.node1)
        node1_obj.shutdown_link(link)
        self.update_node_info(node1_obj)

        # UPDATE NODE 2
        node2_obj = self.get_one_node(link.node2)
        node2_obj.shutdown_link(link)
        self.update_node_info(node2_obj)

        # UPDATE REACHABILITY MATRIX
        self.reachability_matrix = self.get_reachability_matrix()

    def turn_on_link(self,link):
        """
        Turns on a topology link.

        Args:
            link (Link): link to be turned on.
        """

        link.status = 'on'
        self.update_link_info(link)
        
        # UPDATE NODE 1
        node1_obj = self.get_one_node(link.node1)
        node1_obj.startup_link(link)
        self.update_node_info(node1_obj)

        # UPDATE NODE 2
        node2_obj = self.get_one_node(link.node2)
        node2_obj.startup_link(link)
        self.update_node_info(node2_obj)

        # UPDATE REACHABILITY MATRIX
        self.reachability_matrix = self.get_reachability_matrix()

    def change_node_role(self, node, role):
        """
        Changes node role.

        Args:
            node (Node): node to be modified.
            role (string): new role for the node.
        """

        node.role = role
        self.update_node_info(node)
       
    # ************ MORA ANCILLARY METHODS ************

    def enumerate_paths(self, s, d, max_hops, current_prefix = [], pts = []):
        """Get all the paths from node s to node d up to length max_hops.

        Args:
            s ([int]): the source node
            d ([int]): the destination node
            max_hops ([int]): the maximum number of hops considered for paths from s to d.
            current_prefix (list): Called recursively, the current prefix that is being examined. Defaults to [].
            pts (list, optional): Called recursively, paths calculated up to this moment. Defaults to [].

        Returns:
            pts [list]: list of all the paths
        """
        current_prefix.append(s)
        N = self.get_valid_links(current_prefix[-1])
        N = [x for x in N if x not in current_prefix]
        for n in N:
            if d == n:
                new = current_prefix.copy()
                new.append(d)
                pts.append(new)
                continue
            if len(current_prefix) <= max_hops-1:
                pts = self.enumerate_paths(n, d, max_hops, current_prefix, pts)
        current_prefix.pop(-1)
        return pts   

    def is_connection_possible(self, node_1, node_2):
        """Helper method to check if two nodes can be connected

        Args:
            node_1 ([int])
            node_2 ([int])

        Returns:
            [Boolean]: Wheter the connecyion is possible
        """
        node_1_links = self.get_valid_links(node_1)
        if node_2 in node_1_links:
            return True
        else:
            return False

    def get_valid_links(self, node):
        """Get all the valid links (neighbors) for node

        Args:
            node ([int])

        Returns:
            [list]: the nodes adjacent to node
        """
        n = [x for x in self.nodes if x.name == node][0]
        node_links = n.neighbors_list

        return sorted(node_links)

    def has_loops(self, path):
        """Check if a path has loops

        Args:
            path ([list]): the path to be examined

        Returns:
            [Bool]: True if the path has loops, false otherwise
        """
        has_loops = (len(path) != len(set(path)))                                                                     
        return has_loops 

    def is_valid(self, path):
        """Check if all the connections in path are valid (a link exist)

        Args:
            path ([list]): the path to be examined

        Returns:
            [Bool]: True if all the connection are valid
        """
        for idx in range(len(path)-1):
            if path[idx+1] not in self.get_valid_links(path[idx]):
                return False
        return True

    def generate_mutation_support(self, max_hops):
        """Get a list of paths for use in the mutation procedure.
        For each pair of nodes, get all the paths up to length max_hops.

        Args:
            max_hops ([int]): maximum path length considered

        Returns:
            [list]: a list containing tuples in the form (node1, node2, list of paths)
        """
        mutation_support = []
        for ni in self.node_names:
            for nj in self.node_names:
                exist = fetch_paths(ni, nj, mutation_support)
                if ni != nj and not exist:
                    pt = self.enumerate_paths(ni, nj, max_hops, [], [])
                    # Structure node_1, node_2, list of all possible paths 
                    # up to length max_hops
                    mutation_support.append((ni, nj, pt))
        return mutation_support

    def generate_MORA_routes(self):
        """Generate a list of paths to support the multi-objective optimization
        For each pair of nodes, get the shortest path of length l. Then fetch all the paths of length l+2.

        Returns:
            [list]: a list containing tuples in the form (node1, node2, list of paths)
        """
        mora_routes = []
        for ni in self.node_names:
            for nj in self.node_names:
                exist = fetch_paths(ni, nj, mora_routes)
                if ni != nj and not exist:
                    shortest = self.get_shortest_path({'node1': ni, 'node2': nj})
                    pt = self.enumerate_paths(ni, nj, len(shortest)+2, [], [])
                    mora_routes.append((ni, nj, pt+[shortest]))
        return mora_routes

    def init_MORA(self, max_hops = 3, favored_attr = 'Power consumption'):
        """Initialize the multi-objective optimization. Set the meta-heuristic attribute.
        Set DEAP attributes that are not flow-specific.
        See DEAP documentation for more information on the toolbox attributes.

        Args:
            max_hops (int, optional): Length of the sub-paths considered in the mutation phase. Defaults to 3.
            favored_attr (str, optional): Meta-heuristic to decide between multiple Pareto-optimal solutions. 
            Defaults to 'Power consumption'.
        """
        if favored_attr == 'Shortest path':
            self.meta_heuristic = 0
        elif favored_attr == 'Latency':
            self.meta_heuristic = 1        
        elif favored_attr == 'Power consumption':
            self.meta_heuristic = 2
        elif favored_attr == 'Reliability':
            self.meta_heuristic = 3

        self.node_connectivity = []
        for ni in self.nodes:
            self.node_connectivity.append((ni.name, len(ni.neighbors_list)))

        creator.create("FitnessMultiObj", base.Fitness, weights=(-1.0, -1.0, -1.0, -1.0)) 
        creator.create("Individual", list, fitness=creator.FitnessMultiObj)
        self.toolbox = base.Toolbox()
        self.toolbox.register("mate", crossover_one_point, topology=self, ind_class=creator.Individual, toolbox=self.toolbox)
        self.toolbox.register("select", tools.selNSGA2)
        self.toolbox.register("mutate", mutate_path, topology=self, indi_class=creator.Individual)
        
        set_spt(self)
        self.mora_routes = self.generate_MORA_routes()
        self.mutation_support = self.generate_mutation_support(max_hops)

        return

    # ************ HOP BY HOP ANCILLARY METHODS ************
    ############## NOT USED FOR THE PAPER ##################
    def init_Hop_by_hop(self):
        for node in self.nodes:
            input_capacity = 0
            for neighbor in node.neighbors_list:
                input_capacity += self.get_link_between_neighbors(neighbor, node.name).total_bandwidth
            node.x_0 = input_capacity/800
        return
                
    def get_path_hop_by_hop(self, flow_dic):
        dest = flow_dic['node2']
        source = flow_dic['node1']
            # Dictionary: for each node, the item is the current weight to get to that node
        node_paths_weights = {}
        # Dictionary: for each node, store the shortest path to that node
        # Difference from paper: in the paper phi stores only the predecessor (no real difference)
        node_paths = {}
        node_list = []
        pt = [source]
        for n in self.nodes:
            if n.name != dest:
                node_paths_weights[n.name] = np.inf
            else:
                node_paths_weights[n.name] = 0
            node_paths[n.name] = []
            node_list.append(n.name) 
        # Set looping condition
        processed_nodes = []

        while processed_nodes != node_list:
            # Get node with minimum weigth # What exactly are the w
            # Extract_min
            for n in sorted(node_paths_weights.items(), key=operator.itemgetter(1)):
                if n[0] not in processed_nodes:
                    cn = n[0]
                    break
            cn = self.get_one_node(cn)
            # if current node == source
            if cn.name == source:
                nn = source
                while nn != dest:
                    nn = node_paths[nn]
                    pt.insert(0, nn) 
                return list(reversed(pt))
            # Get neighbors of n. For each neighbor...
            for ne in cn.neighbors_list:

                # Get link between nodes
                link = self.get_link_between_neighbors(cn.name, ne)
                x_m = link.average_link_usage
                # weight to get from cn to ne
                w = link.get_power_consumption(x_m + self.get_one_node(ne).x_0) - link.get_power_consumption(x_m)
                # If this path is shorter
                #print(ne, w)
                #print(node_paths_weights[cn.name] + w, node_paths_weights[ne])
                if node_paths_weights[cn.name] + w < node_paths_weights[ne]:
                    # The path to this node passes through cn
                    node_paths[ne] = cn.name 
                    # The weight of this path is equal to the weight to cn + the weight cn->ne
                    node_paths_weights[ne] = node_paths_weights[cn.name] + w

            processed_nodes.append(cn.name)   
        return []
    
class Node:
 
    def __init__(self, info):
        """
        Initialization Method of Node object.

        Keyword Arguments:
            info {dict} -- This Node properties.
        
        """
              
        # Parse input 'info' and initialize object variables

        # ------------------ PHYSICAL STATE ----------------------------------
        self.name = info["_id"]
        self.pop = info["pop"]
        self.links = info["links"]
        self.links_list = list(self.links.values())
        self.neighbors = info["neighbors"]
        self.neighbors_list = list(self.neighbors.values())
        #
        # ---------------------------------------------------------------------

        # --------------------- OPERATIONAL STATE -----------------------------
        #
        self._status = 'on'                 # status: on/off
        self.active_links = self.links.copy()
        self.active_links_list = self.links_list.copy()
        self.active_neighbors = self.neighbors.copy()
        self.active_neighbors_list = self.neighbors_list.copy()
        #
        # ---------------------------------------------------------------------

        # Other properties
        self._role = 'NR'  # default role
        self._info = {}  # initialize self.info

        self.update_info()


    @property
    def status(self):
        return self._status
  
    @status.setter
    def status(self, new_value):
        
        possible_values = ['on', 'off']

        if new_value in possible_values:
            self._status = new_value
            self.update_info()
        else:
            raise Exception("*** {} IS NOT A VALID STATUS! ***".format(new_value))

    @property
    def role(self):
        return self._role
    
    @role.setter
    def role(self, new_value):
        
        possible_values = ['NR', 'ER', 'IR']

        if new_value in possible_values:
            self._role = new_value
            self.update_info()
        else:
            raise Exception("*** {} IS NOT A VALID ROLE! ***".format(new_value))

    def update_info(self):
        """
        Update this node information.
        """

        info = {"_id": self.name,
                "pop": self.pop,
                "links": self.links,
                "links_list": self.links_list,
                "active_links": self.active_links,
                "active_links_list": self.active_links_list,
                "neighbors": self.neighbors,
                "neighbors_list": self.neighbors_list,
                "active_neighbors": self.active_neighbors,
                "active_neighbors_list": self.active_neighbors_list,
                "role": self.role,
                "status": self.status
                }
                
        self.info = info

    def shutdown_link(self, link):
        """
        Shuts down a link of this node.

        Args:
            link (Link): link to be shut down.

        Raises:
            Exception: input 'link' does not belong to this node or it is already shut down.
        """

        # Check if link belongs to this node and it is an active...
        if link.id in self.links_list and link.id in self.active_links_list:
            # ...if so, remove it from active_links_list
            self.active_links_list.remove(link.id)
        else:
            # ...otherwise raise exception.
            raise Exception("*** LINK {} DOES NOT BELONG TO THIS NODE {}, OR IT IS ALREADY SHUT DOWN ***".format(link.name, self.name))
        
        # ------------ UPDATE LINKS -----------------
        # 
        self.active_links = {}  # re-initialize active_links
        i = 1
        
        for act_link in self.active_links_list:
            self.active_links["link{}".format(i)] = act_link
            i+=1
        #
        # -----------------------------------------------

        # ------------ UPDATE NEIGHBORS -----------------
        #
        # Remove neighbor only if this node is link's node1
        if link.node1 == self.name:
            neighbor = link.node2

            self.active_neighbors_list.remove(neighbor)

            self.active_neighbors = {}  # re-initialize active_neighbors
            i = 1

            for act_neighbor in self.active_neighbors_list:
                self.active_neighbors["neighbor{}".format(i)] = act_neighbor
                i+=1
        #
        #-------------------------------------------------

        self.update_info()
   
    def startup_link(self, link):
        """
        Starts up a link of this node.

        Args:
            link (Link): link to be turned on.

        Raises:
            Exception: input 'link' does not belong to this node or it is already turned on.
        """

        # Check if link belongs to this node and it is not active...
        if link.id in self.links_list and link.id not in self.active_links_list:
            # ...if so, add it to active_links_list
            self.active_links_list.append(link.id)
        else:
            # ...otherwise raise exception.
            raise Exception("*** LINK {} DOES NOT BELONG TO THIS NODE {}, OR IT IS ALREADY TURNED ON ***".format(link.name, self.name))
        
        # ------------ UPDATE LINKS -----------------
        #      
        self.active_links = {}  # re-initialize active_links
        i = 1
        
        for act_link in self.active_links_list:
            self.active_links["link{}".format(i)] = act_link
            i+=1
        #
        # -----------------------------------------------

        # ------------ UPDATE NEIGHBORS -----------------
        #
        # Add neighbor only if this node is link's node1
        if link.node1 == self.name:
            neighbor = link.node2

            self.active_neighbors_list.append(neighbor)

            self.active_neighbors = {}  # re-initialize active_neighbors
            i = 1

            for act_neighbor in self.active_neighbors_list:
                self.active_neighbors["neighbor{}".format(i)] = act_neighbor
                i+=1
        #
        #-------------------------------------------------

        self.update_info()


class Link:
    
    def __init__(self, info):
        """
        Initialization Method of Link Object.

        Link is a directed edge, from node1 to node2 vertices.
        (node1) >>>>>>>> link >>>>>>>> (node2)

        Arguments:
            info {dict} -- This Link properties.

        """
        
        # Parse input 'info' and initialize object variables

        # ------------------------- PHYSICAL STATE ----------------------------
        #
        self.node1 = info["node1"]          # first link endpoint
        self.node2 = info["node2"]          # second link endpoint
        self.id = self.node1 + self.node2   # link id
        self.total_bandwidth = info["bw"]   # capacity [Mbps]
        self.len = info["len"]              # length [Km]
        self.latency = info["delay"]        # latency [ms]
        self.jitter = info["jitter"]        # jitter [ms]
        self.loss = info["loss"]            # packet loss [%]
        #
        # ---------------------------------------------------------------------

        # --------------------- OPERATIONAL STATE -----------------------------
        #
        self._status = 'on'                 # status: on/off
        self.consumed_bandwidth = 0.0       # used capacity [Mbps]
        self.bandwidth_usage = 0.0          # used capacity [%]
        self.service_flows = []             # flows coupled to this Link
        self.power_consumption = 0.0        # power consumption [Kwh]
        self.power_consumption_MORA = 0.0   # power consumption [W]
        #
        # ---------------------------------------------------------------------

        # --------------------- HISTORICAL PARAMETER --------------------------
        #
        self.average_link_usage = info["alu"]  # average link usage [Mbps]
        #
        # ---------------------------------------------------------------------

        self.update_info()


    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, new_value):
        
        possible_values = ['on', 'off']

        if new_value in possible_values:
            self._status = new_value
        else:
            raise Exception("*** {} IS NOT A VALID STATUS! ***".format(new_value))
        
        # If this link has just been switched off, erase its operational status
        if self._status == 'off':
            self.consumed_bandwidth = 0.0       
            self.bandwidth_usage = 0.0          
            self.service_flows = []             
            self.power_consumption = 0.0        
            self.power_consumption_MORA = 0.0

        self.update_info()
    
    def update_info(self):
        """
        Update this link information.
        """

        info = {"_id": self.id,
                "node1": self.node1, 
                "node2": self.node2,
                "bw": self.total_bandwidth, 
                "len": self.len,
                "delay": self.latency,
                "jitter": self.jitter,
                "loss": self.loss,
                "status": self.status,
                "bw_usage": self.bandwidth_usage,
                "consumed_bw": self.consumed_bandwidth,
                "service_flows": self.service_flows,
                "power_consumption": self.power_consumption,
                "alu": self.average_link_usage
                }
                
        self.info = info

    def apply_service_on_link(self, service_flow):
        """
        Applies a service flow on this link.

        Args:
            service_flow (dict): service flow to be applied on this link.
        """

        # get service flow id and bandwidth values
        service_flow_id = service_flow["_id"]
        service_flow_bandwidth = service_flow["bandwidth"]

        # apply service flow on this link
        self.service_flows.append(service_flow_id)
        self.consume_bandwidth(service_flow_bandwidth)

        self.update_info()

    def remove_service_from_link(self, service_flow):
        """
        Remove a service flow from this link.

        Args:
            service_flow (dict): service flow to be removed from this link.
        """
       
        # get service flow id and bandwidth values
        service_flow_id = service_flow["_id"]
        service_flow_bandwidth = - service_flow["bandwidth"]

        # remove service flow from this link
        self.service_flows.remove(service_flow_id)
        self.consume_bandwidth(service_flow_bandwidth)
        
        self.update_info()

    def consume_bandwidth(self, required_bandwidth):
        """
        Calculate link consumed bandwidth and power of this link after applying or removing a service flow from it.


        Args:
            required_bandwidth (string): new amount of bandwidth to be consumed or released.
        """
       
        self.consumed_bandwidth = self.consumed_bandwidth + float(required_bandwidth)

        if self.consumed_bandwidth < -1e-3:
            self.consumed_bandwidth = 0.0
            self.bandwidth_usage = 0.0
        elif self.consumed_bandwidth > self.total_bandwidth:
            self.bandwidth_usage = self.consumed_bandwidth/self.total_bandwidth # 1.0
            print("***** LINK {} IS CONGESTED: BANDWIDTH USAGE = {} % *****".format(self.id, (self.consumed_bandwidth/self.total_bandwidth)*100))
        else:
            self.bandwidth_usage = self.consumed_bandwidth/self.total_bandwidth

        # Updating power consumption based on new link occupation
        self.power_consumption_MORA = self.get_power_consumption(self.consumed_bandwidth)
        self.update_info()

    def get_power_consumption(self, x, delta = 180, rho = 5e-4, mu = 1e-03, alpha = 1.4, n_l = 1):
        """
        Calculate actual power consumed by this link.

        See paper IEEE "A Hop-by-Hop Routing Mechanism for Green Internet"

        Args:
            x ([type]): [description]
            delta (int, optional): [description]. Defaults to 180.
            rho ([type], optional): [description]. Defaults to 5e-4.
            mu ([type], optional): [description]. Defaults to 1e-03.
            alpha (float, optional): [description]. Defaults to 1.4.
            n_l (int, optional): [description]. Defaults to 1.

        Returns:
            [float]: power consumed by this link.
        """
        
        # Link energy model used for "hop by hop..." and MORA
        if x <= 0:
            return 0
        else:
            if x > self.total_bandwidth:
                x = self.total_bandwidth
            return 2*n_l*(delta + rho*(x/n_l) + mu * ((x/n_l)**alpha))