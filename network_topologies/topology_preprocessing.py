# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import json
import os
from geopy.geocoders import Nominatim  # https://github.com/geopy/geopy
from geopy.distance import great_circle
from service_flows.data_processor import get_mean_link_bw
import time

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
        json_path {str} -- relative path of json file to be created/overwritten,
    """

    # Get the complete path
    filepath = os.path.join(json_path, filename)

    # Write data
    with open(filepath + '.json', 'w+') as f:
            json.dump(data, f, sort_keys=True, indent=4)

def preprocess_metadata(topo_name):
    
    current_dir = os.path.dirname(__file__)
    meta_path = os.path.join(current_dir, topo_name, topo_name + '_metadata.json')
    meta = read_from_json(meta_path)
    
    node_dict = meta['nodes']
    link_dict = meta['links']

    print(" *** PREPROCESSING METADATA *** ")
    
    print(" *** ADDING GEO-COORDINATES and LINK LATENCY ***")
    add_geo_coordinates(node_dict)
    calculate_latency(link_dict, node_dict)

    print(" *** SETTING AVERAGE LINK USAGE (ALU) *** ")
    set_average_link_usage(link_dict)

    #calculate_power_consumption(link_dict, node_dict)

    save_topology_info(topo_name, node_dict, link_dict)

def set_average_link_usage(link_dict):

    mean_link_bw = get_mean_link_bw()

    for link in link_dict:
        link_dict[link]["alu"] = 0.0
        for link_bw in mean_link_bw:
            if link_dict[link]["_id"] == link_bw:
                link_dict[link]["alu"] = round(mean_link_bw[link_bw]/1e6,0)

def add_geo_coordinates(node_dict):
    """[summary]
    
    Arguments:
        node_dict {[type]} -- [description]
    """

    geolocator = Nominatim(user_agent='geant')

    for node in node_dict:
        # Extract city and nation values from node. This is where the PoP is.
        city = node_dict[node]['pop']['city']
        nation = node_dict[node]['pop']['nation']
        # Get geographical info on the PoP location.
        location = geolocator.geocode("{}, {}".format(city, nation))
        
        # Set latitude and longitude info for the node.
        node_dict[node]['pop']['latitude'] = location.latitude
        node_dict[node]['pop']['longitude'] = location.longitude
        time.sleep(1)
    
def calculate_latency(link_dict, node_dict):
    """[summary]
    
    Arguments:
        link_dict {[type]} -- [description]
        node_dict {[type]} -- [description]
    """

    for link in link_dict:
        node1 = link_dict[link]['node1']
        node2 = link_dict[link]['node2']
        for node in node_dict:
            if node_dict[node]['_id'] == node1:
                node1_latitude  = node_dict[node]['pop']['latitude']
                node1_longitude  = node_dict[node]['pop']['longitude']
                node1_coordinates = (node1_latitude, node1_longitude)
            elif node_dict[node]['_id'] == node2:
                node2_latitude  = node_dict[node]['pop']['latitude']
                node2_longitude  = node_dict[node]['pop']['longitude']
                node2_coordinates = (node2_latitude, node2_longitude)
        
        distance = great_circle(node1_coordinates, node2_coordinates).kilometers  # Km
        light_speed_in_fiber = 200000.0  # Km/s
        delay = 1000 * (distance/light_speed_in_fiber)  # ms
        delay = round(delay, 1)

        # OUTPUT
        link_dict[link]['delay'] = delay  # ms
        link_dict[link]['len'] = round(distance, 3)  # Km

def calculate_power_consumption(link_dict, node_dict):
    
    for link in link_dict:
        node1 = link_dict[link]['node1']
        node2 = link_dict[link]['node2']
        for node in node_dict:
            if node_dict[node]['_id'] == node1:
                node1_latitude  = node_dict[node]['pop']['latitude']
                node1_longitude  = node_dict[node]['pop']['longitude']
                node1_coordinates = (node1_latitude, node1_longitude)
            elif node_dict[node]['_id'] == node2:
                node2_latitude  = node_dict[node]['pop']['latitude']
                node2_longitude  = node_dict[node]['pop']['longitude']
                node2_coordinates = (node2_latitude, node2_longitude)

        distance = great_circle(node1_coordinates, node2_coordinates).kilometers
        ola_per_link = distance // INTER_OLA_DISTANCE
        link_power_consumption = ola_per_link * OLA_POWER_CONSUMPTION

        # OUTPUT
        link_dict[link]["power_consumption"] = link_power_consumption

def save_topology_info(topo_name, node_dict, link_dict):
    """
    Save topology info.
    
    'node_dict' and 'link_dict' are saved in folder ."self.name"/"self.name"DB/
    respectively in the files nodes.json and links.json.

    """

    # Build up database_path
    current_dir = os.path.dirname(__file__)
    database_folder = topo_name + 'DB'
    database_path = os.path.join(current_dir, topo_name, database_folder)
    
    # If it doesn't exists, create it
    if not os.path.exists(database_path):
        os.mkdir(database_path)

    # Save nodes and links data
    write_to_json(node_dict, 'nodes', database_path)
    write_to_json(link_dict, 'links', database_path)