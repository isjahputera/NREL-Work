from socket import MsgFlag
from xml.dom.minidom import parseString
from pip import List
from nodescontrollerfolder.nodescontroller import (
    initialize_controller_parameters_nodes, initialize_nodes_conrtol_central,
    initialize_volt_control, run_nodes_central, run_nodes_control,
    run_volt_control)
import mesamodel as gm
# Builtins
import ast
import inspect
import json
import logging
import math
import os
import random
import glob 
import sys
import threading as mt
import time
import pprint

import helics as h
import numpy as np
import opendssdirect as dss
import pandas as pd
from fap import federateagent
from opendssdirect import dss
import datetime 



import datetime
import pytz
from pandas.tseries.offsets import DateOffset


# offset_sfo_july = DateOffset(hours=-7,days=1) # July PDT
# offset_sfo_jan = DateOffset(hours=-8,days=1) # January PST

# pdt_months = [4,5,6,7,8,9,10]
# pst_months = [11,12,1,2,3]


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.realpath(__file__)) 
logdir = "/Users/dvaidhyn/work/fy22/abm/mvpmarch/outputs"
BEHAVIOR_FLAG = 0
timezoneoffset = 7

def process_irridiance(drive_cycle):
    """
    Process irridiance file to return current status from a time series.
    
    """
    starttime = "2013-04-07 10:00:00"
    stoptime = "2013-04-07 12:00:00"
    pv_profile = pd.read_csv(drive_cycle,header=0, index_col=0)
    pv_profile = pv_profile['dni']
    year = pd.to_datetime(starttime).year
    month = pd.to_datetime(starttime).month
    day = pd.to_datetime(starttime).day -1

    pv_profile.index = pd.date_range(start='{}-{}-{} 00:00:00'.format(int(year), int(month), int(day)), \
    end='{}-{}-{} 00:00:00'.format(int(year), int(month), int(day)+1), freq='5T')[:-1]
    # if month in pst_months:
    #     offset_sfo = offset_sfo_jan
    # elif month in pdt_months:
    #     offset_sfo = offset_sfo_july
    offset_sfo_july = DateOffset(hours=0,days=0) # July PDT
    pv_profile.index = [x+offset_sfo_july for x in pv_profile.index.tolist()]
    # pv_profile.index = [x for x in pv_profile.index.tolist()]
    irridiance_profile = pd.DataFrame(pv_profile)
    del(pv_profile)
    irridiance_profile = \
    pd.DataFrame(irridiance_profile.resample('1S').interpolate())
    irridiance_profile.columns = ['irrad']
    pv_profile = (irridiance_profile['irrad'].values*0.1).tolist()
    newprofile =  pv_profile[-6*3600:] +pv_profile [:-6*3600]
    return(newprofile)

def process_loadshape(drive_cycle,ftype=None):
    """
    Process irridiance file to return current status from a time series.
    """
    starttime = "2013-04-07 10:00:00"
    stoptime = "2013-04-07 12:00:00"
    if (ftype):
        pv_profile =  pd.DataFrame(drive_cycle)
    else:
        df = pd.read_csv("data/LoadShape1.CSV",header=None)
        pv_profile = pd.DataFrame(df[0].values[24*30*6: 24*30*6 + 24])
        del(df)
    year = pd.to_datetime(starttime).year
    month = pd.to_datetime(starttime).month
    day = pd.to_datetime(starttime).day -1
    pv_profile.index = pd.date_range(start='{}-{}-{} 00:00:00'.format(int(year), int(month), int(day)), \
    end='{}-{}-{} 00:00:00'.format(int(year), int(month), int(day+1)), freq='1H')[:-1]
    offset_sfo_july = DateOffset(hours=0,days=0) # July PDT
    pv_profile.index = [x+offset_sfo_july for x in pv_profile.index.tolist()]
    # print(pv_profile.index)
    irridiance_profile = pd.DataFrame(pv_profile)
    del(pv_profile)
    irridiance_profile = \
    pd.DataFrame(irridiance_profile.resample('1S').interpolate())
    irridiance_profile.columns = ['load']
    # print(irridiance_profile)
    pv_profile = (irridiance_profile['load'].values).tolist()
    newprofile =  pv_profile[6*3600:] +pv_profile [:6*3600]
    return (newprofile)


fname = "./data/Whole Premise Load Shapes (Day) downloaded on 2022-03-22 10.55.53.csv"

