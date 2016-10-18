import pandas
import numpy
import sys
import glob
import os
import geopy.distance
import math
import threading

current_dir = os.getcwd()
files = [f for f in glob.glob("*.csv") if 'LandUseApprox_' in f[0:14]]
fields = ['AREA']
landuse_codes = [10,11,12,13,15,16,50,75]
landuse_types = [(x,y) for x in fields for y in landuse_codes]
landuse_types.append(('DEVELOPABLE','BY_AREA'))

gis_field = {'1971':'LANDUSE_Slope_Clip_LU21_1971','1985':'LANDUSE_Slope_Clip_LU37_1985','1999':'LANDUSE_Slope_Clip_LU37_1999','2005':'LandUse2005_Slope_Clip_LUCODE'}

def agg_developable(dataset):
	'''Aggregate developable land use. Create new field for aggregate developable.
	Assumes two desired multiindex (AREA)'''
	agg_data = dataset.copy()
	dev_agg_data = agg_data.drop(('AREA',0), axis =1)
	agg_data.loc[:, ('DEVELOPABLE','BY_AREA')] = dev_agg_data.loc[:, 'AREA'].sum(axis=1)
	return agg_data.sortlevel(axis=1)

def agg_residential(dataset, new_LU_code):
	'''Aggregate residential land use. Create new land use code (new_LU_code) for aggregate residential.
	Assumes two desired multiindex (AREA) and uses MASSGIS LUCODES (10:13)'''
	agg_data = dataset.copy()
	agg_data2 = dataset.copy()
	agg_data.loc[:, ('AREA',new_LU_code)] = agg_data2.loc[:, ('AREA',10):('AREA',13)].sum(axis=1)
	return agg_data.sortlevel(axis=1).loc[:, landuse_types]

def format_gis_data(file):
	#Import .csv file
	raw_data = pandas.read_csv(file)
	landuse_field = gis_field[file[-13:-9]]


	#Reclassify undevelopable land by creating new land use code 0 and setting all undevelopable polygons to 0
	#Reclassify potentially developable land as new land use code 75 and set all potentially developable polygon as 75
	reclass_data = raw_data.copy(deep=True)
	reclass_data.loc[reclass_data.MassGIS_Dev_Undev_LU_Ref_Not_Dev == 1, landuse_field] = 0
	reclass_data.loc[reclass_data.MassGIS_Dev_Undev_LU_Ref_P_Dev == 1, landuse_field] = 75

	#Add in farmland
	reclass_data_farmland = raw_data.copy(deep=True)
	farm_grid_data = pandas.pivot_table(reclass_data_farmland, index = 'OBJECTID_1',columns = landuse_field, aggfunc=numpy.sum)[[('AREA',1),('AREA',2)]]
	farm_muni_data = pandas.pivot_table(reclass_data_farmland, index = 'TOWN_ID',columns = landuse_field, aggfunc=numpy.sum)[[('AREA',1),('AREA',2)]]

	#Create a table storing the total amount of each land use type in a grid (via OBJECTID) 
	agg_grid_data = pandas.pivot_table(reclass_data, index = 'OBJECTID_1',columns = landuse_field, aggfunc=numpy.sum)[['AREA']]
	agg_grid_data = agg_developable(agg_grid_data)
	agg_grid_data = agg_residential(agg_grid_data,50)
	agg_grid_data = agg_grid_data.join(farm_grid_data).sortlevel(axis=1)

	#Create a table storing the total amount of each land use type in a municipality (via FIPS code)
	agg_muni_data = pandas.pivot_table(reclass_data, index = 'TOWN_ID',columns = landuse_field, aggfunc=numpy.sum)[['AREA']]
	agg_muni_data = agg_developable(agg_muni_data)
	agg_muni_data = agg_residential(agg_muni_data,50)
	agg_muni_data = agg_muni_data.join(farm_muni_data).sortlevel(axis=1)

	#Create a column for TOWN_ID code 
	muni_data = raw_data.copy(deep=True)
	muni_data = muni_data[['OBJECTID_1','TOWN_ID','Longitude','Latitude']].drop_duplicates()

	#Format to join to the pivoted land use table based on grid ID
	grid_fips_data = muni_data.set_index('OBJECTID_1')
	grid_fips_data = grid_fips_data.rename(columns={'TOWN_ID':('TOWN_ID','TOWN_ID'),'Longitude':('Longitude','Longitude'),'Latitude':('Latitude','Latitude')})

	#Create final Grid ID table by join FIPS code data to grid land use table
	gridid_data = agg_grid_data.join(grid_fips_data)

	#Create a table to keep track of Grid ID's that are part of the municipality's FIPS code
	muni_gridid_data = muni_data.groupby('TOWN_ID')['OBJECTID_1'].unique()
	muni_gridid_data.name = ('OBJECTID_1','OBJECTID_1')

	#Create final FIPS ID table by joining Grid ID's to land use table
	muniid_data = agg_muni_data.join(muni_gridid_data)

	#Create 2 new CSV files
	#gridid_data.to_csv('gridid_'+file[-13:-4]+'.csv')
	#muniid_data.to_csv('muniid_'+file[-13:-4]+'.csv')
	
	print "Conversion Done"

	return gridid_data, muniid_data

