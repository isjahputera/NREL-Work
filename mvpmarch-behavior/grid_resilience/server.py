#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 13:11:23 2021

@author: cclark2
"""

import math

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import NetworkModule
from mesa.visualization.modules import TextElement
from .model import SocialNetwork, State, number_informed


def network_portrayal(G):
    # The model ensures there is always 1 agent per node

    def node_color(agent):
#        return {State.UNINFORMED: "#FF0000", State.INFORMED: "#008000"}.get(
#            agent.state, "#808080"
        return {State.UNINFORMED: "#FF0000", State.INFORMED: "#008000"}.get(
            agent.state, "#808080"
        )

    def edge_color(agent1, agent2):
#        if State.RESISTANT in (agent1.state, agent2.state):
#            return "#000000"
        return "#e8e8e8"

    def edge_width(agent1, agent2):
#        if State.RESISTANT in (agent1.state, agent2.state):
#            return 3
        return 2

    def get_agents(source, target):
        return G.nodes[source]["agent"][0], G.nodes[target]["agent"][0]

    portrayal = dict()
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": node_color(agents[0]),
            "tooltip": "id: {}<br>state: {}".format(
                agents[0].unique_id, agents[0].state.name
            ),
        }
        for (_, agents) in G.nodes.data("agent")
    ]

    portrayal["edges"] = [
        {
            "source": source,
            "target": target,
            "color": edge_color(*get_agents(source, target)),
            "width": edge_width(*get_agents(source, target)),
        }
        for (source, target) in G.edges
    ]

    return portrayal


network = NetworkModule(network_portrayal, 500, 500, library="d3")
chart = ChartModule(
    [
        {"Label": "Uninformed", "Color": "#FF0000"},
        {"Label": "Informed", "Color": "#008000"},
#        {"Label": "Isolated", "Color": "#808080"},
#
#
#        {"Label": "Infected", "Color": "#FF0000"},
#        {"Label": "Susceptible", "Color": "#008000"},
#        {"Label": "Resistant", "Color": "#808080"},
    ]
)


class MyTextElement(TextElement):
    def render(self, model):
#        ratio = model.resistant_susceptible_ratio()
        ratio = model.informed_uninformed_ratio()
        ratio_text = "&infin;" if ratio is math.inf else "{0:.2f}".format(ratio)
        informed_text = str(number_informed(model))

        return "Informed/Uninformed Ratio: {}<br>Uninformed Remaining: {}".format(
#        return "Resistant/Susceptible Ratio: {}<br>Infected Remaining: {}".format(
            ratio_text, informed_text
        )


model_params = {
    "num_nodes": UserSettableParameter(
        "slider",
        "Number of agents",
        10,
        10,
        100,
        1,
        description="Choose how many agents to include in the model",
    ),
    "avg_node_degree": UserSettableParameter(
        "slider", "Average Node Degree", 3, 3, 8, 1, description="Average Node Degree" #Node Degree"
    ),
    "initial_reaction_size": UserSettableParameter(
        "slider",
        "Initial Reaction Size",
        1,
        1,
        10,
        1,
        description="Initial Reaction Size", #outbreak
    ),
    "info_spread_chance": UserSettableParameter(
        "slider",
        "Information Spread Chance",
        0.4,
        0.0,
        1.0,
        0.1,
        description="Probability that uninformed neighbor will receive information", #be infected",
    ),
    "electricity_check_frequency": UserSettableParameter(
        "slider",
        "Electricity Check Frequency",
        0.4,
        0.0,
        1.0,
        0.1,
        description="Frequency the nodes check their electricity balance",
    ),
#    "recovery_chance": UserSettableParameter(
#        "slider",
#        "Chance Agent will Disconnect their Solar",
#        0.3,
#        0.0,
#        1.0,
#        0.1,
#        description="Probability that the agent will disconnect solar", #the virus will be removed",
#    ),
#    "gain_resistance_chance": UserSettableParameter(
#        "slider",
#        "Chance Agent will Plug in EV",
#        0.5,
#        0.0,
#        1.0,
#        0.1,
#        description="Probability that the agent will plug in EV", #a recovered agent will become "
#       # "resistant to this virus in the future",
#    ),
}

server = ModularServer(
    SocialNetwork, [network, MyTextElement(), chart], "Social Model", model_params
)
server.port = 8521
