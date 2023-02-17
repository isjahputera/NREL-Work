

import ast
import datetime as dt
import math
import os

import numpy as np
import pandas as pd

import cosim


# def Proj_battery_model(xtd, ytd, Uxpos, Uxneg,  Sx):
def Proj_battery(xtd, ytd, Uxpos, Uxneg,  Sx):

    xt = xtd.real
    yt = ytd.real
    theta = np.arctan2(np.sqrt(Sx**2 - Uxpos**2), Uxpos)
    if math.isnan(theta):
        theta = math.atan(np.inf)
    theta_neg = np.arctan2(np.sqrt(Sx**2 - Uxneg**2), np.abs(Uxneg))
    if math.isnan(theta_neg):
        theta_neg = math.atan(np.inf)
    theta_t = np.arctan2(yt, xt)
    if math.isnan(theta_t):
        theta_t = math.atan(np.inf)
    if xt >= 0:

        if (xt**2 + yt**2 <= Sx**2) and xt <= Uxpos:
            x2 = xt
            y2 = yt

        else:

            if np.abs(theta_t) > theta:
                xx = np.column_stack((xt, yt))*Sx/np.sqrt((xt**2 + yt**2))
                x2 = xx[0, 0]
                y2 = xx[0, 1]
            if np.abs(theta_t) <= theta:

                if np.abs(yt) > np.sqrt(Sx**2 - Uxpos**2):
                    x2 = Uxpos
                    if yt > 0:
                        y2 = np.sqrt(Sx**2 - Uxpos**2)
                    else:
                        y2 = -np.sqrt(Sx**2 - Uxpos**2)
                else:
                    x2 = Uxpos
                    y2 = yt

    if xt < 0:
        if (xt**2 + yt**2 <= Sx**2) and (np.abs(xt) <= np.abs(Uxneg)):
            x2 = xt
            y2 = yt
        else:
            if np.abs(theta_t) > theta_neg:
                xx = np.column_stack((xt, yt))*Sx/np.sqrt((xt**2 + yt**2))
                x2 = xx[0, 0]
                y2 = xx[0, 1]

            if np.abs(theta_t) <= theta_neg:
                if np.abs(yt) > np.sqrt(Sx**2 - Uxneg**2):
                    x2 = Uxneg
                    if yt > 0:
                        y2 = np.sqrt(Sx**2 - Uxneg**2)
                    else:
                        y2 = -np.sqrt(Sx**2 - Uxneg**2)
                else:
                    x2 = Uxneg
                    y2 = yt
    P = x2
    Q = y2
    return [P, Q]


def Proj_inverter(xt, yt, Ux, Sx):
    # print(" INside PV projection ")
    P = 0.000
    Q = 0.000
    xt = xt.real
    yt = yt.real
    theta = np.arctan2(np.sqrt(Sx**2 - Ux**2), Ux)
    theta_t = np.arctan2(yt, xt)

    if (((xt**2 + yt**2) <= (Sx**2)) and (xt <= Ux)):
        x2 = xt
        y2 = yt
    else:
        if np.abs(theta_t) > theta:
            xx = np.column_stack((xt, yt))*Sx/np.sqrt((xt**2 + yt**2))
            x2 = xx[0, 0]
            y2 = xx[0, 1]
        if np.abs(theta_t) <= theta:
            if np.abs(yt) > np.sqrt(Sx**2 - Ux**2):
                x2 = Ux
                y2 = np.sqrt(Sx**2 - Ux**2)
            else:
                x2 = Ux
                y2 = yt

    P = x2
    Q = y2

    return [P, Q]


def initialize_controller_parameters_nodes(obj, controller_parameters):
    # obj.properties = {}
    obj.properties = {}

    # objsbase = sbase['sbase']
    obj.uuid = controller_parameters['uuid']

    obj.slope = -10.0

    obj.properties['Ap'] = np.array(controller_parameters['Ap'])
    obj.properties['Aq'] = np.array(controller_parameters['Aq'])
    obj.properties['Mp'] = np.array(controller_parameters['Mp'])
    obj.properties['Mq'] = np.array(controller_parameters['Mq'])
    obj.properties['costp'] = controller_parameters['costp']
    obj.properties['costq'] = controller_parameters['costq']
    obj.properties['nu'] = controller_parameters['nu']
    obj.properties['capacity'] = controller_parameters['capacity']
    obj.model_type = controller_parameters['model_type']
    obj.soc = controller_parameters.get('soc', 50.0)
    obj.alpha = controller_parameters.get('ahpha', 0.01)
    print("Capacity  ", obj.properties['capacity'])
    obj.setpoints = {
        'P': obj.properties['capacity'],
        'Q': 0.0,
        'Pf': obj.properties['capacity'],
        'Qf': 0.0,
        'P_out': obj.properties['capacity'],
        'Q_out': 0.0,
    }