def get_cbd_data(cbd_file):
	data = pandas.read_csv(cbd_file)

	#Extract muni name and lat/long of the town, rename fields, and set index to the town ID
	return data.loc[:,['muni','lat','long']].rename(columns={'muni': 'Municipality','lat':'CBD_Lat','long':'CBD_Long'}).set_index(data['id'])

def local_proximity(file):
	grid, muni = format_gis_data(file)

	print 'Calculating Local Proximity for: ' + str(file[-13:-4])

	#Create an dictionary to store all of the local proximity data
	local_prox = {}
	grid_area = grid.loc[:,'AREA']
	lu_codes = grid_area.columns.values

	#Iterate through all rows where municipality is TownID of the grid and row is the information
	for municipality, row in muni.iterrows():
		print municipality

		#Initialize all initial landuse local proximity to be None
		#None is preserved for a pair of landuse type if one or more the landuse type(s) is missing
		ij_pairs = [(i,j) for i in lu_codes for j in lu_codes]
		local_prox[municipality] = dict.fromkeys(ij_pairs, None)

		for m_grid in row['OBJECTID_1']['OBJECTID_1']: #For every grid in the municipality
			t_m = grid.loc[:,'DEVELOPABLE'].loc[m_grid, 'BY_AREA'] #Set t_m to the total deveopable and potentially developable area
			
			#Iterate through all landuse codes (10,11,12,13,15,16,50)
			for landuse1 in lu_codes:
				I = row.loc[('AREA',landuse1)] #Set I, the total amount of landuse type i in the municipality
				i_m = grid_area.loc[m_grid][landuse1] #Set i_m to be the amount of landuse i in cell m
				
				#Iterate through all landuse j (10,11,12,13,15,16,50) for pair (i,j)
				for landuse2 in lu_codes: 
					j_m = grid_area.loc[m_grid][landuse2] #Set j_m to be the amount of landuse j in cell m

					#Check for any non-finite (nan or infinite) numbers to exclude from calculation
					if I != 0 and t_m != 0 and numpy.isfinite(I) and numpy.isfinite(t_m) and numpy.isfinite(i_m) and numpy.isfinite(j_m):
						#If this is the first time the calculation is performed on this pair, change None to float. If not, add onto existing value
						if local_prox[municipality][(landuse1,landuse2)] == None:
							local_prox[municipality][(landuse1,landuse2)] = (i_m/I)*(j_m/t_m)
						else:
							local_prox[municipality][(landuse1,landuse2)] += (i_m/I)*(j_m/t_m)

		for ij_pair in local_prox[municipality].keys():
			I = row.loc[('AREA',ij_pair[0])]
			J = row.loc[('AREA',ij_pair[1])]
			T = muni.loc[:,'DEVELOPABLE'].loc[municipality, 'BY_AREA']

			#Adjust for Composition and Assymmetry: Adjust for overall composition of municipality
			#Results from adjusted measures should be bound by 0 and 1
			if ij_pair[0] == ij_pair[1] and local_prox[municipality][ij_pair] != None:
				local_prox[municipality][ij_pair] = (local_prox[municipality][ij_pair]-(I/T))/(1-I/T)
			else:
				if I+J != 0 and J != 0 and numpy.isfinite(I+J) and numpy.isfinite(J) and local_prox[municipality][ij_pair] != None:
					local_prox[municipality][ij_pair] = local_prox[municipality][ij_pair]/(J/(I+J))

	local_prox_table = pandas.DataFrame.from_dict(local_prox, orient = 'index').sortlevel(axis=1)
	local_prox_table.to_csv('Local_Prox_'+file[-13:-4]+'.csv')

	return local_prox_table



