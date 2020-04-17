from itertools import permutations
import random
import numpy as np
from deap import algorithms, base, creator, tools, algorithms
import json
import collections
from utils.network_objects import Flow



def eval_bandwidth_single_link(percentage):
    if percentage > 0.6:
        return 6.25*(percentage**2) - 7.5 *(percentage) + 2.25
    elif percentage < 0.6:
        return 0
    
def get_evaluate_individual(topology, flow):
    def evaluate_individual(individual):
        latency = 0
        power = 0
        reliability = []
        for idx in range(len(individual)-1):
            # TODO consider multiple links
            link = topology.get_link_between_neighbors(individual[idx], individual[idx+1])
            latency +=  link.latency 
            power += (link.get_power_consumption(link.consumed_bandwidth+ flow['bandwidth'])-link.power_consumption_MORA) 
            reliability.append(eval_bandwidth_single_link((link.consumed_bandwidth+ flow['bandwidth'])/link.total_bandwidth))
        return len(individual), latency, power, max(reliability)
    return evaluate_individual

def get_evaluate_SLA(SLA_terms, topology, evaluate_individual):
    def evaluate_SLA(individual):
        evaluation = evaluate_individual(individual)
        if evaluation[0] > SLA_terms.latency:
            return False
        return True
    return evaluate_SLA

def get_penalty(SLA_terms, topology, evaluate_individual):
    def penalty(individual):
        evaluation = evaluate_individual(individual)
        p1 = (evaluation[0] - SLA_terms.latency )**2
        #p2 = (evaluation[1] - SLA_terms.jitter)**3
        #p3 = ((evaluation[3] - 0.8)*10)**2
        return p1#+p2+p3)
    return penalty

def compare_individuals(indi1, indi2):
    return indi1 == indi2

def crossover_one_point(parent_1, parent_2, topology, ind_class, toolbox):
    connection_loci = []
    # Do not consider the last two 
    # The last is the final host
    # the other is needed to give space for parent_2 material)
    # The first one must not be skipped: beside the trivial locus [0,0] 
    # there could be connections to other points in parent2
    for ind_p1 in range(len(parent_1)-2):    
        valid_links_P1 = topology.get_valid_links(parent_1[ind_p1])
        # These nodes are already used
        used_nodes_P1_p1 = parent_1[:(ind_p1+1)] # Notation: P -> parent; p -> part
        used_nodes_P1_p2 = parent_1[(ind_p1+1):]
        # Filter valid links to avoid going backward
        valid_links_P1 = [x for x in valid_links_P1 if x not in used_nodes_P1_p1]
        # TODO -1 o -2?
        for ind_p2 in range(1, len(parent_2)-1):
            # These nodes are already used, we must check that parent1 does not contain any of these
            used_nodes_P2_p1 = parent_2[ind_p2:]
            used_nodes_P2_p2 = parent_2[:ind_p2]
            # Check if there is any common node between the parent_1 and parent_2 genome
            common_nodes_P1_P2 = [x for x in used_nodes_P1_p1 if x in used_nodes_P2_p2]
            common_nodes_P2_P1 = [x for x in used_nodes_P2_p1 if x in used_nodes_P1_p2]
            # If there are common nodes, no crossover can be made at these loci
            if common_nodes_P1_P2 or common_nodes_P2_P1:
                continue
            else:
                # If there are no common nodes, check if the two genomes can be connected
                is_compatible = parent_2[ind_p2] in valid_links_P1 
                if is_compatible:
                    # The two genomes cannot be connected at this locus
                    connection_loci.append((ind_p1, ind_p2))

    # If no compatible merging point has been found, output the two parents
    if not connection_loci:
        return parent_1, parent_2
    else:
        # Choose a random locus
        locus = connection_loci[np.random.choice(len(connection_loci))]
        # Create children (necessary for DEAP)
        child1, child2 = [toolbox.clone(ind) for ind in (parent_1, parent_2)] 

        child1 = child1[:locus[0]+1]
        child1.extend((parent_2[locus[1]:]))
        child1 =ind_class(child1)

        child2 = child2[:locus[1]]
        child2.extend((parent_1[locus[0]+1:]))
        child2 = ind_class(child2)

        return (child1, child2)


def mutate_path(individual, topology, indi_class):
    possible_mutations = []
    # Resample until we have at least one valid mutation
    # Select the mutation locus at random, excluding first and last node
    if len(individual) >= 4:
        mutandis_idx = np.random.choice(range(1,len(individual)-2))
        max_hop = 3
        search_len = min(max_hop, (len(individual)-1)-mutandis_idx)
        possible_mutations = []
        for idx in range(1, search_len+1):
            pts = [x[2] for x in topology.mutation_support if x[0] == individual[mutandis_idx] and x[1] ==individual [mutandis_idx+idx]]
            if pts:
                selected = pts[0][np.random.choice(range(len(pts[0])))]
                possible_mutations.append((individual[mutandis_idx], individual[mutandis_idx+idx], selected))

    if possible_mutations:
        mutation = possible_mutations[np.random.choice(range(len(possible_mutations)))]
        mutated_individual = individual[:individual.index(mutation[0])]
        mutated_individual.extend(mutation[2])
        mutated_individual.extend(individual[individual.index(mutation[1])+1:])

        return indi_class(mutated_individual),
    else:
        return individual,

def initPopulation(node1, node2, topology):
    pts = fetch_paths(node1, node2, topology)   
    if pts:
        return pts[0]
    else:
        return []

def fetch_paths(node1, node2, pt_list):
    pts = [x[2] for x in pt_list \
        if (x[1]==node1 and x[2]==node2) or (x[1]==node2 and x[2]==node1)]
    return pts

def get_optimize_route(topology, toolbox):
    def optimize_route(flow_dic):
        
        flow_obj = Flow(flow_dic)        
        evaluate_individual = get_evaluate_individual(topology, flow_dic)
        evaluate_SLA = get_evaluate_SLA(flow_obj.SLA, topology, evaluate_individual)
        penalty = get_penalty(flow_obj.SLA, topology, evaluate_individual) 
        topology.toolbox.register("evaluate", evaluate_individual)
        topology.toolbox.decorate("evaluate", tools.DeltaPenality(evaluate_SLA, 20.0, penalty))
        topology.toolbox.register("population_fetch", initPopulation, list, \
            creator.Individual, flow_obj.starting_node, flow_obj.ending_node, topology)
        pop = topology.toolbox.population_fetch()
        
        hof = tools.ParetoFront(similar = compare_individuals)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        algorithms.eaSimple(pop, topology.toolbox, cxpb=0.75, mutpb=0.2, ngen=10, stats=stats, halloffame=hof, verbose=False)

        min_attr = 1e15 
        meta_att = topology.meta_heuristic
        for p in hof:
            evaluation = evaluate_individual(p)
            if evaluation[meta_att] < min_attr:
                meta_best = p
                min_attr = evaluation[meta_att]

        topology.toolbox.unregister("evaluate")
        topology.toolbox.unregister("population_fetch")

        return meta_best
        
    return optimize_route