df = pd.read_csv(fname)
df = df.T
js = json.loads(df.to_json())["0"]
hourly = { x:y for x,y in js.items() if "HR" in x}
loads = list(hourly.values())
mc = math.ceil(max(loads))
loads2 = [ x/mc for x in loads]
LDPROFILE =  process_loadshape(drive_cycle=loads2,ftype=True)
# PVFILE = process_irridiance("/Users/dvaidhyn/work/fy22/abm/mvpmarch/data/Solar_data_37.92_-122.29.csv")
PVFILE = process_irridiance("/Users/dvaidhyn/Solar_data_38.22_-122.97.csv")
class powerflow(federateagent):
    """
        Agent to handle poewrflow for the electrical network
    """

    def __init__(self, config_dict):
        super(powerflow, self).__init__(
            name=config_dict['name'], feeder_num=0, starttime=config_dict['starttime'], endtime=config_dict['stoptime'], agent_num=0, config_dict=config_dict)
        self.config_dict = config_dict
        self.initialize_opendss()
        print(" |NITIALIZED OPENDSS PF ", flush=True)
        # self.log_dir = root_dir + "/" + config_dict['logdir']
        self.log_dir =  config_dict['logdir']
        self.soc = []
        ## assume each home is 50kwh behavior_agents
        self.num_homes = len(config_dict['behavior_agents'].keys())
        self.homes = config_dict['behavior_agents']
        self.ldshape = LDPROFILE
        self.house_dict = {}
        self.homewrite = True
        load = self.dss.Loads.First()

        while(load):
            loadname = dss.Loads.Name().lower()
            # houses in current loadname 
            houses =  [x for x,y in self.homes.items() if loadname == y['loadname'].lower()]
            self.house_dict[loadname] = houses
            load = dss.Loads.Next()
            print("HOUSES in powerflow ", loadname, houses)

        # for ii in range(len(config_dict['logdir']num_homes))

    def initialize_opendss(self):
        # masterfile = root_dir + "/" + self.model_parameters['masterfile']
        masterfile = self.model_parameters['masterfile']
        self.dss = dss
        str_cmd = 'Compile {}'.format(masterfile)
        self.dss.run_command(str_cmd)
        logger.debug("OpenDSS Compiled!!! ")
        self.AllNodeNames = self.dss.Circuit.AllNodeNames()
        logger.debug("all node names: {}".format(self.AllNodeNames))

        self.load_pq = {}
        self.load_to_node = {}
        self.node_to_num = {}
        # Obtain load <--> node mapping.
        load = self.dss.Loads.First()
        while load:
            loadname = self.dss.Loads.Name()
            self.load_to_node[loadname] = self.dss.CktElement.BusNames()[
                0].split(".2")[0]
            self.load_pq[loadname] = {'p': 0.0, 'q': 0.0}
            load = self.dss.Loads.Next()
        self.node_to_load = {v: k for k, v in self.load_to_node.items()}

        # number of nodes in the circuit
        self.node_number = len(self.dss.Circuit.AllNodeNames())
        self.NodeNum = self.node_number  # why need to do this?
        YVol = self.dss.Circuit.YNodeVArray()
        # self.control_volt = self.Voltage(YVol)
        self.voltages = self.dss.Circuit.AllBusMagPu()

        for x in self.load_pq.keys():
            self.load_pq[x] = {'p': 0.0, 'q': 0.0}

        # format for opendss powerflow result
        self.return_volt = {'voltage': self.voltages,
                            'Psubk': [0.0, 0.0, 0.0], 'Qsubk': [0.0, 0.0, 0.0]}
        self.aggregator = None
        self.aggregator_dict = {}
        self.current_house = {}

    def process_subscription_event(self, msg):
        """ This must be implemented """
        for x in msg.keys():
            self.current_house = msg[x]['message']

    def process_periodic_publication(self):
        # print("Call opendss ")
        # self.current_house = {'home_0': {'L2': -1, 'PV': -1, 'EV': -1}, 'home_1': {'L1': 1, 'EV': 1, 'PV': 1}, 'home_2': {'L2': -1, 'EV': 0}, 'home_3': {'L1': -1, 'EV': 0}, 'home_4': {'L1': -1, 'EV': -1}, 'home_5': {'L1': -1, 'EV': -1}, 'home_6': {'L1': -1, 'EV': -1}, 'home_7': {'L1': -1}, 'home_8': {'L2': -1}, 'home_9': {'L1': -1}, 'home_10': {'L2': -1}, 'home_11': {'L1': -1, 'L2': -1}, 'home_12': {'L2': -1}, 'home_13': {'L2': -1, 'PV': -1, 'EV': -1}, 'home_14': {'L2': 1, 'EV': 1, 'PV': 1}, 'home_15': {'L2': -1}, 'home_16': {'L1': -1, 'PV': -1, 'EV': -1}, 'home_17': {'L2': 1, 'EV': 1, 'PV': 1}, 'home_18': {'L2': -1, 'EV': 0}, 'home_19': {'L2': -1, 'EV': 0}, 'home_20': {'L1': -1, 'L2': -1, 'EV': 0}, 'home_21': {'L2': -1, 'EV': 0}, 'home_22': {'L2': -1, 'EV': 0}, 'home_23': {'L2': -1, 'EV': 0}, 'home_24': {'L1': -1, 'EV': 0}, 'home_25': {'L2': -1, 'EV': 0}, 'home_26': {'L1': -1, 'EV': -1}, 'home_27': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_28': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_29': {'L2': -1, 'EV': -1}, 'home_30': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_31': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_32': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_33': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_34': {'L1': -1, 'EV': -1}, 'home_35': {'L2': -1, 'EV': -1}, 'home_36': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_37': {'L2': -1, 'EV': -1}, 'home_38': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_39': {'L1': -1, 'EV': -1}, 'home_40': {'L1': -1, 'EV': -1}, 'home_41': {'L1': -1}, 'home_42': {'L2': -1}, 'home_43': {'L2': -1}, 'home_44': {'L1': -1, 'L2': -1}, 'home_45': {'L1': -1, 'L2': -1}, 'home_46': {'L1': -1, 'L2': -1}, 'home_47': {'L2': -1, 'L1': -1}, 'home_48': {'L1': -1}, 'home_49': {'L2': -1}, 'home_50': {'L2': -1}, 'home_51': {'L1': -1, 'L2': -1}, 'home_52': {'L2': -1, 'L1': -1}, 'home_53': {'L2': -1}, 'home_54': {'L1': -1, 'L2': -1}, 'home_55': {'L2': -1, 'L1': -1}, 'home_56': {'L1': -1, 'L2': -1}, 'home_57': {'L2': -1}, 'home_58': {'L1': -1, 'L2': -1}, 'home_59': {'L2': -1}, 'home_60': {'L1': -1}, 'home_61': {'L1': -1}, 'home_62': {'L2': -1}, 'home_63': {'L1': -1, 'L2': -1}, 'home_64': {'L1': -1}, 'home_65': {'L1': -1, 'PV': -1, 'EV': -1}, 'home_66': {'L1': 1, 'L2': 1, 'EV': 1, 'PV': 1}, 'home_67': {'L1': -1, 'EV': 0}, 'home_68': {'L1': -1, 'EV': -1}, 'home_69': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_70': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_71': {'L2': -1}, 'home_72': {'L2': -1}, 'home_73': {'L2': -1}, 'home_74': {'L2': -1}, 'home_75': {'L2': -1, 'L1': -1}, 'home_76': {'L1': -1, 'PV': -1, 'EV': -1}, 'home_77': {'L2': 1, 'L1': 1, 'EV': 1, 'PV': 1}, 'home_78': {'L1': -1}, 'home_79': {'L1': -1, 'L2': -1, 'PV': -1, 'EV': -1}, 'home_80': {'L2': 1, 'L1': 1, 'EV': 1, 'PV': 1}, 'home_81': {'L2': -1, 'L1': -1, 'EV': 0}, 'home_82': {'L2': -1, 'EV': 0}, 'home_83': {'L1': -1, 'EV': 0}, 'home_84': {'L2': -1, 'EV': 0}, 'home_85': {'L1': -1, 'EV': 0}, 'home_86': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_87': {'L2': -1, 'EV': -1}, 'home_88': {'L2': -1, 'EV': -1}, 'home_89': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_90': {'L2': -1, 'EV': -1}, 'home_91': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_92': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_93': {'L1': -1, 'EV': -1}, 'home_94': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_95': {'L1': -1, 'EV': -1}, 'home_96': {'L2': -1}, 'home_97': {'L2': -1}, 'home_98': {'L2': -1}, 'home_99': {'L2': -1}, 'home_100': {'L1': -1}, 'home_101': {'L2': -1}, 'home_102': {'L2': -1, 'L1': -1}, 'home_103': {'L1': -1, 'L2': -1}, 'home_104': {'L2': -1}, 'home_105': {'L1': -1, 'L2': -1}, 'home_106': {'L2': -1}, 'home_107': {'L2': -1}, 'home_108': {'L1': -1}, 'home_109': {'L2': -1, 'L1': -1}, 'home_110': {'L2': -1, 'L1': -1}, 'home_111': {'L1': -1}, 'home_112': {'L2': -1, 'PV': -1, 'EV': -1}, 'home_113': {'L2': 1, 'EV': 1, 'PV': 1}, 'home_114': {'L1': -1, 'EV': 0}, 'home_115': {'L1': -1, 'L2': -1, 'EV': 0}, 'home_116': {'L2': -1, 'L1': -1, 'EV': 0}, 'home_117': {'L1': -1, 'EV': -1}, 'home_118': {'L2': -1, 'EV': -1}, 'home_119': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_120': {'L2': -1, 'EV': -1}, 'home_121': {'L2': -1, 'EV': -1}, 'home_122': {'L1': -1, 'EV': -1}, 'home_123': {'L1': -1, 'L2': -1}, 'home_124': {'L2': -1}, 'home_125': {'L1': -1, 'L2': -1}, 'home_126': {'L1': -1, 'L2': -1}, 'home_127': {'L1': -1, 'L2': -1}, 'home_128': {'L2': -1}, 'home_129': {'L1': -1}, 'home_130': {'L1': -1}, 'home_131': {'L1': -1}, 'home_132': {'L2': -1}, 'home_133': {'L2': -1, 'PV': -1, 'EV': -1}, 'home_134': {'L1': 1, 'EV': 1, 'PV': 1}, 'home_135': {'L2': -1, 'L1': -1, 'EV': 0}, 'home_136': {'L1': -1, 'L2': -1, 'EV': 0}, 'home_137': {'L2': -1, 'EV': 0}, 'home_138': {'L1': -1, 'EV': 0}, 'home_139': {'L1': -1, 'L2': -1, 'EV': 0}, 'home_140': {'L1': -1, 'EV': 0}, 'home_141': {'L2': -1, 'EV': 0}, 'home_142': {'L1': -1, 'EV': 0}, 'home_143': {'L1': -1, 'EV': -1}, 'home_144': {'L2': -1, 'EV': -1}, 'home_145': {'L1': -1, 'EV': -1}, 'home_146': {'L1': -1, 'EV': -1}, 'home_147': {'L1': -1, 'EV': -1}, 'home_148': {'L1': -1, 'EV': -1}, 'home_149': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_150': {'L1': -1, 'EV': -1}, 'home_151': {'L1': -1, 'EV': -1}, 'home_152': {'L1': -1, 'EV': -1}, 'home_153': {'L2': -1, 'EV': -1}, 'home_154': {'L2': -1, 'EV': -1}, 'home_155': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_156': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_157': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_158': {'L2': -1}, 'home_159': {'L2': -1}, 'home_160': {'L1': -1}, 'home_161': {'L2': -1, 'L1': -1}, 'home_162': {'L2': -1}, 'home_163': {'L1': -1}, 'home_164': {'L2': -1}, 'home_165': {'L2': -1, 'L1': -1}, 'home_166': {'L2': -1}, 'home_167': {'L1': -1, 'L2': -1}, 'home_168': {'L1': -1}, 'home_169': {'L2': -1}, 'home_170': {'L2': -1, 'L1': -1}, 'home_171': {'L1': -1, 'L2': -1}, 'home_172': {'L1': -1}, 'home_173': {'L1': -1}, 'home_174': {'L1': -1}, 'home_175': {'L2': -1, 'L1': -1}, 'home_176': {'L2': -1}, 'home_177': {'L1': -1}, 'home_178': {'L2': -1}, 'home_179': {'L1': -1, 'L2': -1}, 'home_180': {'L1': -1}, 'home_181': {'L1': 1, 'L2': 1, 'PV': 1, 'EV': 1}, 'home_182': {'L2': 1, 'L1': 1, 'EV': 1, 'PV': 1}, 'home_183': {'L2': -1, 'EV': 0}, 'home_184': {'L1': -1, 'EV': -1}, 'home_185': {'L1': -1, 'EV': -1}, 'home_186': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_187': {'L2': -1, 'L1': -1}, 'home_188': {'L2': -1, 'L1': -1}, 'home_189': {'L1': -1, 'L2': -1}, 'home_190': {'L1': -1}, 'home_191': {'L1': -1, 'PV': -1, 'EV': -1}, 'home_192': {'L2': 1, 'EV': 1, 'PV': 1}, 'home_193': {'L1': -1, 'EV': 0}, 'home_194': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_195': {'L1': -1, 'L2': -1, 'EV': -1}, 'home_196': {'L2': -1, 'EV': -1}, 'home_197': {'L2': -1}, 'home_198': {'L2': -1, 'L1': -1}, 'home_199': {'L2': -1}, 'home_200': {'L1': -1}, 'home_201': {'L1': -1, 'L2': -1}, 'home_202': {'L1': -1, 'PV': -1, 'EV': -1}, 'home_203': {'L1': 1, 'L2': 1, 'EV': 1, 'PV': 1}, 'home_204': {'L2': -1, 'EV': 0}, 'home_205': {'L2': -1, 'EV': 0}, 'home_206': {'L2': -1, 'EV': 0}, 'home_207': {'L2': -1, 'EV': 0}, 'home_208': {'L1': -1, 'L2': -1, 'EV': 0}, 'home_209': {'L2': -1, 'EV': 0}, 'home_210': {'L2': -1, 'EV': 0}, 'home_211': {'L1': -1, 'EV': 0}, 'home_212': {'L1': -1, 'EV': -1}, 'home_213': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_214': {'L2': -1, 'EV': -1}, 'home_215': {'L1': -1, 'EV': -1}, 'home_216': {'L2': -1, 'EV': -1}, 'home_217': {'L2': -1, 'EV': -1}, 'home_218': {'L1': -1, 'EV': -1}, 'home_219': {'L2': -1, 'EV': -1}, 'home_220': {'L2': -1, 'EV': -1}, 'home_221': {'L2': -1, 'EV': -1}, 'home_222': {'L2': -1, 'EV': -1}, 'home_223': {'L2': -1, 'L1': -1, 'EV': -1}, 'home_224': {'L1': -1, 'EV': -1}, 'home_225': {'L1': -1, 'EV': -1}, 'home_226': {'L2': -1, 'EV': -1}, 'home_227': {'L2': -1, 'L1': -1}, 'home_228': {'L2': -1}, 'home_229': {'L1': -1}, 'home_230': {'L1': -1}, 'home_231': {'L2': -1, 'L1': -1}, 'home_232': {'L1': -1}, 'home_233': {'L1': -1}, 'home_234': {'L2': -1}, 'home_235': {'L2': -1, 'L1': -1}, 'home_236': {'L2': -1}, 'home_237': {'L1': -1, 'L2': -1}, 'home_238': {'L1': -1}, 'home_239': {'L2': -1}, 'home_240': {'L1': -1}, 'home_241': {'L2': -1}, 'home_242': {'L1': -1}, 'home_243': {'L2': -1, 'L1': -1}, 'home_244': {'L2': -1}, 'home_245': {'L2': -1}, 'home_246': {'L1': -1}, 'home_247': {'L2': -1}, 'home_248': {'L1': -1}, 'home_249': {'L2': -1, 'L1': -1}, 'home_250': {'L1': 1, 'PV': 1, 'EV': 1}}        
        if self.aggregator_dict != {}:
            df = pd.DataFrame(list(self.aggregator_dict.values()))
            ddf = df.groupby(['node']).sum()
            loadpq = {}
            for i, x in ddf.iterrows():
                self.load_pq[i.lower()] = {'p': x['p'], 'q': x['q']}
            # print(self.load_pq)
            # print("#######")
            # pprint.pprint(df)
            # print("#######")
            ldshape = self.ldshape[int(self.get_currenttime())]

            with open(f'{logdir}/ldshapes.csv', 'a') as filex:
                filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(ldshape) + os.linesep)    

            if self.current_house != {}:
                dfhouse = pd.DataFrame(list(self.current_house.values()))
                # print(dfhouse)
                # print(dfhouse.columns)
                ddfhouse = dfhouse.groupby(['loadname']).sum()
                # print("SUM of hosues: ", ddfhouse)
                # print(ddfhouse.columns)
                ddfhouse.sort_index(axis=0, inplace=True)
                ddfhouse.sort_index(axis=1, inplace=True)
                if self.homewrite:
                    self.homewrite = False
                    strs = []
                    for i,x in ddfhouse.iterrows():
                        for y in x.keys():
                            strs.append(f"{i}_{y}")
                    aa = [str(xx) for xx in strs]
                    xyz = ",".join(aa)
                    with open('{}/homes.csv'.format(self.log_dir), 'a') as filex:
                        filex.write(str("Timestamp") + ',' + xyz + os.linesep)

                strs = []
                for i,x in ddfhouse.iterrows():
                    for y in x.values:
                        strs.append(y)
                # print(ddfhouse)
                # print(strs)
                # sys.exit(0)
                aa = [str(xx) for xx in strs]
                xyz = ",".join(aa)
                with open('{}/homes.csv'.format(self.log_dir), 'a') as filex:
                    filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset))) + ',' + xyz + os.linesep)

            # strs = []
            # for i,x in ddfhouse.iterrows():
            #     strs.append()
            #     with open(f'{logdir}/homes.csv', 'a') as filex:
            #         filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(ddfhouse) + os.linesep)    


            load = self.dss.Loads.First()
            strs = []
            while(load):
                loadname = dss.Loads.Name()
                default_home_p = ldshape*(len(self.house_dict[loadname.lower()]))
                try:
                    default_home_p += (ddfhouse.loc[loadname]['L1']*0.10  + ddfhouse.loc[loadname]['L2']*.15 )
                except: 
                    pass
                default_home_q = default_home_p*0.80
                # assuming each house is 50kwh
                default_home_p = default_home_p*30.0
                default_home_q = default_home_q*30.0  

                strs.append(default_home_p)   
                strs.append(default_home_q)   

                # print(f" {loadname} : p :{default_home_p} q: {default_home_q} ")                
                nodenum = loadname
                self.dss.Loads.kW(self.load_pq[nodenum]['p'] + default_home_p)
                self.dss.Loads.kvar(self.load_pq[nodenum]['q'] + default_home_q)
                strs.append(default_home_p+ self.load_pq[nodenum]['p'])   
                strs.append(default_home_q+self.load_pq[nodenum]['q'] )  
                load = dss.Loads.Next()

            aa = [str(xx) for xx in strs]
            xyz = ",".join(aa)
            with open('{}/opendssinjection.csv'.format(self.log_dir), 'a') as filex:
                filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset))) + ',' + xyz + os.linesep)


            ## solve powerflow in snapshot mode
            self.dss.run_command('Solve mode=snap')

            # Obtain substation information.
            self.dss.Circuit.SetActiveElement(
                self.dss.Circuit.AllElementNames()[0])
            subPQ_temp = self.dss.CktElement.Powers()
            subPQ_temp = np.array(subPQ_temp)
            subP_3phase = subPQ_temp[0:5:2] * (-1)
            subQ_3phase = subPQ_temp[1:6:2] * (-1)
            self.voltages = self.dss.Circuit.AllBusMagPu()

            YVol = self.dss.Circuit.YNodeVArray()
    #         self.control_volt = self.Voltage(YVol)
            self.return_volt = {'voltage': self.voltages, 'psub': subP_3phase.tolist(), 'qsub': subQ_3phase.tolist()}

            for x in self.pub.keys():
                if 'voltage' in x:
                    # print("Publoished voltage")
                    self.broadcast(self.pub[x], self.return_volt['voltage'])
                    # print("Publoished voltage")
                elif 'psub' in x:
                    self.broadcast(self.pub[x],self.return_volt['psub'])
                    # print("Publoished P---sub")
                elif 'qsub' in x:
                    self.broadcast(self.pub[x],self.return_volt['qsub'])
                    # print("Publoished Q---sub")
                elif 'soc' in x:
                    self.broadcast(self.pub[x], self.soc)

            if self.get_currenttime() > self.starttime:
                if self.log_dir is not None:
                    with open('{}/Psubodss.csv'.format(self.log_dir), 'a') as filex:
                        filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(subP_3phase[0]) + ',' + str(subP_3phase[1]) + ',' + str(
                            subP_3phase[2]) + os.linesep)
                    aa = [str(xx) for xx in self.voltages]
                    xyz = ",".join(aa)
                    with open('{}/Voltageodss.csv'.format(self.log_dir), 'a') as filex:
                        filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset))) + ',' + xyz + os.linesep)
                print(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset))), " Opendss : AVERAGE voltage ", np.mean(
                    self.voltages), " substation :", subP_3phase)
        else:
            pass
            # print(f"Aggregator is empty {self.get_currenttime()}")
            
    def process_periodic_endpoint(self):
        pass

    def process_endpoint_event_old(self, msg):
        """ This must be implemented """
        # print("Endpoint received ", msg)
        for message in msg:
            # if message.time > self.get_currenttime():
            #     ## ignore if value is stale
            #     continue
            # else:
            if True:
                if message.source not in self.aggregator_dict.keys():
                    self.aggregator_dict[message.source] = {
                        'p': 0, 'q': 0, 'node': ""}
                    pqn = ast.literal_eval(message.data)
                    self.aggregator_dict[message.source] = {
                        'p': pqn[1], 'q': pqn[2], 'node': pqn[0]}
                else:
                    # print(message, message.data, type(message), type(message.data), flush=True)
                    pqn = ast.literal_eval(message.data)
                    self.aggregator_dict[message.source] = {
                        'p': pqn[1], 'q': pqn[2], 'node': pqn[0]}

    def process_endpoint_event(self, msg):
        """ This must be implemented """
        # print("Endpoint received ", msg)
        self.soc = {}
        for message in msg:
            # if message.time > self.get_currenttime():
            #     ## ignore if value is stale
            #     continue
            # else:
            # print(" received message in powerflow ", message )
            if True:
                if message.source not in self.aggregator_dict.keys():
                    self.aggregator_dict[message.source] = {
                        'p': 0, 'q': 0, 'node': ""}
                    pqn = ast.literal_eval(message.data)
                    self.aggregator_dict[message.source] = {
                        'p': pqn[1], 'q': pqn[2], 'node': pqn[0]}
                else:
                    # print(message, message.data, type(message), type(message.data), flush=True)
                    pqn = ast.literal_eval(message.data)
                    self.aggregator_dict[message.source] = {
                        'p': pqn[1], 'q': pqn[2], 'node': pqn[0]}
                if len(pqn) == 5:
                    if pqn[4] not in self.soc.keys():
                        self.soc[pqn[4]] = {}
                    if pqn[3] == -1:
                        self.soc[pqn[4]].update({'pv' : pqn[2]})
                    else:
                        self.soc[pqn[4]].update({'ev' : pqn[3]})

