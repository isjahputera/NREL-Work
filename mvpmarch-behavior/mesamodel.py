
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

# def compute_gini(model): #interesting tidbit I found...inequality index (energy inequality...wut!?)
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
        agent_supply=0.0,
        behavior_agents={}
        # TODO: JEN Could we try to integrate to node-specific electricity/power flow model here?
        #        demand = agent_supply(num_nodes, 1)
    ):

        # these are houses and can have multiple DERs.
        self.num_nodes = num_nodes
        self.behavior_agents = behavior_agents
        prob = avg_node_degree / self.num_nodes
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=prob)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.initial_reaction_size = (
            initial_reaction_size if initial_reaction_size <= num_nodes else num_nodes
        )
        self.info_spread_chance = info_spread_chance
        self.electricity_check_frequency = electricity_check_frequency
# TODO: JEN Could we try to integrate to node-specific electricity/power flow model here?
#        self.demand = demand
        self.soc_dict = {}
        self.datacollector = DataCollector(
            {
                "Uninformed": number_uninformed,
                "Informed": number_informed
            }  # ,
            #agent_reporters={"Demand": "demand"}

        )

        # Create agents
        for i, node in enumerate(self.G.nodes()):
            ders = self.behavior_agents[f"home_{i}"]
            a = ElectricityAgent(
                i,
                self,
                State.UNINFORMED,
                self.info_spread_chance,
                self.electricity_check_frequency,
                agent_supply=agent_supply,
                soc_dict={},
                ders=ders,
                myhouse=f"home_{i}"
            )
            self.schedule.add(a)
            # Add the agent to the node
            self.grid.place_agent(a, node)

        self.datacollector = DataCollector(
            #            model_reporters={"Gini": compute_gini},
            model_reporters={"Total Demand": compute_total_demand},
            agent_reporters={"Demand": "demand"})

        # Inform some nodes
        informed_nodes = self.random.sample(
            self.G.nodes(), self.initial_reaction_size)
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

    def step(self, ):
        # self.datacollector.collect(self)
        # self.grid.
        # self.schedule.step()
        self.schedule.step()
        # ts = self.schedule.step( )
        # collect data

    def run_model_mesa(self, n,):
        tmp = randint(-1,1)
        for a in self.grid.get_cell_list_contents(self.G.nodes()):
            # for i, node in enumerate(self.G.nodes()):
            if a.myhouse in self.soc_dict.keys():
                a.soc_dict = self.soc_dict[a.myhouse]
            else:
                a.soc_dict = {}
            a.coordinate = tmp
        
        for i in range(int(self.num_nodes)):
            
            self.step()
        self.behv = {}
        for a in self.grid.get_cell_list_contents(self.G.nodes()):
            self.behv.update({a.myhouse: a.behv})


class ElectricityAgent(Agent):
    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        info_spread_chance,
        electricity_check_frequency,
        agent_supply,
        soc_dict={},
        ders=None,
        myhouse=None
        #        demand
    ):

        super().__init__(unique_id, model)

        self.state = initial_state

        self.info_spread_chance = info_spread_chance
        self.electricity_check_frequency = electricity_check_frequency
        # 1000 * np.random.randn() #this is random initial demand of each agent
