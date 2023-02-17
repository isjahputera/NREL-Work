# Indiana Sjahputera
# Dr. Jennifer King - NREL
# Human Behavior Model (trial)

# Sites/sources for Credit:
# [1] https://data-flair.training/blogs/python-probability-distributions/#:~:text=What%20is%20Python%20Probability%20Distribution,out%20of%20all%20possible%20outcomes. 
# [2] https://www.geeksforgeeks.org/plotting-histogram-in-python-using-matplotlib/
# [3] https://www.geeksforgeeks.org/python-gaussian-fit/ 
# [4] https://towardsdatascience.com/histograms-and-density-plots-in-python-f6bda88f5ac0 
# [5] https://www.census.gov/quickfacts/denvercountycolorado 
# [6] https://www.geeksforgeeks.org/python-read-csv-columns-into-list/

import pandas as pd
from pandas import *
import numpy as np
import csv
import matplotlib.pyplot as plt
from matplotlib import colors 
# from matplotlib.ticker import PercentFormatter
import scipy as sp
from scipy import stats
from scipy.optimize import curve_fit 

# Footnotes about the data inputs:
# For age, used raw ages and for the data sample only accepted people over the age of 18 for simplicity
# For socioeconomic, the use of raw income pay so we can decide to put them in incoe brackets or not
# For housing used differerent terms:
    # Single family attatched; Single family detatched; Multiple Family Home; 
    # Apartments; Vintage Homes; Mobile homes
# For citizenship, status of residence
# For political, list different parties or unaffiliated


data = read_csv("simplified_data.csv")

# This portion will convert the columns from the csv file into lists:
age = data["Age"].tolist()
econ = data["Socioeconomic"].tolist()
house = data["Housing"].tolist()
citizen = data["Citizenship"].tolist()
dependant = data["Dependancy"].tolist()
politics = data["Politics"].tolist()
edu = data["Education"].tolist()
race = data["Race"].tolist()
ethnic = data["Ethnicity"].tolist()
gen = data["Gender"].tolist()

print("Housing type: ", house)
age_sorted = sorted(age)
plt.plot(age_sorted)
plt.show()
econ_sorted = sorted(econ)
plt.plot(econ_sorted)
plt.show()
plt.hist(house)
plt.show()

    


# Creation of Probability Distribution
# Usual use of Gaussian from Mesa codes (observed)

def func(x, a, x0, sigma):    # [3] in defining the Gaussian function
    return a*np.exp(-(x-x0)**2/(2*sigma**2))

# Another thing to remember is the norm.pdf() function, the probability density function.
# 

# This next portion is a trial run, used by the examples from sources given above
# The sample data that I am using is the demographics from Denver, CO

