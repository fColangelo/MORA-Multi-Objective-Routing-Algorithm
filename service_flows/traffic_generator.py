# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import json
import threading
import time
import os

class TrafficGenerator():

    def __init__(self, interval, topology, path=os.path.dirname(__file__)):
        
        #### CONSTANT PARAMETERS ####
        self.p_part = 0.16
        self.a_part = 0.67
        self.be_part = 1 - (self.p_part + self.a_part)  # 0.17

        #### ATTRIBUTES ####
        self.flows = {}
        self.interval = interval
        self.topo = topology
        self.old_path_archive = []
        self.new_path_archive = []

        #### TRAFFIC MATRICES ####
        self.path = os.path.join(path, 'traffic_matrices')

        # Get Traffic files & sort them
        self.traffic_files = [f for f in os.listdir(self.path)]
        self.traffic_files.sort(key=str.lower)
        
        # Create thread
        thread = threading.Thread(target=self.generate_flows, args=())
        thread.daemon = True
        thread.start()

    def generate_flows(self):
        
        i = 0
        
        while i < len(self.traffic_files):
            
            flows = {}

            f_path = os.path.join(self.path, self.traffic_files[i])
            f = read_from_json(f_path)

            for src in f:
                for dst in f[src]:
                    bw = round(f[src][dst]/1000000,0)  # Get traffic bandwidth from src to dst and convert in Mbps
                    if bw > 0:
                        bw_p = round(self.p_part * bw, 3)  # premium bandwidth
                        bw_a = round(self.a_part * bw, 3)  # assured bandwidth
                        bw_be = round(self.be_part * bw, 3)  # best effort bandwidth
                        flows['{}{}{}'.format(src, dst, 'premium')] = self.get_flow(service_class='premium', bandwidth=bw_p, nodeA=src, nodeB=dst)
                        flows['{}{}{}'.format(src, dst, 'assured')] = self.get_flow(service_class='assured', bandwidth=bw_a, nodeA=src, nodeB=dst)
                        flows['{}{}{}'.format(src, dst, 'besteffort')] = self.get_flow(service_class='besteffort', bandwidth=bw_be, nodeA=src, nodeB=dst)
            self.flows = flows
            i+=1
            self.apply_flows()
            time.sleep(self.interval)

    def get_flow(self, service_class, bandwidth, nodeA, nodeB):
        """[summary]
        
        Arguments:
            service_class {[type]} -- [description]
            bandwidth {[type]} -- [description]
            nodeA {[type]} -- [description]
            nodeB {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        
        flow_id = nodeA + nodeB + service_class
        flow_constraints = self.class_performance_constraints(service_class)

        service_flow = {
            "_id": flow_id,
            "node1": nodeA,
            "node2": nodeB,
            "bandwidth": bandwidth
        }

        service_flow.update(flow_constraints)
        
        return service_flow

    def class_performance_constraints(self, service_class):    
        """[summary]
        
        Arguments:
            service_class {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        
        if service_class == 'premium':
            latency = 150  # ms
            jitter = 0
            loss = 0
        elif service_class == 'assured':
            latency = 400  # ms
            jitter = 0
            loss = 0
        else:
            latency = 300000  # ms --> 5 minutes = infinite time!
            jitter = 0
            loss = 0
        
        performance_constraints = {
            'latency': latency,
            'jitter': jitter,
            'loss': loss
        }

        return performance_constraints

    def apply_flows(self):

        # init constant
        bw_delta_thrs = 100  # Mbps

        #old_flows = self.topo.get_current_flows().copy()
        
        if not self.old_path_archive:

            ## APPLY FLOWS ON NETWORK (THE NETWORK IS EMPTY)
            for _, flow in self.flows.items():
                #node1 = flow["node1"]
                #node2 = flow["node2"]
                #flow_path = self.topo.get_shortest_path(node1, node2)
                flow_path = self.topo.get_path(flow)
                self.new_path_archive.append((flow, flow_path))
                self.topo.apply_service_on_network(flow, flow_path)
        
        else:

            ## APPLY/MODIFY FLOWS ON NETWORK
            # Topology not empty, evaluate if new flows correspond to old flows
            for _, flow in self.flows.items():
                #node1 = flow["node1"]
                #node2 = flow["node2"]
                #flow_path = self.topo.get_path(node1, node2)
                #presence_flag = False
                # Check if flow is currently applied on topology...

                flow_exist = [x for x in self.old_path_archive if x[0]["_id"] == flow["_id"]]

                if flow_exist: 
                    # A flow with the same id exist, check if it's a random fluctuation
                    #presence_flag = True
                    old_entry = flow_exist[0]
                    if abs(old_entry[0]["bandwidth"] - flow["bandwidth"]) > bw_delta_thrs:
                        # It's a new flow, discard the old one and route this one                    
                        self.topo.remove_service_from_network(old_entry[0], old_entry[1])
                        self.old_path_archive.remove()
                        flow_path = self.topo.get_path(flow)
                        self.new_path_archive.append((flow, flow_path))
                        self.topo.apply_service_on_network(flow, flow_path)
                    else:
                        # It's an old flow, remove it from old list, put it into new list                    
                        self.old_path_archive.remove(old_entry)
                        self.new_path_archive.append(old_entry)
                    """
                    for cf in current_flows:
                        if not presence_flag and flow["_id"] == cf["_id"]:
                            # ...if so, set presence_flag and evaluate bandwidth delta 
                            # between this flow and the same flow 'self.interval' seconds ago..
                            presence_flag = True
                            bw_delta = abs(flow["bandwidth"] - cf["bandwidth"])
                            applied_flow = cf
                    

                    if presence_flag:  # presence_flag: TRUE -> flow already applied, FALSE -> vice versa
                        # Check if bandwidth delta is greater than the threshold...
                        if bw_delta > bw_delta_thrs:
                            # ..if so, remove it and apply new flow
                            #flow_path = self.topo.get_shortest_path(node1, node2)
                            flow_path = self.topo.get_path(flow)
                            cf_path = self.topo.get_path(applied_flow["node1"], applied_flow["node2"])
                            self.topo.remove_service_from_network(applied_flow, cf_path)
                            self.topo.apply_service_on_network(flow, flow_path) 
                    """   
                else:  
                    # It's a new flow, route it and log it
                    flow_path = self.topo.get_path(flow)
                    self.new_path_archive.append((flow, flow_path))
                    self.topo.apply_service_on_network(flow, flow_path)

            ## REMOVE TERMINED FLOWS FROM NETWORK

            # Remove all flows that are not alive anymroe
            # All old flows that are not matched in new flows
            # Everything left in old flows
            #flows_ids = [x for x in old_flows if x]
            #for _, flow, in self.flows.items():
            #    flows_ids.append(flow["_id"])
            

            for entry in self.old_path_archive:
                self.topo.remove_service_from_network(entry[0], entry[1])
                """
                if cf["_id"] not in flows_ids:
                    node1 = cf["node1"]
                    node2 = cf["node2"]
                    cf_path = self.topo.get_path(node1, node2)
                    self.topo.remove_service_from_network(cf, cf_path)
                """
        self.old_path_archive = self.new_path_archive
        self.new_path_archive = []


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