def global_proximity(file):
	grid, muni = format_gis_data(file)

	print 'Calculating Global Proximity for: ' + str(file[-13:-4])

	#Create an dictionary to store all of the global proximity data:
	global_prox = {}
	grid_area = grid.loc[:,'AREA']                                
	lu_codes = grid_area.columns.values

	grid_lat = grid.loc[:,('Latitude','Latitude')]
	grid_long = grid.loc[:,('Longitude','Longitude')]

	#Iterate through all rows where municipality is TownID of the grid and row is the information
	for municipality, row in muni.iterrows():
		print municipality

		#Initialize an empty dictionary to keep track of all the global proximity results
		grids = row['OBJECTID_1']['OBJECTID_1']
		ij_pairs = [(i,j) for i in lu_codes for j in lu_codes]
		global_prox[municipality] = dict.fromkeys(ij_pairs, None)

		#Initialize the calculations for w_x
		w_x = 0
		N = len(grids)
		N_choose_two = (N*(N-1))/2


		for m_grid in grids: #For every grid m in the municipality

			#Create a dictionary for the distance between two cells
			dist_dict = {}
			for k_grid in grids: #Iterate through all cell k, where k>m and add to dictionary and add to 
				if k_grid > m_grid:
					distance_m_k = geopy.distance.distance((grid_lat[m_grid],grid_long[m_grid]),(grid_lat[k_grid],grid_long[k_grid])).meters
					dist_dict[(m_grid,k_grid)] = distance_m_k
					w_x += distance_m_k/N_choose_two

			#Select i
			for landuse1 in lu_codes:
				I = row.loc[('AREA',landuse1)] #Set I, the total amount of landuse type i in the municipality
				i_m = grid_area.loc[m_grid][landuse1] #Set i_m to be the amount of landuse i in cell m

				for k_grid in grids: #For every other grid in the municipality
					if k_grid > m_grid:

						#Select j, iterate through all j in a cell k
						for landuse2 in lu_codes:
							j_m = grid_area.loc[m_grid][landuse2]
							J = row.loc[('AREA',landuse2)]

							if I != 0 and J != 0 and numpy.isfinite(I) and numpy.isfinite(J) and numpy.isfinite(i_m) and numpy.isfinite(j_m):
								if global_prox[municipality][(landuse1,landuse2)] == None:
									global_prox[municipality][(landuse1,landuse2)] = (i_m/I)*(j_m/J) * dist_dict[(m_grid,k_grid)]
								else:
									global_prox[municipality][(landuse1,landuse2)] += (i_m/I)*(j_m/J) * dist_dict[(m_grid,k_grid)]

		#Make adjustments with average distance
		for ij_pair in global_prox[municipality].keys():
			if global_prox[municipality][ij_pair] != 0 and global_prox[municipality][ij_pair] != None:
				global_prox[municipality][ij_pair] = (w_x/global_prox[municipality][ij_pair]) - 1


	global_prox_table = pandas.DataFrame.from_dict(global_prox, orient = 'index').sortlevel(axis=1)
	global_prox_table.to_csv('Global_Prox_'+file[-13:-4]+'.csv')
	return global_prox_table