def run_nodes_control(obj, controller_inputs):
    '''
    Update the P and Q setpoont of 3phase delta connected PV inverters
    inputs:   time, Service,muk,lambdak,gammaUk, gammaLk
    outputs : P and Q of the inverter

    time, Service,muk,lambdak,gammaUk, gammaLk
    '''

    # Service = int(controller_inputs['service'])
    Service = 1.0
    muk = controller_inputs['muk']
    lambdak = controller_inputs['lambdak']
    gammaUk = controller_inputs['gammauk']
    gammaLk = controller_inputs['gammalk']
    
    
    

    # obj.alpha = float(controller_inputs.get('alpha', obj.alpha))
    obj.alpha = 0.1
  
    # float(controller_inputs.get('alpha', obj.alpha))

    if 'pav_soc' in controller_inputs.keys():
        # pav is in percentage so divide by 100 and then multiply by capacity to get overall pu power available
        obj.Pav = float(controller_inputs['pav_soc']) / 100.0 * \
            (obj.properties['capacity'])
    else:
        # Assume full capacity is available for services.
        # pav is in percentage so divide by 100 and then multiply by capacity to get overall pu power available
        obj.Pav = (90.0) / 100.0 * \
            (obj.properties['capacity'])


    if obj.model_type == "PV":
        # print("PV controller")
        dLq_pp = 2*obj.properties['costq']*obj.setpoints['Qf'] + np.dot(obj.properties['Aq'].T, (muk - lambdak)) + Service*np.dot(
            (obj.properties['Mq']).T, (gammaUk - gammaLk)) + obj.properties['nu']*obj.setpoints['Qf']
        uqk = obj.setpoints['Q'] - obj.alpha*dLq_pp
        dLp_pp = 2*obj.properties['costp']*(obj.setpoints['Pf'] - obj.Pav) + np.dot((obj.properties['Ap']).T, (muk - lambdak)) + Service*np.dot(
            (obj.properties['Mp']).T, (gammaUk - gammaLk)) + obj.properties['nu']*obj.setpoints['Pf']
        upk = obj.setpoints['P'] - obj.alpha*dLp_pp

    if obj.model_type == "EV":
        uqk = 0.0
        diff_time = controller_inputs['diff_time']
        alpha = obj.alpha
                        #update P set point
        dLp_pp = 2*obj.properties['costp']*(obj.setpoints['Pf']) + np.dot((obj.properties['Ap']).T,(muk - lambdak) )+ Service*np.dot((obj.properties['Mp']).T,(gammaUk- gammaLk)) + obj.properties['nu']*obj.setpoints['Pf'];
        upk = obj.setpoints['P'] - alpha*dLp_pp;

        soc = controller_inputs['soc']
        ev_available = controller_inputs['ev_available']
        soePU = soc*0.01*obj.properties['capacity']
        socmaxpu = 1.0*obj.properties['capacity']
        min_p_Bat_3d = min(0.0,-(socmaxpu-soePU))/(diff_time);

        # min_p_Bat_3d  = 0
        # max_p_Bat_3d = -max(upk,obj.properties['capacity'])
        
        min_p_Bat_3d = -min(-min_p_Bat_3d,obj.properties['capacity'])
        max_p_Bat_3d = 0.0

    if obj.model_type == "PV":
        maxpv = min(float(obj.Pav),float(obj.properties['capacity']))
        [P, Q] = Proj_inverter(
            # upk, uqk, obj.Pav, obj.Pav,obj.properties['capacity'])
            upk, uqk, maxpv, obj.Pav)
        # [P,Q] = Proj_battery(upk, uqk, max_p_Bat_3d, min_p_Bat_3d, max_p_Bat_3d);
        try:
            P = P[0]
        except:
            pass
        try:
            Q = Q[0]
        except:
            pass
        # print("PV active power ",P,Q)
    elif obj.model_type == "EV":

        [P, Q] = Proj_battery(
            upk, uqk, max_p_Bat_3d, min_p_Bat_3d, obj.pmax)
            # upk, uqk,  min_p_Bat_3d,max_p_Bat_3d, obj.properties['capacity'])
        try:
            P = P[0]
        except:
            pass
        try:
            Q = Q[0]
        except:
            pass
        # print("P value for load ", P ,obj.properties['capacity'] )
        if P < 0.0:
            P = P*-1.0
        if P < obj.properties['capacity']: 
            P = obj.properties['capacity']
        if ev_available == 0:
            P = 0.0
            Q = 0.0


    else:
        # print("Sometype of DER ",obj.model_type , flush=True)
        [P,Q] = [0.0,0.0]


    obj.setpoints = {
        'P': P,
        'Q': Q,
        'Pf': P,
        'Qf': Q,
        'P_out': P,
        'Q_out': Q,
    }
    obj.Pset = P
    obj.Qset = Q

    # print('PQ for Inverter', obj.setpoints,
    # " Pav ", str(obj.Pav),  flush=True)
    return(obj.Pset, obj.Qset, obj.Pav)


