from itertools import permutations
import random
import numpy as np
from deap import algorithms, base, creator, tools, algorithms
import json
import collections
from utils.network_objects import *



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

def generate_individual(indi_class, starting_node, ending_node, topology):

    genome = []
    
    starting_node = starting_node
    ending_node = ending_node
    while not genome or genome[-1] != ending_node:
    
        genome = []
        genome.append(starting_node)

        while genome[-1] != ending_node:
            
            # Cerca i collegamenti validi 
            valid_links = topology.get_valid_links(genome[-1])
            # Filter out nodes already in the topology
            valid_links = [x for x in valid_links if x not in genome]
            # If there is no valid link, restart the procedure
            if not valid_links:
                break
            # Scegli a random il next hop
            next_link = np.random.choice(valid_links)

            # Controlla se non stato attraversato, se  valido aggiungilo alla topologia
            if next_link not in genome:
                genome.append(next_link)

    return indi_class(genome)

def mutate_path_faster(individual, topology, indi_class):
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

def mutate_path(individual, topology, indi_class):

    # Starting and ending node cannot mutate
    valid_mutations = []
    mutated_individual = []

    for ind in range(1, len(individual)-1):
        previous_node = individual[ind-1]        
        next_node = individual[ind+1]
        
        # Mutations: flipping (redundant link)
        # Consider every locus, is flipping possible?
        for node in topology.node_names:
            if node != individual[ind]:
                if topology.is_connection_possible(previous_node, node) and \
                    topology.is_connection_possible(node, next_node) and \
                        not topology.has_loops([x if individual.index(x) != ind else node for x in individual]):
                    # Encoding: type of the mutation (str), locus of the mutation(int), value of the mutation (int)
                    mutation = ('flipping', ind, node)
                    valid_mutations.append(mutation)
        
        # Mutation: deletion
        # Deletion check (check if it possible to delete up to two consecutive nodes without invaliding the path)
        for del_seq in range(0, 2):
            # If we are at the end of the path it makes no sense to delete
            if ind+del_seq > len(individual)-2:
                break

            next_x_node = individual[ind+del_seq+1]
            if topology.is_connection_possible(previous_node, next_x_node) and \
                not topology.has_loops(individual[:ind]+individual[ind+del_seq+1:]): # TODO check this
                    # Encoding: type of the mutation (str), prefix boundary (int),  postfix boundary (int)
                    mutation = ('deletion', ind,  ind+del_seq+1)
                    valid_mutations.append(mutation)
            
        # Mutation: insertion
        # Insertion check (check if it possible to insert up to two consecutive nodes without invaliding the path)
        # For every in-between (upper for)
        # For every length of insertion
        for ins_seq in range(1, 3):            
            # Check all possible insertions
            # Combinatorial products of unused nodes
            unused_nodes = [x for x in topology.node_names if x not in individual]
            possible_insertions = permutations(unused_nodes, ins_seq)
            valid_permutations = []
            is_permutation_valid = True
            for perm in possible_insertions:
                if len(perm)>1:
                    for jj in range(len(perm)-1): 
                        if not topology.is_connection_possible(perm[jj], perm[jj+1]):
                            is_permutation_valid = False
                    if is_permutation_valid:
                        valid_permutations.append(perm)    
                else:
                    valid_permutations.append(perm)    


            for ins in valid_permutations:
                if topology.is_connection_possible(ins[0], previous_node) and \
                    topology.is_connection_possible(ins[-1], individual[ind]) and \
                        not topology.has_loops(individual[:individual.index(previous_node)]+ list(ins) +individual[ind:]): # TODO check this
                        # Encoding: type of the mutation (str), prefix boundary (int),  insertion (list)
                        mutation = ('insertion', ind,  list(ins))
                        valid_mutations.append(mutation)

    # Select mutation
    if len(valid_mutations) > 0:
        choice = np.random.choice(len(valid_mutations))
    # Apply mutation
        mutated_individual = individual[:]

        if valid_mutations[choice][0] == 'flipping':
            mutated_individual[valid_mutations[choice][1]] = valid_mutations[choice][2]
        elif valid_mutations[choice][0] == 'deletion':
            del mutated_individual[valid_mutations[choice][1]: valid_mutations[choice][2]]
        elif valid_mutations[choice][0] == 'insertion':
            mutated_individual = individual[:valid_mutations[choice][1]] + valid_mutations[choice][2] + individual[valid_mutations[choice][1]:]

        return indi_class(mutated_individual),
    else:
        return individual,
