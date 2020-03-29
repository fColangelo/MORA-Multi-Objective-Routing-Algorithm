# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import os
import numpy as np
from network_topologies.geant import Geant
from routing_algorithms.dijkstra import dijkstra
from routing_algorithms.dijkstra import calculate_path
from routing_algorithms.dijkstra import set_spt
import csv
import json
from scipy.optimize import nnls

THIS_FILE_PATH = os.path.dirname(__file__)
TRAFFIC_MATRICES_PATH = os.path.join(THIS_FILE_PATH, 'service_flows', 'traffic_matrices')
if not os.path.exists(TRAFFIC_MATRICES_PATH):
    os.makedirs(TRAFFIC_MATRICES_PATH, exist_ok=True)
DATASET_PATH = os.path.join(THIS_FILE_PATH, 'service_flows', 'dataset_geant')

def main():

    # ****** TIME SETUP ******
    timeline = get_timeline()
    START = 0
    STOP = len(timeline)


    # ****** TOPOLOGY SETUP ******
    topo = Geant()
    set_spt(topo)

    # Preliminary Definitions
    directed_links = topo.link_names
    traffic_directions = generate_traffic_directions(topo.node_names)

    # Linear System Components
    # A x = b
    # where
    # A  is a binary coefficient_matrix
    # x  is the vector of the unknowns --> the i-th element of x represents network traffic (bit per second)
    #                                       originated and terminated in two network nodes
    # b  is the vector of the known terms --> the j-th element of b is the network traffic coupled on a network link
    #                                           in a specific link direction
    # Constrained Optimization: Karush-Kuhn-Tucker Theorem (generalization of Lagrange Multiplier Method)
    # -----> min_x (|A x - b|) with x >= 0

    coefficient_matrix = generate_coefficient_matrix(directed_links, traffic_directions, topo)  # A
    A = np.array(coefficient_matrix)

    for t in range(START, STOP):
        constants = get_link_throughputs(directed_links, t)  # b
        b = [elem[0] for elem in constants]  # b
        solution, _ = nnls(A, b)  # x
        post_process_solution(solution)  # x
        
        mae = round(np.mean(abs(b-A.dot(solution)))/1000000,3)  # Mean Absolute Error expressed in Mbps
        print(" {} --> MAE: {} ".format(timeline[t], mae))

        # Reorder data and write on json file (for every 
        # t value)
        traffic_matrix_data = generate_traffic_matrix_data(solution, traffic_directions)
        filename = '{}_traffic_matrices'.format(timeline[t])
        write_to_json(traffic_matrix_data, filename, TRAFFIC_MATRICES_PATH)


def get_timeline():
    """
    This function returns the timeline, i.e. time axis data.

    Returns:
        [List] -- time axis data.
    """

    # init timeline
    timeline = []

    # Import one file @ DATASET_PATH (the "anchor_file") 
    files = os.listdir(DATASET_PATH)
    time_anchor_file_name = files[0]
    time_anchor_path = os.path.join(DATASET_PATH, time_anchor_file_name)
    time_anchor_data = import_csv(time_anchor_path)
    
    # Extract time sampling instants to build timeline
    for i in range(1,len(time_anchor_data)):  # ..skip first row (header)
         timeline.append(time_anchor_data[i][0])
    
    return timeline  

def generate_traffic_directions(nodes):
    """
    This function returns all possible traffic directions on the network topology.
    
    If the network is made up of only three nodes (e.g. A, B and C), the possible traffic directions are: AB, AC, BA, BC, CA, CB.
    If the number of nodes is N, the number of traffic directions is N*(N-1).

    Arguments:
        nodes {List} -- List of topology node names.
    
    Returns:
        [List] -- List of possible traffic directions.
    """

    # init traffic_directions
    traffic_directions = []
    
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i != j:
                direction = nodes[i] + nodes[j]
                traffic_directions.append(direction)
    
    return traffic_directions