class primalupdate(federateagent):
    """
        Agent to handle poewrflow for the electrical network
    """

    def __init__(self, config_dict):
        super(primalupdate, self).__init__(
            name=config_dict['name'], feeder_num=0, starttime=config_dict['starttime'], endtime=config_dict['stoptime'], agent_num=0, config_dict=config_dict)
        self.config_dict = config_dict
        self.vmeas = np.ones(50)
        self.psub = np.ones(3)
        self.qsub = np.ones(3)
        controller_parameters = config_dict['control_parameters']
        initialize_controller_parameters_nodes(self, controller_parameters)
        self.nodes_broadcast = {}
        self.pq = [0.0, 0.0, 0.0]
        self.loadname = self.LoadName
        self.behv_factor = 0.0
        self.control_time = None
        # maxrange = int(gp_config['pmax']/30.0)
        if self.model_type == "EV":
            self.capacity = 100.0 ### Size of car battery in kWh
            self.pmax = 30.0 ### EV charging level
            self.qmax = 0.0
            self.soc = random.randrange(20,30) #### soc of the battery in percentage
            self.ev_arrival=random.randrange(3600*11, 3600*12)
            self.ev_departure=random.randrange(3600*20, 3600*21)
            # self.ev_travelled=random.randrange(10,35)
            self.ev_travelled=10.0
            # random.randrange(10,35)1
            self.travelflag = 1
        if self.model_type == "PV" or self.model_type == "MG":
            self.pv_profile = PVFILE
        self.myhouse = config_dict['house']
        self.DRTSConnect = config_dict.get('DRTSConnect', None)
        self.drtssequence = 0
        

    def process_subscription_event(self, msg):
        """ This must be implemented """
        # if self.get_currenttime() %2 == 0:
        # print("subscribe at primal")
        if True:
            self.nodes_broadcast = {}
            for x in msg.keys():
                name = x.split("feeder_0_")[-1]
                # print(f"{name} value: {msg[x]} , x: {x}")
                if name not in ['service', 'alpha', 'behavior']:
                    self.nodes_broadcast[name] = np.array(msg[x]['message'])
                elif "behavior" in name:
                    self.nodes_broadcast[name] = msg[x]['message']
                else:
                    self.nodes_broadcast[name] = float(msg[x]['message'])

            if "behavior" not in self.nodes_broadcast.keys():
            # if True:
                self.nodes_broadcast["behavior"] = []
        # print("BROADCAST ", self.nodes_broadcast, flush=True)

    def process_endpoint_event(self, msg):
        """ This must be implemented """
        pass
        # print("Endpoint received ", msg)
        # for msgs in msg:
        #     print(msgs.data, msgs.source, msgs.time)

    def process_periodic_publication(self):

        self.nodes_broadcast['alpha'] = 0.1

        if self.model_type == "PV" or self.model_type == "MG":
            self.nodes_broadcast['pav_soc'] = self.pv_profile[int(self.get_currenttime())]
            
        if self.control_time == None or (self.get_currenttime() - self.control_time) == 0:
            diff_time = 1.0
        else:
            diff_time = self.get_currenttime() - self.control_time


        if self.model_type == "EV":
            self.nodes_broadcast["soc"] = self.soc
 

            if self.get_currenttime() > self.ev_arrival and self.get_currenttime() < self.ev_departure: 
                self.ev_available = 1
                if self.soc >= 100.0:
                    self.ev_available = 0
                if self.get_currenttime() >= self.ev_arrival:
                    if self.travelflag:
                        self.soc = self.soc - self.ev_travelled
                        self.travelflag = 0
            

            else:
                self.ev_available = 0
                
            self.nodes_broadcast['ev_available'] = self.ev_available

        self.nodes_broadcast['diff_time'] = diff_time
   
        try:
            self.pq = list(run_nodes_control(
                self, controller_inputs=self.nodes_broadcast))
            if self.model_type == "PV" :
                if self.pq[0] < 0.0:
                    self.pq[0] = 0.0

                # self.pq[0] = 0.0
                # self.pq[1] = 0.0
                with open(f'{logdir}/{self.name}.csv', 'a') as filex:
                    filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(self.pq[0])  + ',' + str(self.pq[1]) + ',' + str(self.pq[2]) + os.linesep)    
            rank = int(self.agent_id)



            if self.nodes_broadcast['behavior'] != 0:
                if self.model_type == "EV":
                    if self.myhouse in self.nodes_broadcast['behavior']: 
                        self.behv_factor = self.nodes_broadcast['behavior'][self.myhouse][self.model_type]
                        print(f"{self.name} , behv {self.behv_factor}")
                        if self.behv_factor > 0 and (self.ev_available and self.soc < 100.0) :
                            self.pq[0] = self.pmax
                        elif self.behv_factor == 0:
                            self.pq[0] = 0.0

            if self.model_type == "EV":
                self.soc = self.soc + ((self.pq[0]/self.pmax)*diff_time/360)       
                with open(f'{logdir}/{self.name}.csv', 'a') as filex:
                    filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(self.pq[0])  + ',' + str(self.pq[1])  + ',' + str(self.soc)+ os.linesep)     
            


        except Exception as e :
            print(f"PRIMAL update failed at {self.get_currenttime()} , {self.name}, {self.model_type} ,  {e}")
        self.control_time = self.get_currenttime()

    def process_periodic_endpoint(self):
        if self.DRTSConnect:
            if self.model_type == "MG": 
                # ['t1', 't2', 'seq', 'UFPLOAD', 'UFQLOAD', 'UFPGEN', 'UFPBAT', 'UFINSOLPV', 'UFPPV', 'UFQPV']
                msg = [ self.pq[0], self.pq[1],0.0,0.0,self.pv_profile[int(self.get_currenttime())], 0.0,0.0]
                for x in self.pub.keys():
                        self.broadcast(self.pub[x], str(msg))
        else:
            if self.model_type == "PV":
                message = str(
                    f"['{self.loadname}',{self.pq[0]*-1.0},{self.pq[1]},{-1},'{self.myhouse}']")
            else:
                # print("EV model")
                message = str(
                    f"['{self.loadname}',{self.pq[0]},{self.pq[1]},{self.soc},'{self.myhouse}']")
            for ends in self.ends.keys():
                h.helicsEndpointSendBytesTo(
                    self.ends[ends], message, "feeder_0_opendss")

