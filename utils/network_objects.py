import json
import collections
import re
from pathlib import Path

class SLA(object):
    # Object representing the requirement for a flow
    def __init__(self, flow_dict):
        self.bandwidth = flow_dict['bandwidth'] 
        self.latency = flow_dict['latency'] 

         
class Flow(object):
    # Object representing a flow
    def __init__(self, flow_dict):
        
        self.starting_node = flow_dict['node1']
        self.ending_node = flow_dict['node2']
        self.id = flow_dict['_id']
        self.SLA = SLA(flow_dict)