def generate_coefficient_matrix(rows, columns, topo):

    # init variables
    row_len = len(rows)
    col_len = len(columns)

    # init coefficient matrix
    coefficient_matrix = np.zeros((row_len, col_len))


    for j in range(len(columns)):
        col = j
        service_name = columns[j]
        node_name = service_name[:len(service_name)//2]
        node_obj = topo.get_one_node(node_name)
        node_spt = node_obj.spt
        if service_name in node_spt.keys():
            service_path = node_spt[service_name]

            for i in range(len(service_path)-1):
                link = service_path[i] + service_path[i+1]
                row = rows.index(link)
                coefficient_matrix[row][col] = 1
    
    return coefficient_matrix

def get_link_throughputs(links, t):
    """
    This functions returns the vector of current topology links throughput (bps).

    Arguments:
        links {List} -- List of topology link names.
        t {int} -- Time index.
    
    Returns:
        [List] -- Vector of current topology links throughputs.
    """

    # init link_throughputs
    link_throughputs = np.zeros((len(links),1))

    link_ids = {
        "BENL": "ams-bru",
        "DENL": "ams-fra",
        "DUNL": "ams-ham",
        "NLUK": "ams-lon",
        "GCGR": "ath-ath2",
        "GRIT": "ath-mil",
        "ATGC": "ath2-vie",
        "HUSK": "bra-bud",
        "ATSK": "bra-vie",
        "BEUK": "bru-lon",
        "HURO": "buc-bud",
        "BGRO": "buc-sof",
        "HUSI": "bud-lju",
        "CZHU": "bud-pra",
        "ATHU": "bud-vie",
        "HRHU": "bud-zag",
        "IEIR": "dub-dub",
        "IEUK": "dub-lon",
        "IRUI": "dub2-lon2",
        "CHDE": "FRA-GEN",
        "DEDU": "fra-ham",
        "DEPL": "fra-poz",
        "CZDE": "FRA-PRA",
        "CHES": "gen-mad",
        "CHFN": "gen-mar",
        "CHIT": "GEN-MIL2",
        "CHFR": "GEN-PAR",
        "DUEE": "ham-tal",
        "LNLT": "kau-kau",
        "LTPL": "kau-poz",
        "LNLV": "kau-rig",
        "PRPT": "lis-lis",
        "PTUK": "lis-lon",
        "ESPR": "lis-mad",
        "ITSI": "LJU-MIL2",
        "UIUK": "lon-lon2",
        "FRUI": "lon2-par",
        "ESFR": "mad-par",
        "ITFN": "mar-mil2",
        "ATIT": "MIL2-VIE",
        "ATPL": "poz-vie",
        "ATCZ": "PRA-VIE",
        "ETLV": "rig-tal",
        "ATBG": "sof-vie",
        "EEET": "tal-tal",
        "ATHR": "vie-zag"
    }

    # DATASET FILES
    files = os.listdir(DATASET_PATH)

    for link in link_ids:
        link_id = link_ids[link]
        for f in files:
            if link_id in f:
                # Import Data
                csvfile = os.path.join(DATASET_PATH, f)
                csvdata = import_csv(csvfile)

                # Find link directions
                if csvdata[0][1] == '{}'.format(link_id):
                    straight_col = 1
                    reverse_col = 3
                else:
                    straight_col = 3
                    reverse_col = 1
                
                # Remove header
                csvdata.pop(0)

                # Get link directions data
                straight_data = csvdata[t][straight_col]  
                reverse_data = csvdata[t][reverse_col]

                # Fill link_throughputs
                straight_link_index = links.index(link)
                knil = link[len(link)//2:] + link[:len(link)//2]
                reverse_link_index = links.index(knil)
                link_throughputs[straight_link_index][0] = straight_data
                link_throughputs[reverse_link_index][0] = reverse_data

    return link_throughputs

def import_csv(csvfilename):
    data = []
    with open(csvfilename, "r", encoding="utf-8", errors="ignore") as scraped:
        reader = csv.reader(scraped, delimiter=',')
        for row in reader:
            if row:  # avoid blank lines
                data.append(row)
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

def post_process_solution(solution):

    for i in range(len(solution)):
        
        if solution[i] < 1:
            solution[i] = 0
        
        solution[i] = round(solution[i],0)

def generate_traffic_matrix_data(traffic_data, traffic_directions):
    
    traffic_matrix_data = {}

    road = traffic_directions[0]
    nodeA_name = road[:len(road)//2]
    nodeB_name = road[len(road)//2:]
    traffic_matrix_data[nodeA_name] = {nodeB_name : traffic_data[0]}

    for i in range(1,len(traffic_directions)):
        
        road = traffic_directions[i]
        nodeA_name = road[:len(road)//2]
        nodeB_name = road[len(road)//2:]

        prev_road = traffic_directions[i-1]
        prev_nodeA_name = prev_road[:len(prev_road)//2]
        
        if nodeA_name != prev_nodeA_name:
            traffic_matrix_data[nodeA_name] = {}
        
        traffic_matrix_data[nodeA_name].update({nodeB_name : traffic_data[i]})
    
    return traffic_matrix_data


if __name__ == "__main__":
    main()