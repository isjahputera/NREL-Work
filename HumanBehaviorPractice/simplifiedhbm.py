# This is a simplified restart to the work done in HumanBehaviorModel

# Sites/sources for Credit:
# [1] https://data-flair.training/blogs/python-probability-distributions/#:~:text=What%20is%20Python%20Probability%20Distribution,out%20of%20all%20possible%20outcomes. 
# [2] https://www.geeksforgeeks.org/plotting-histogram-in-python-using-matplotlib/
# [3] https://www.geeksforgeeks.org/python-gaussian-fit/ 
# [4] https://towardsdatascience.com/histograms-and-density-plots-in-python-f6bda88f5ac0 
# [5] https://www.census.gov/quickfacts/denvercountycolorado 
# [6] https://www.geeksforgeeks.org/python-read-csv-columns-into-list/
# [7] https://matplotlib.org/stable/gallery/pyplots/pyplot_text.html#sphx-glr-gallery-pyplots-pyplot-text-py 
# [8] https://www.gaussianwaves.com/2020/06/using-matplotlib-histogram-in-python/ 
# [9] https://stackoverflow.com/questions/68409093/using-python-how-to-take-input-from-an-excel-file-define-a-function-and-genera
# [10] https://machinelearningmastery.com/probability-density-estimation/ 
# [11] https://www.pluralsight.com/guides/interpreting-data-using-descriptive-statistics-python 

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

# Reads data as csv file
data = pd.read_csv("simplified_data.csv")  

# house = data['Housing'].tolist()
# house_sorted = sorted(house)
# age = data['Age'].tolist()
# mu_age = mean(age)
# sigma_age = std(age)
# print("mu: ", mu_age, "; sigma: ", sigma_age )
# dist = norm(mu_age, sigma_age)
# values = [value for value in range(18,65)]
# prob = [dist.pdf(value) for value in values]
# plt.hist(age)
# plt.plot(values, prob)
# plt.xlabel('Age')
# plt.ylabel('Number of People')
# plt.title('Age Histogram')
# plt.text(30, 3.5, r'$\mu=36.2,\ \sigma=17.3$')
# plt.show()

# Main questions for Caitlyn:
# - Was getting confused with def functions and calling them. 
#   Can we work through one of the def functions?
# - Does the logic make sense? The data looks wonky,
#   but is it because the sample size is so small? 
# - Once I can get this to work, I could implement this methodology 
#   for the rest of the categories and make a histogram/distribution from them..

# Make a def function to read the data and categorize each column to separate sections 
def read_input(data):
    #global age_sorted, econ_sorted, house_sorted, citi_sorted, dep_sorted, poli_sorted, edu_sorted, race_sorted, ethnic_sorted, gen_sorted
    global biglist, namelist
    biglist = []
    namelist = []
    for i in data:
        datalist = data[i].tolist()
        listsorted = sorted(datalist)
        biglist.append(listsorted)
        namelist.append(i)
    print(namelist)
    print(biglist)
    return listsorted

        # if i == "Age":
        #     age = data[i].tolist()
        #     age_sorted = sorted(age)
        #     print(i + ":", age_sorted)
        #     sort = age_sorted
        # if i == "Socioeconomic":
        #     econ = data[i].tolist()
        #     econ_sorted = sorted(econ)
        #     print(i + ":", econ_sorted)
        #     sort = econ_sorted
        # if i == "Housing":
        #     house = data[i].tolist()
        #     house_sorted = sorted(house)
        #     print(i + ":", house_sorted)
        #     sort = house_sorted
        # if i == "Citizenship":
        #     citi = data[i].tolist()
        #     citi_sorted = sorted(citi)
        #     print(i + ":", citi_sorted)
        #     sort = citi_sorted
        # if i == "Dependancy":
        #     dep = data[i].tolist()
        #     dep_sorted = sorted(dep)
        #     print(i + ":", dep_sorted)
        #     dep = dep_sorted
        # if i == "Politics":
        #     poli = data[i].tolist()
        #     poli_sorted = sorted(poli)
        #     print(i + ":", poli_sorted)
        #     sort = poli_sorted
        # if i == "Education":
        #     edu = data[i].tolist()
        #     edu_sorted = sorted(edu)
        #     print(i + ":", edu_sorted)
        #     sort = edu_sorted
        # if i == "Race":
        #     race = data[i].tolist()
        #     race_sorted = sorted(race)
        #     print(i + ":", race_sorted)
        #     sort = race_sorted
        # if i == "Ethnicity":
        #     ethnic = data[i].tolist()
        #     ethnic_sorted = sorted(ethnic)
        #     print(i + ":", ethnic_sorted)
        #     sort = ethnic_sorted
        # if i == "Gender":
        #     gen = data[i].tolist()
        #     gen_sorted = sorted(gen)
        #     print(i + ":", gen_sorted)
        #     sort = gen_sorted
    #return sort
    