def initialize_nodes_conrtol_central(obj, controller_parameters):
    obj.nodes_central_params = {}
    obj.nodes_central_params['Vmax'] = 0
    obj.nodes_central_params['Vmin'] = 0
    obj.nodes_central_params['epsilon'] = 0
    # obj.nodes_central_params['']=0
    # obj.nodes_central_params['']=0
    # obj.nodes_central_params['']=0
    obj.properties = {}

    # objsbase = controller_parameters['sbase']
    obj.properties['nu'] = np.array(controller_parameters['nu'])
    obj.alpha = controller_parameters.get('ahpha', 0.01)
    obj.Nodes_monitor_V_index_3 = controller_parameters['Nodes_monitor_V_index_3']
    obj.muk = np.zeros((len(obj.Nodes_monitor_V_index_3)), dtype=float)
    obj.lambdak = np.zeros((len(obj.Nodes_monitor_V_index_3)), dtype=float)
    obj.gammaUk = np.zeros((3), dtype=float)
    obj.gammaLk = np.zeros((3), dtype=float)


def run_nodes_central(obj, controller_inputs):

    obj.nodes_central_params['alpha'] = controller_inputs.get(
        'ahpha', 0.01)
    obj.nodes_central_params['alpha'] = 0.01
    # vmeas=controller_inputs['vmeas'][obj.Nodes_monitor_V_index_3.tolist()]
    vmeas = controller_inputs['vmeas'][obj.Nodes_monitor_V_index_3]

    uni = np.ones(len(obj.Nodes_monitor_V_index_3))
    psubk = controller_inputs['psubk']
    setpoints = controller_inputs['setpoints']
    set_sub_low = np.array(setpoints)
    set_sub_up = np.array(setpoints)
    Service = 1
    lk = obj.lambdak + obj.nodes_central_params['alpha']*(uni.flatten(
    )*obj.nodes_central_params['Vmin'] - vmeas - obj.nodes_central_params['epsilon']*obj.lambdak)
    obj.lambdak = np.maximum(0, lk)
    mk = obj.muk + obj.nodes_central_params['alpha']*(vmeas - uni.flatten(
    )*obj.nodes_central_params['Vmax'] - obj.nodes_central_params['epsilon']*obj.muk)
    obj.muk = np.maximum(0, mk)
    # set_sub_low = np.array([400.0, 400.0, 400.0])
    # set_sub_up = np.array([400.0, 400.0, 400.0])
    if Service == 1:
        lk = obj.gammaUk + obj.nodes_central_params['alpha'] * \
            (np.array(psubk) - set_sub_up -
                obj.nodes_central_params['epsilon']*obj.gammaUk)
        obj.gammaUk = np.maximum(0, lk)
        lk = obj.gammaLk + obj.nodes_central_params['alpha'] * \
            (set_sub_low - np.array(psubk) -
                obj.nodes_central_params['epsilon']*obj.gammaLk)
        obj.gammaLk = np.maximum(0, lk)
        # print(f"gammuk {obj.gammaUk}  gammalk  {obj.gammaLk} setpoint {setpoints} psub {psubk}")


def initialize_volt_control(obj, controller_parameters):
    obj.volt_control_params = {}
    obj.volt_control_params['Vmax'] = controller_parameters['Vupper']
    obj.volt_control_params['Vmin'] = controller_parameters['Vlower']
    obj.volt_control_params['volt_index'] = controller_parameters['volt_index']
    obj.properties = {}
#     obj.properties['step'] = np.array(controller_parameters['step'])
    obj.pfactor = 1.0
    obj.qfactor = 1.0
    obj.Pset = 0.0
    obj.Qset = 0.0
    obj.properties['capacity'] = controller_parameters['capacity']
    obj.model_type = controller_parameters['model_type']


def run_volt_control(obj, controller_inputs):
    vmeas = controller_inputs['vmeas'][obj.volt_control_params['volt_index']]
    obj.Pset = (controller_inputs['der_available'] /
                100.0) * obj.properties['capacity']*1000.0
    obj.Qset = obj.Pset*0.85
    if vmeas < obj.volt_control_params['Vmin']:
        obj.pfactor = obj.pfactor + obj.pfactor/2.0
    if vmeas > obj.volt_control_params['Vmax']:
        obj.pfactor = obj.pfactor/2.0
    if vmeas < obj.volt_control_params['Vmin']:
        obj.qfactor = obj.qfactor/2.0 - obj.qfactor
    if vmeas > obj.volt_control_params['Vmax']:
        obj.qfactor = obj.qfactor/2.0
    obj.Pset = obj.Pset*obj.pfactor
    obj.Qset = obj.Qset*obj.qfactor
    return(obj.Pset, obj.Qset, (controller_inputs['der_available'] / 100.0) * obj.properties['capacity']*1000.0)
