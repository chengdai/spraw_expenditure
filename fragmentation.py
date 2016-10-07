import pandas
import numpy
import sys
import glob
import os
import geopy.distance
import math
import threading

files = [f for f in glob.glob("*.csv") if 'Dissolve_MuniIntersect_' in f]

gis_fields_1971 = 


#def format_raw_data(file):

#Import csv file
raw_data = pandas.read_csv(file)