# Make a def function to read the categories into a histogram
def hist_data():
    # global listothing
    # listothing = [age_sorted, econ_sorted, house_sorted, citi_sorted, dep_sorted, poli_sorted, edu_sorted, race_sorted, ethnic_sorted, gen_sorted]
    npbiglist = np.array(biglist)
    listnum = len(biglist)
    npnamelist = np.array(namelist)
    for i in range(listnum):
        plt.hist(npbiglist[i])
        plt.xlabel(npnamelist[i])
        plt.ylabel('Number of People')
        plt.title(npnamelist[i] + ' Histogram')
        plt.show()
        # if i == age_sorted:
        #     print(i)
        #     plt.hist(i)
        #     plt.xlabel("Age")
        #     plt.ylabel('Number of People')
        #     plt.title('Age Histogram')
        #     plt.show()
        # if i == econ_sorted:
        #     print(i)
        #     plt.hist(i)
        #     plt.xlabel("Socioeconomic Salary")
        #     plt.ylabel('Number of People')
        #     plt.title('Socioeconomic Histogram')
        #     plt.show()

        
            
# Make a def function to output parameters of mu and sigma for normal distribution
def nordis_data():
    global mu_age, mu_econ
    global sigma_age, sigma_econ
    for i in listothing:
        if i == age_sorted:
            mu_age = mean(age_sorted)
            print(mu_age)
            sigma_age = std(age_sorted) 
            print(sigma_age)
        if i == econ_sorted:
            mu_econ = mean(econ_sorted)
            print(mu_econ)
            sigma_econ = std(age_sorted) 
            print(sigma_econ)
        



# Make a def function to estimate a distribution from histogram
def pdf_data():
    global listothing
    listothing = [age_sorted, econ_sorted, house_sorted, citi_sorted, dep_sorted, poli_sorted, edu_sorted, race_sorted, ethnic_sorted, gen_sorted]
    lenlistothing = len(listothing)
    listoxlabel = np.array(['Age', 'Socioeconomic', 'House', 'Citizenship', 'Dependancy', 'Politics', 'Education', 'Race', 'Ethnicity', 'Gender'])
    for i in range(lenlistothing):
        pdf = stats.norm.pdf(listothing[i]) # Ask how to make a pdf for strings amt i.e. House aka qualitative
        print(pdf)
        plt.plot(pdf)
        print(listothing[i])
        plt.hist(listothing[i])
        plt.xlabel(listoxlabel[i])
        plt.ylabel('Number of People')
        plt.title(listoxlabel[i] + ' Histogram')
        plt.show()




# Notes with Caitlyn - 11/08/2022
# Use histogram, use line plot when necessary
# More times sampled, more normal distribution will be 
# Good to simplify data first, then can build to more normal 
# 4 Functions:
# i) Read funciton (reads data)
# ii) Histogram (plot each data stream in its own histogram)
# iii) Estimate a distribution from that histogram
# iv) Output parameters (mu, sigma for normal distributions)



# This portion of the code will take the converted csv file and read the data
# df_age = pd.read_csv("DenverDataPractice", col1 = ["Age"])   # Insert csv file of demographics data - age
# df_econ = pd.read_csv("DenverDataPractice", col2 = ["Socioeconomic"])
# df_house = pd.read_csv("DenverDataPractice", col3 = ["Housing"])
# df_citizen = pd.read_csv("DenverDataPractice", col4 = ["Citizenship"])
# df_dependant = pd.read_csv("DenverDataPractice", col5 = ["Dependancy"])
# df_politics = pd.read_csv("DenverDataPractice", col6 = ["Political"])
# df_edu = pd.read_csv("DenverDataPractice", col7 = ["Education"])
# df_race = pd.read_csv("DenverDataPractice", col8 = ["Race"])
# df_ethnic = pd.read_csv("DenverDataPractice", col8 = ["Ethnicity"])
# df_gen = pd.read_csv("DenverDataPractice", col9 = ["Gender/Sex"]);