def get_optimize_route(topology):
    def optimize_route(flow_dic):
        flow_obj = Flow(flow_dic)
        # number of weights in the tuple -> number of objective functions
        creator.create("FitnessMultiObj", base.Fitness, weights=(-1.0, -1.0, -1.0, -1.0,)) 
        creator.create("Individual", list, fitness=creator.FitnessMultiObj)
        toolbox = base.Toolbox()
        toolbox.register("individual", generate_individual, creator.Individual, flow_obj.starting_node, flow_obj.ending_node, topology)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", crossover_one_point, topology=topology, ind_class=creator.Individual, toolbox=toolbox)
        toolbox.register("select", tools.selNSGA2)
        toolbox.register("mutate", mutate_path, topology=topology, indi_class=creator.Individual)
        
        evaluate_individual = get_evaluate_individual(topology, flow_dic)
        toolbox.register("evaluate", evaluate_individual)
        evaluate_SLA = get_evaluate_SLA(flow_obj.SLA, topology, evaluate_individual)
        penalty = get_penalty(flow_obj.SLA, topology, evaluate_individual) 
        toolbox.decorate("evaluate", tools.DeltaPenality(evaluate_SLA, 20.0, penalty))

        pop = toolbox.population(n=50)
        hof = tools.ParetoFront(similar = compare_individuals)
        stats = tools.Statistics(lambda ind: ind.fitness.values)

        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        algorithms.eaSimple(pop, toolbox, cxpb=0.75, mutpb=0.2, ngen=10, stats=stats, halloffame=hof, verbose=False)

        min_attr = 1e15
        
        meta_att = topology.meta_heuristic
        for p in hof:
            evaluation = evaluate_individual(p)
            if evaluation[meta_att] < min_attr:
                meta_best = p
                min_attr = evaluation[meta_att]
        return meta_best
        
    return optimize_route


def get_faster_optimize_route(topology):
    def faster_optimize_route(flow_dic):
        flow_obj = Flow(flow_dic)
        # number of weights in the tuple -> number of objective functions
        creator.create("FitnessMultiObj", base.Fitness, weights=(-1.0, -1.0, -1.0, -1.0,)) 
        creator.create("Individual", list, fitness=creator.FitnessMultiObj)
        toolbox = base.Toolbox()
        toolbox.register("individual", generate_individual, creator.Individual, flow_obj.starting_node, flow_obj.ending_node, topology)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", crossover_one_point, topology=topology, ind_class=creator.Individual, toolbox=toolbox)
        toolbox.register("select", tools.selNSGA2)
        toolbox.register("mutate", mutate_path_faster, topology=topology, indi_class=creator.Individual)
        
        evaluate_individual = get_evaluate_individual(topology, flow_dic)
        toolbox.register("evaluate", evaluate_individual)
        evaluate_SLA = get_evaluate_SLA(flow_obj.SLA, topology, evaluate_individual)
        penalty = get_penalty(flow_obj.SLA, topology, evaluate_individual) 
        toolbox.decorate("evaluate", tools.DeltaPenality(evaluate_SLA, 20.0, penalty))

        pop = toolbox.population(n=25)
        hof = tools.ParetoFront(similar = compare_individuals)
        stats = tools.Statistics(lambda ind: ind.fitness.values)

        stats.register("avg", np.mean, axis=0)
        #stats.register("std", np.std, axis=0)
        #stats.register("min", np.min, axis=0)
        #stats.register("max", np.max, axis=0)

        algorithms.eaSimple(pop, toolbox, cxpb=0.75, mutpb=0.2, ngen=10, stats=stats, halloffame=hof, verbose=False)

        min_attr = 1e15
        
        meta_att = topology.meta_heuristic
        for p in hof:
            evaluation = evaluate_individual(p)
            if evaluation[meta_att] < min_attr:
                meta_best = p
                min_attr = evaluation[meta_att]
        return meta_best
        
    return faster_optimize_route