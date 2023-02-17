
import glob
from mpi4py import MPI

from aumcfunctions import OrchestrateAgent


size = MPI.COMM_WORLD.Get_size()
ranks = MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()

flist = glob.glob("agentdebug/*.json")
flist.sort()


OrchestrateAgent(flist[int(ranks)], ranks)
