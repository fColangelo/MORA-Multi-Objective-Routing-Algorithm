import json
import collections
import re
from pathlib import Path

class SLA(object):
    
    def __init__(self, flow_dict):
        self.bandwidth = flow_dict['bandwidth'] #int(re.findall(r'\d+', flow_dict['bandwidth'])[0])
        self.latency = flow_dict['latency'] #int(re.findall(r'\d+', flow_dict['delay'])[0])
        self.jitter = flow_dict['jitter'] #int(re.findall(r'\d+', flow_dict['jitter'])[0])


class Link(object):
    
    def __init__(self, link_dict):
        self.total_bandwidth = link_dict['bw'] # Measured in MB # TODO marco controlla
        self.latency = int(re.findall(r'\d+', link_dict['delay'])[0])
        self.jitter = int(re.findall(r'\d+', link_dict['jitter'])[0])
        if link_dict['loss']:
            self.packet_loss = int(re.findall(r'\d+', link_dict['jitter'])[0])
        else:
            self.packet_loss = 0
        if 'cost' in link_dict:
            self.cost = link_dict['cost']
        else:
            self.cost = None
    def __repr__(self):
        s = 'Link bandwidth (MB): {}'.format(self.total_bandwidth)+'\n'+\
            'Latency: {}'.format(self.latency) + '\n' + \
            'Jitter: {}'.format(self.jitter) +  '\n' + \
            'Packet loss: {}'.format(self.packet_loss)
        if self.cost is not None:
            s += '\n' + 'Cost: {}'.format(self.cost)
        return s
            
class Flow(object):
    
    def __init__(self, flow_dict):
        
        self.starting_node = flow_dict['node1']
        self.ending_node = flow_dict['node2']
        self.id = flow_dict['_id']
        #self.type = flow_dict['type']
        #self.priority = flow_dict['priority']
        self.SLA = SLA(flow_dict)