#         self.demand = agent_supply(self.unique_id)
        self.demand = agent_supply
        self.ders = ders
        self.soc_dict = {}
        self.behv = {}
        self.coordinate = 0
        self.myhouse = myhouse
        self.mydecision = {}
        print(f"I am a house with the followng DERS : {self.ders}")
        # I am a house with the followng DERS : {'loadname': 'tr(r:p1udt471-p1udt471lv)', 'ders': ['L1', 'L1', 'PV', 'EV']}

    def try_to_inform_neighbors(self):
        neighbors_nodes = self.model.grid.get_neighbors(
            self.pos, include_center=False)
        uninformed_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if agent.state is State.UNINFORMED
        ]
        for a in uninformed_neighbors:
            if self.random.random() < self.info_spread_chance:
                a.state = State.INFORMED

    def step(self,):
        # print(f"{self.myhouse} = DERS : {self.ders['ders']} , PV or EV : {self.soc_dict}")
        self.behv = {x: 0.0 for x in self.ders['ders']}
        # self.behv = {'L1' : 0.0, 'L2' : 0.0 , 'EV' : 0, 'PV' : 0 }
        # self.soc = {'ev' : 35 , 'pv' : 50}
        
        # if blackout = 0: #if agents are not experiencing a blackout
        if self.state is State.INFORMED:
            self.try_to_inform_neighbors()

            load_behaviors = [-1, 0, 1] #Three choices: -1) use less power, 0) keep using power as normal, 1) enhance power consumption
            load_weights = (5, 15, 80) #probability of a behavior post-event (we assume weights are equal and random prior to an event happening)
            load_choice = choices(load_behaviors, weights=load_weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)

            
            ev_behaviors = [0, 1] #Two choices: 0) turn off charging, 1) turn on charging
            ev_weights = (5, 95) #probability of a behavior post-event (we assume weights are equal and random prior to an event happening)
            soc_thresh = 100

            if 'ev' in self.soc_dict: #if they have an EV
                if self.soc_dict['ev'] < soc_thresh: #and the charge is less than 100%, they are 90% probably going to plug in
                    ev_choice = choices(ev_behaviors, weights=ev_weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
                    self.behv.update({'EV' : ev_choice})
                else: #if charge is greater than 100%, they don't charge
                    self.behv.update({'EV' : 0})

            
            #If they have rooftop solar, and they are producing energy, they can use during an outage
            if 'pv' in self.soc_dict: 
                if self.soc_dict['pv'] > 0.0: 
                    self.behv.update({'L1' : load_choice}) #kept loads at set amounts for now, to make results easier to read (less noise if random probabilistic load increase)
                    self.behv.update({'L2' : load_choice})
                    self.behv.update({'PV' : 1})
            else: #if they don't have PV or PV is not producing
                    self.behv.update({'L1' : load_choice})
                    self.behv.update({'L2' : load_choice})
                    self.behv.update({'PV' : 0})    


        if self.state is State.UNINFORMED:

            load_behaviors = [-1, 0, 1] #Three choices: -1) use less power, 0) keep using power as normal, 1) enhance power consumption
            load_weights = (10, 80, 10) #probability of load change 
            load_choice = choices(load_behaviors, weights=load_weights, k=1)[0] 

            ev_behaviors = [0, 1] #Two choices: 0) turn off charging, 1) turn on charging
            ev_weights_above = (80, 20) #probability charging choices above soc_thresh
            ev_weights_below = (20, 80) #probability charging choices below soc_thresh
            soc_thresh = 70 #threshold at which behavior changes around charging EV
            
            if 'ev' in self.soc_dict: #if they have an EV
                if self.soc_dict['ev'] < soc_thresh: #if soc is less than 70%, they are 80% likely to charge
                    ev_choice = choices(ev_behaviors, weights=ev_weights_below, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
                    self.behv.update({'EV' : ev_choice})
                else: #if soc is greater than 70%, they are 20% likely to charge
                    ev_choice = choices(ev_behaviors, weights=ev_weights_above, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
                    self.behv.update({'EV' : 0})

            if 'pv' in self.soc_dict: 
                if self.soc_dict['pv'] > 0.0: 
                    self.behv.update({'L1' : load_choice}) 
                    self.behv.update({'L2' : load_choice})
                    self.behv.update({'PV' : 1})
            else: #if they don't have PV or PV is not producing
                    load_choice = choices(load_behaviors, weights=load_weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
                    self.behv.update({'L1' : load_choice}) #keeping redundancy here in case having a PV changes choice probabilities
                    self.behv.update({'L2' : load_choice})
                    self.behv.update({'PV' : 0})    
                        
        ## Keep this same. 
        if 'pv' in self.soc_dict:
            self.behv['PV'] = 1
        self.behv.update({'loadname': self.ders['loadname']})

        ## Keep this same. 
        self.mydecision = self.behv
        return {self.myhouse: self.behv}


        # else: #if there is a blackout
            
        #     #we assume they are informed
        #     self.try_to_inform_neighbors()

        #     load_behaviors = [-1, 0, 1] #Three choices: -1) use less power, 0) keep using power as normal, 1) enhance power consumption
        #     load_weights = (5, 15, 80) #probability of a behavior post-event (we assume weights are equal and random prior to an event happening)
            
        #     ev_behaviors = [0, 1] #Two choices: 0) turn off charging, 1) turn on charging
        #     ev_weights = (5, 95) #probability of a behavior post-event (we assume weights are equal and random prior to an event happening)
        #     soc_thresh = 100
            
        #     #If they have PV, and they are producing energy, they can have a load during an outage
        #     if 'pv' in self.soc_dict: 
        #         if self.soc_dict['pv'] > 0.0: 
        #             load_choice = choices(load_behaviors, weights=load_weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
        #             self.behv.update({'L1' : load_choice})
        #             self.behv.update({'L2' : load_choice})
        #             self.behv.update({'PV' : 1})
                    
        #             if 'ev' in self.soc_dict: #if they have an EV
        #                 if self.soc_dict['ev'] < soc_thresh: #and the charge is less than 100%, they are 90% probably going to plug in
        #                     ev_choice = choices(ev_behaviors, weights=ev_weights, k=1)[0] # agents make random choice at every timestep to do nothing differently (0), plug in their EV (1), or unplug (2)
        #                     self.behv.update({'EV' : ev_choice})
        #                 else: #if charge is greater than 100%, they don't charge
        #                     self.behv.update({'EV' : 0})
                    
        #     else: #if they don't have PV or PV is not producing, set all loads to 0
        #             self.behv.update({'L1' : 0}) #how do I decrease loads by 100%?
        #             self.behv.update({'L2' : 0}) #how do I decrease loads by 100%?
        #             self.behv.update({'PV' : 0})
        #             self.behv.update({'EV' : 0})

            # ## Keep this same. 
            # if 'pv' in self.soc_dict:
            #     self.behv['PV'] = 1
            # self.behv.update({'loadname': self.ders['loadname']})
    
            # ## Keep this same. 
            # self.mydecision = self.behv
            # return {self.myhouse: self.behv}

            