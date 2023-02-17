import cmath
import math

import dss
import numpy as np
import scipy.linalg as linalg
import opendssdirect as dss
from numpy.linalg import inv


def magnitudeDerivative(V, derivVWye, derivVDelta):
    derivMagWye = np.matmul(
        np.diag(1/abs(V)), (np.matmul(np.diag(V.conjugate()),        derivVWye)).real)
    derivMagDelta = np.matmul(
        np.diag(1/abs(V)), (np.matmul(np.diag(V.conjugate()),        derivVDelta)).real)
    ret = {}
    ret = {'derivMagWye': derivMagWye, 'derivMagDelta': derivMagDelta}
    return ret


def DER_coeff_computation(Node, connection, phase, coeffMagWye, coeffMagDelta, coeffWyeP0, coeffDeltaP0, Seq_numbers, tmp):
    Nmulti = coeffMagWye.shape[0]
    Node = Node
    Seq_numbers_skip_3 = Seq_numbers
    A = np.zeros((Nmulti, 2), complex)
    M = np.zeros((3, 2), complex)
    index = 0
    temp = []
    seq_skip = np.round(tmp['Seq_numbers'], 1).tolist()
    if connection == 'wye':
        for jj in range(0, len(phase)):
            node_phase = np.round(Node + float(phase[jj])*0.1, 1)
            try:
                index = seq_skip.index(node_phase) - 3
            except:
                return (None)
            temp = [index, (index+Nmulti)]
            A = A + coeffMagWye[:, temp]
            M = M + coeffWyeP0[:, temp]

    if connection == 'delta':
        for jj in range(0, len(phase)):
            node_phase = np.round(Node + phase[jj]*0.1, 1)
            try:
                index = seq_skip.index(node_phase) - 3
            except:
                return (None)
            temp = [index, (index+Nmulti)]
            A = A + coeffMagDelta[:, temp]
            M = M + coeffDeltaP0[:, temp]

    power_index = []
    for jj in range(0, len(phase)):
        node_phase = np.round(Node + phase[jj]*0.1, 1)
        try:
            index = seq_skip.index(node_phase) - 3
        except:
            return (None)
        power_index.append(index)

    [rr, cc] = M.shape
    for ii in range(0, rr):
        for jj in range(0, cc):
            if np.abs(M[ii, jj]) > 1:
                M[ii, jj] = np.sign(M[ii, jj])*(.99)
    ret = {'A': A, 'M':  M, 'power_index': power_index}
    return (ret)


def LinearApproxFeeder(masterfile):

    compile_cmd = "Compile {}".format(masterfile)
    dss.run_command(compile_cmd)
    Yckt = dss.Circuit.SystemY()
    shapes = int(np.sqrt(len(Yckt)/2))
    print("SHAPES ", shapes, flush=True)
    Ynet = np.array(Yckt).reshape((shapes, shapes*2))
    Y_net = Ynet[:, ::2] + Ynet[:, 1::2]*(1j)
    idx = 0
    node_to_number = {}
    for x in dss.Circuit.AllNodeNames():
        node_to_number[x.upper()] = str(idx)
        idx += 1
    idx = 0
    bus_to_number = {}
    for x in dss.Circuit.AllBusNames():
        bus_to_number[x.upper()] = str(idx)
        idx += 1
    number_to_bus = {bus_to_number[k]: k for k in bus_to_number.keys()}
    try:
        Seq_numbers = np.array([float(x.replace(x.split(
            ".")[0], bus_to_number[x.split(".")[0]])) for x in dss.Circuit.YNodeOrder()])
    except:
        Seq_numbers = np.array([float(x) for x in dss.Circuit.YNodeOrder()])
    Seq_numbers = Seq_numbers-1.0
    Nnode = math.floor(max(Seq_numbers))
    NmultiNode = Y_net.shape[0]
    YLL = Y_net[3:, 3:]
    Y00 = Y_net[0:3, 0:3]
    Y0L = Y_net[0:3, 3:]
    YL0 = Y_net[3:, 0:3]
    YLLi = inv(YLL)
    pu = dss.Vsources.PU()
    V0 = [1, 1, 1]

    w = -1*(np.matmul(np.matmul(YLLi, YL0), V0))
    Seq_numbers_round = np.floor(Seq_numbers)
    N = len(dss.Circuit.AllNodeNames())
    Gamma = np.row_stack(
        [np.array([1, -1, 0]), np.array([0, 1, -1]),    np.array([-1, 0, 1])])
    nps = len(dss.Circuit.AllNodeNames())-3
    H = np.array((nps, nps), dtype=complex)
    temp = None
    flag = 1
    for ii in range(0, N):
        point_ii = []
        point_ii = Seq_numbers[(Seq_numbers_round == ii).nonzero()]
        point_ii = (np.round(np.mod(point_ii, 1)*10)-1)
        point_ii = np.rint(point_ii).astype(int)
        row_idx = np.array(point_ii)
        col_idx = np.array(point_ii)
        try:
            gamma_value = Gamma[row_idx[:, None], col_idx]
        except:
            print(ii, point_ii)
            continue

        if flag == 1:
            temp = gamma_value
            flag = 0
        else:
            temp = linalg.block_diag(temp, gamma_value)
    H = temp
    x = 1
    # Vref = 1
    if x == 1:
        Vref = w
    jay = cmath.sqrt(-1)
    coeffWye = np.column_stack([np.matmul(YLLi, inv(np.diagflat(Vref.conjugate(
    )))),        -jay*np.matmul(YLLi, inv(np.diagflat(Vref.conjugate())))])
    coeffDelta = np.column_stack([np.matmul(np.matmul(YLLi, H.T),    inv(np.diagflat(np.matmul(H, Vref.conjugate(
    ))))),     -jay*np.matmul(np.matmul(YLLi, H.T),    inv(np.diagflat(np.matmul(H, Vref.conjugate()))))])
    ret_struct = magnitudeDerivative(Vref, coeffWye, coeffDelta)
    coeffMagWye = ret_struct['derivMagWye']
    coeffMagDelta = ret_struct['derivMagDelta']
    coeffWyeP0 = (np.matmul(
        np.matmul(np.diag(V0), Y0L.conjugate()),    coeffWye.conjugate())).real
    coeffDeltaP0 = (np.matmul(
        np.matmul(np.diag(V0), Y0L.conjugate()),    coeffDelta.conjugate())).real
    return {
        "Nnode": Nnode,
        "NmultiNode": NmultiNode,
        "coeffMagWye": coeffMagWye,
        "coeffMagDelta": coeffMagDelta,
        "coeffWyeP0": coeffWyeP0,
        "coeffDeltaP0": coeffDeltaP0,
        "coeffWye": coeffWye,
        "coeffDelta": coeffDelta,
        "Seq_numbers": Seq_numbers,
        "node_to_number": node_to_number,
        "bus_to_number": bus_to_number,
        "number_to_bus": number_to_bus
    }