class dualupdate(federateagent):
    """
        Agent to handle poewrflow for the electrical network
    """

    def __init__(self, config_dict):
        super(dualupdate, self).__init__(
            name=config_dict['name'], feeder_num=0, starttime=config_dict['starttime'], endtime=config_dict['stoptime'], agent_num=0, config_dict=config_dict)
        self.config_dict = config_dict

        self.psub = np.ones(3)
        self.qsub = np.ones(3)
        controller_parameters = {
            'Vupper': 1.05,
            'Vlower': 0.95,
            "epsilon": 100.0,
            "nu": 0.1,
            "alpha": 1.0,
            "Nodes_monitor_V_index_3": config_dict["Nodes_monitor_V_index_3"]
        }
        NN = config_dict['NN']
        self.vmeas = np.ones(NN)
        self.soc = {}
        self.behv = {}
        initialize_nodes_conrtol_central(self, controller_parameters)
        self.BEHAVIOR_FLAG = config_dict.get('BEHAVIOR_FLAG', None)
        if (self.BEHAVIOR_FLAG):
            self.behavior_agents = config_dict['behavior_agents']
            self.sn = gm.SocialNetwork(num_nodes= len(list(self.behavior_agents.keys())),avg_node_degree=2,behavior_agents=self.behavior_agents)
            # self.sn = gm.SocialNetwork(num_nodes=19,avg_node_degree=2,behavior_agents=self.behavior_agents)

    def process_subscription_event(self, msg):
                """ This must be implemented """
                for x in msg.keys():
                    if "voltage" in x:
                        self.vmeas = msg[x]['message']
                    elif "psub" in x:
                        self.psub = msg[x]['message']
                    elif "qsub" in x:
                        self.qsub = msg[x]['message']
                    elif "soc" in x:
                        self.soc = msg[x]['message']

    def process_endpoint_event(self, msg):
        """ This must be implemented """
        pass
        # print("Endpoint received ", msg)
        # for msgs in msg:
        #     print(msgs.data, msgs.source, msgs.time)

    def process_periodic_publication(self):
        Service = 1
        # if self.get_currenttime() %2 == 0:
        if True:
            run_nodes_central(self, {'alpha': 1.0, 'vmeas': np.array(
                self.vmeas), 'psubk': np.array(self.psub), 'setpoints': [2000.0, 2000.0, 2000.0]})
                # self.vmeas), 'psubk': np.array(self.psub), 'setpoints': [-5000.0, -5000.0, -5000.0]})
                # self.vmeas), 'psubk': np.array(self.psub), 'setpoints': [-2000.0, -2000.0, -2000.0]})
            nodes_broadcast = {'service': Service, 'muk': self.muk, 'lambdak': self.lambdak,
                            'gammauk': self.gammaUk, 'gammalk': self.gammaLk, "behavior": []}
            
            for x in nodes_broadcast.keys():
                pubtopic = [y for y in self.pub.keys() if x in y][0]
                # print("PUB topic ", pubtopic)
                if x == 'service':
                    self.broadcast(self.pub[pubtopic], int(nodes_broadcast[x]))
                # print(f"publlish  {pubtopic} {nodes_broadcast[x]}")
                elif x == "behavior":
                    if (self.BEHAVIOR_FLAG):
                        # if self.get_currenttime() > 100 and self.get_currenttime() < 500:
                        ## Call behavior every 15 minutes. 
                        if (self.get_currenttime() % (60*15)) == 0: 
                                self.sn.soc_dict = self.soc
                                # print("BEHAVIOR INPUT : ", self.soc)
                                temp = self.sn.run_model_mesa(self.num_evs)
                                
                                self.behv = self.sn.behv
                                # print("BAHAVIOR OUTPUT : ",self.behv)
                                self.broadcast(
                                    self.pub[pubtopic], self.behv)
                                
 
                        else:
                            print("No Behavior ", pubtopic, flush=True)
                            self.broadcast(self.pub[pubtopic], self.behv)
                else:
                    self.broadcast(self.pub[pubtopic], nodes_broadcast[x].tolist())      
                # print(f"broadcast topic {pubtopic}, time:{self.get_currenttime()} ")                           
    def process_periodic_endpoint(self):
        pass

