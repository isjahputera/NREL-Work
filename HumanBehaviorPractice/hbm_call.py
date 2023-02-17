import simplifiedhbm    #Calling the code here
import pandas as pd
from pandas import *
import numpy as np
import csv
import matplotlib.pyplot as plt
# from matplotlib import pyplot
from matplotlib import colors 
# from matplotlib.ticker import PercentFormatter
import scipy as sp
from scipy import mean
from scipy import std
from scipy import stats
from scipy.stats import norm
from scipy.optimize import curve_fit 

data = pd.read_csv("simplified_data.csv")

sort = simplifiedhbm.read_input(data)
# display = simplifiedhbm.hist_data()
# woohoo = simplifiedhbm.nordis_data()
showie = simplifiedhbm.pdf_data()