def centrality(file, cbd_file):

	grid, muni = format_gis_data(file)

	cbd = get_cbd_data(cbd_file)

	print 'Calculating Centrality for: ' + str(file[-13:-4])

	cent = {}
	grid_area = grid.loc[:,'AREA']
	lu_codes = grid_area.columns.values

	grid_lat = grid.loc[:,('Latitude','Latitude')]
	grid_long = grid.loc[:,('Longitude','Longitude')]

	muni_lat = cbd.loc[:,'CBD_Lat']
	muni_long = cbd.loc[:,'CBD_Long']

	#Iterate through all rows where municipality is TownID of the grid and row is the information
	for municipality, row in muni.iterrows():
		print municipality

		cent[municipality] = dict.fromkeys(lu_codes,None)

		municipality_lat = muni_lat[municipality]
		municipality_long = muni_long[municipality]

		grids = row['OBJECTID_1']['OBJECTID_1']
		N = len(grids)

		w = 0

		for m_grid in grids:
			distance = geopy.distance.distance((grid_lat[m_grid],grid_long[m_grid]),(municipality_lat, municipality_long)).meters
			w += distance/N

			for landuse in lu_codes:
				i_m = grid_area[landuse][m_grid]
				I = row['AREA'][landuse]

				if I != 0 and numpy.isfinite(i_m) and numpy.isfinite(I):
					if cent[municipality][landuse] == None:
						cent[municipality][landuse] = (i_m/I)*distance
					else:
						cent[municipality][landuse] += (i_m/I)*distance

		for landuse in cent[municipality].keys():
			if cent[municipality][landuse] != 0 and cent[municipality][landuse] != None:
				cent[municipality][landuse] = (w/cent[municipality][landuse]) - 1

	centrality_table = pandas.DataFrame.from_dict(cent, orient = 'index').sortlevel(axis=1)
	centrality_table.to_csv('Centrality_'+file[-13:-4]+'.csv')
	return centrality_table

def concentration(file):

	grid, muni = format_gis_data(file)

	print 'Calculating Concentration for: ' + str(file[-13:-4])

	delta = {}
	grid_area = grid.loc[:,'AREA']
	lu_codes = grid_area.columns.values

	for municipality, row in muni.iterrows():
		print municipality

		delta[municipality] = dict.fromkeys(lu_codes, None)

		T = muni.loc[:,'DEVELOPABLE'].loc[municipality, 'BY_AREA']

		for m_grid in row['OBJECTID_1']['OBJECTID_1']: #For every grid in the municipality
			t_m = grid.loc[:,'DEVELOPABLE'].loc[m_grid, 'BY_AREA'] #Set t_m to the total deveopable area

			for landuse in lu_codes:
				i_m = grid_area[landuse][m_grid]
				I = row['AREA'][landuse]

				if I != 0 and T != 0 and numpy.isfinite(i_m) and numpy.isfinite(t_m) and numpy.isfinite(I) and numpy.isfinite(T):
					if delta[municipality][landuse] == None:
						delta[municipality][landuse] = 0.5 * (i_m/I - t_m/T)
					else:
						delta[municipality][landuse] += 0.5 * (i_m/I - t_m/T)

	concentration_table = pandas.DataFrame.from_dict(delta, orient = 'index').sortlevel(axis=1)
	concentration_table.to_csv('Concentration_'+file[-13:-4]+'.csv')
	return concentration_table

#Implement algorithm using threads to allow for concurrent analysis
class sprawlThread (threading.Thread):
    def __init__(self, threadID, file):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.file = file
    def run(self):
        print "Starting thread for: " + str(self.file[-13:-4])
        global_proximity(self.file)
        local_proximity(self.file)
        centrality(self.file, 'townhall_geo.csv')
        concentration(self.file)
        print "Exiting thread for: " + str(self.file[-13:-4])

def main():
	print files	

	thread_1 = sprawlThread(1, files[0])
	thread_2 = sprawlThread(2, files[1])
	thread_3 = sprawlThread(3, files[2])
	thread_4 = sprawlThread(4, files[3])
	thread_5 = sprawlThread(5, files[4])
	thread_6 = sprawlThread(6, files[5])
	thread_7 = sprawlThread(7, files[6])
	thread_8 = sprawlThread(8, files[7])

	thread_1.start()	
	thread_2.start()
	thread_3.start()
	thread_4.start()
	thread_5.start()
	thread_6.start()
	thread_7.start()
	thread_8.start()
	
if __name__=='__main__':
    main()