def OrchestrateAgent(fname,rank=0):
    f = open(fname, "r")
    js = json.load(f)
    js['agent_id'] = rank
    f.close()
    A = globals()[js['Agent']](js)
    A.run_helics_setup()
    B = inspect.getmembers(A)
    C = [x[0] for x in B]
    function_targets = []
    if "function_targets" in js.keys():
        if len(js["function_targets"]) > 0:
            for y in js["function_targets"]:
                function_targets.append(B[C.index(y)][1])
    A.enter_execution(function_targets=function_targets,
                      function_arguments=[[]])

class SkysparkAgent(federateagent):
    """
        Agent to handle poewrflow for the electrical network
    """

    def __init__(self, config_dict):
        super(SkysparkAgent, self).__init__(
            name=config_dict['name'], feeder_num=0, starttime=config_dict['starttime'], endtime=config_dict['stoptime'], agent_num=0, config_dict=config_dict)
        self.config_dict = config_dict
        
    def process_subscription_event(self, msg):
        pass

    def process_endpoint_event(self, msg):
        pass

    def process_periodic_endpoint(self):
        pass

    def process_periodic_publication(self):
        ## query skyspark for all the keys
        for x in self.pub.keys():
            pubtopic = [y for y in self.pub.keys() if x in y][0]
        # self.broadcast(some topic, query result)  
        # with open(f'{logdir}/{self.name}.csv', 'a') as filex:
        #     filex.write(str(datetime.datetime.fromtimestamp(self.get_currenttime()+(3600*timezoneoffset)))  + ',' + str(self.pq[2]-self.pq[0]) + os.linesep)    


