"""
Working copy with cosim
"""

import math
from enum import Enum
import networkx as nx
from random import randint, uniform, choice, choices
import numpy as np

#import mesa.mesa as mesa
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid
#from FakeAES import *

# TODO: add in state around if people are producing distributed power or not
# TODO: add in actions (0 = do nothing, 1 = plug in EV, 2 = 'unplug' or opt in to blackout)

#def compute_gini(model): #interesting tidbit I found...inequality index (energy inequality...wut!?)
#    agent_demand = [agent.demand for agent in model.schedule.agents]
#    x = sorted(agent_demand)
#    N = model.num_nodes
#    B = sum( xi * (N-i) for i,xi in enumerate(x) ) / (N*sum(x))
#    return (1 + (1/N) - 2*B)

def compute_total_demand(model):
    agent_demand = [agent.demand for agent in model.schedule.agents]
    return sum(agent_demand)

class State(Enum):
    UNINFORMED = 0
    INFORMED = 1

def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if a.state is state])


def number_uninformed(model):
    return number_state(model, State.UNINFORMED)


def number_informed(model):
    return number_state(model, State.INFORMED)


class SocialNetwork(Model):
    """A social model with some number of agents"""

    def __init__(
        self,
        num_nodes=10,
        avg_node_degree=3,
        initial_reaction_size=1,
        info_spread_chance=0.4,
        electricity_check_frequency=0.4,
        agent_supply=0.0
        #TODO: JEN Could we try to integrate to node-specific electricity/power flow model here?
#        demand = agent_supply(num_nodes, 1)
    ):

        self.num_nodes = num_nodes
        prob = avg_node_degree / self.num_nodes
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=prob)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.initial_reaction_size = (
            initial_reaction_size if initial_reaction_size <= num_nodes else num_nodes
        )
        self.info_spread_chance = info_spread_chance
        self.electricity_check_frequency = electricity_check_frequency
#TODO: JEN Could we try to integrate to node-specific electricity/power flow model here?
#        self.demand = demand

        self.datacollector = DataCollector(
            {
                "Uninformed": number_uninformed,
                "Informed": number_informed
            }#,
            #agent_reporters={"Demand": "demand"}

        )

        # Create agents
        for i, node in enumerate(self.G.nodes()):
            a = ElectricityAgent(
                i,
                self,
                State.UNINFORMED,
                self.info_spread_chance,
                self.electricity_check_frequency,
#                self.demand
                agent_supply=agent_supply
            )
            self.schedule.add(a)
            # Add the agent to the node
            self.grid.place_agent(a, node)

        self.datacollector = DataCollector(
#            model_reporters={"Gini": compute_gini},
            model_reporters={"Total Demand": compute_total_demand},
            agent_reporters={"Demand": "demand"})

        # Inform some nodes
        informed_nodes = self.random.sample(self.G.nodes(), self.initial_reaction_size)
        for a in self.grid.get_cell_list_contents(informed_nodes):
            a.state = State.INFORMED

        self.running = True
        self.datacollector.collect(self)


    def informed_uninformed_ratio(self):
        try:
            return number_state(self, State.INFORMED) / number_state(
                self, State.UNINFORMED
            )
        except ZeroDivisionError:
            return math.inf


    def step(self,array_agent_demand):
        self.datacollector.collect(self)
        # self.grid.
        # self.schedule.step()
        self.schedule.step(array_agent_demand)
        # collect data

    ## make a call to all cosim agents to get the agent_supply for the given timestep. asp_ts
    def run_model_mesa(self, n, array_agent_demand):
        print("agent_array_demand ", array_agent_demand)
        for i in range(n):
            self.step(array_agent_demand[i])
            # self.step(asp_ts)


class ElectricityAgent(Agent):
    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        info_spread_chance,
        electricity_check_frequency,
        agent_supply
#        demand
        ):

        super().__init__(unique_id, model)

        self.state = initial_state

        self.info_spread_chance = info_spread_chance
        self.electricity_check_frequency = electricity_check_frequency
        #1000 * np.random.randn() #this is random initial demand of each agent
#         self.demand = agent_supply(self.unique_id)
        self.demand = agent_supply
        self.array_agent_demand = 0.0
#        print(self.demand)

    def try_to_inform_neighbors(self):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos, include_center=False)
        uninformed_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if agent.state is State.UNINFORMED
        ]
        for a in uninformed_neighbors:
            if self.random.random() < self.info_spread_chance:
                a.state = State.INFORMED

#    def try_check_situation(self):
#        energy = 1000 * np.random.randn()
#        return energy

    def step(self,array_agent_demand):
        print("Did we call this after schedule.step() ",array_agent_demand)
#TODO: JEN Could we try to integrate to node-specific electricity/power flow model here?
#        demand = agent_supply(self.num_nodes, self.unique_id)
        demand = array_agent_demand

        if self.state is State.UNINFORMED:
            pre_event_choices = randint(0,2) # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)

            #TODO: Make functions out of these choices.

            if self.demand > 0: # if they are contributing power...
                if pre_event_choices == 1: # and made a choice to plug in the EV, then...
                    self.demand -= uniform(300.0, 600.0) # plug in EV, which is assumed to consume 3-6kW
                if pre_event_choices == 2: # to reduce power consumption, then...
                    self.demand += uniform(100.0, 200.0)   # use less, which assumes the house is using 1-2kW

            elif self.demand < 0:                          # if they are drawing power from the grid...
                if pre_event_choices == 1:                           # and made a choice to plug in the EV, then...
                    self.demand -= uniform(300.0, 600.0)     # they can plug in EV, which is assumed to consume 3-6kW
    #Should we pretend this isn't a choice right now, since there is plenty of power for everyone? A la Andrey's confusion/comment?
                elif pre_event_choices == 2:
                    self.demand += uniform(100.0, 200.0) #= 0.0   # disconnect, which assumes the house is using 1-2kW


        if self.state is State.INFORMED:

            self.try_to_inform_neighbors()

            #TODO: Move these to a toggle/slider in visualization, and then input them up top with other slider/initial inputs
            behaviors = [0, 1, 2] #Three choices: 0) keep using power as normal, 1) enhance power consumption (ex: plug in EV (assumption of 3-6kW)), 2) reduce power consumption
            weights = (80, 10, 10) #probability of a behavior post-event (we assume weights are equal and random prior to an event happening)
            post_event_choices = choices(behaviors, weights=weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)

            if self.demand > 0:                            # if they are contributing power...
                if post_event_choices == 1:                           # and made a choice to plug in the EV, then...
                    self.demand -= uniform(300.0, 600.0)    # plug in EV, which is assumed to consume 3-6kW, and plugging in for 500 mins
                elif post_event_choices == 2:                         # to reduce power consumption, then...
                    self.demand += uniform(100.0, 200.0)   # use less, which assumes the house is using 1-2kW, and unplugging for 250 mins

            elif self.demand < 0:                          # if they are drawing power from the grid...
                if post_event_choices == 1:                           # and made a choice to plug in the EV, then...
                    self.demand -= uniform(300.0, 600.0)     # they can plug in EV, which is assumed to consume 3-6kW
    #Let's pretend this isn't a choice right now, since there is plenty of power for everyone
                elif post_event_choices == 2:
                    self.demand += uniform(100.0, 200.0) #= 0.0   # disconnect, which assumes the house is using 1-2kW

#        return demand















