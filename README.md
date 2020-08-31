# Multi-Objective Routing Algorithm (MORA)
This repo contains the code for the paper 'Multi-objective optimization-based reliable,energy efficient routing for SDN networks'.
Below are instructions to replicate the experiments described in the paper.
The Results directory contains the csv files obtained during the experiments.

## Instructions
1) Install the prerequisites <br>
<code>pip install -r requirements.txt</code>
2) Clone this repository. <br>
<code>git clone https://github.com/fColangelo/MORA-Multi-Objective-Routing-Algorithm</code>
3) Launch the 'Simulator' notebook
4) Set the routing algorithm (see instructions inside the notebook)
5) Set the traffic generator by specifying the path for the traffic files and the value of traffic boost (see instructions inside the notebook for setting the values, see paper for an explanation of traffic boost)

The code will run in a separate thread, printing results on a file-by-file basis. The simulation is complete when the final iteration is printed. E.g.:
<code>
******* GENERATE_FLOWS -> ITERATION 288 OUT OF 288 *******
++++ BEGINNING OF ITERATION @ 06/21/2020, 18:18:19 ++++

#### NODE FAILURES PHASE... execution time = 5.0067901611328125e-06
#### DISRUPTED FLOWS REROUTING PHASE... execution time = 0.00015687942504882812
#### GENERATE NEW FLOWS PHASE... execution time = 222.01595902442932
++++ END OF ITERATION @ 06/21/2020, 18:22:01 ++++
******* GENERATE_FLOWS -> ITERATION 288 OUT OF 288 ELAPSED TIME = 222.0168719291687 *******
--------------------------------------------------------------------------
</code>
The results of the simulation are logged inside a CSV file, named after the date and time of the simulation start and the chosen routing algorithm. As an example, a simulation starting on 31/08/20, 10:00 with the EAR algorithm would result in a file named "log_2020-08-31 10:00:00_EAR.csv".

## Structure of the code

Most of the core code (i.e. crossover, mutation, optimization and solution evaluation) is contained in the file "routing_algorithms/mora_v2.py". The initialization code (and thus the population generation function) can be found inside the "network_topologies/topology.py" file.
Traffic generation and logging function can be found in the "service_flows/traffic_generator.py"
