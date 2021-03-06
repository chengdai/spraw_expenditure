import sqlite3
import pandas
import numpy
import glob


class Fragmentation(object):
	
	def __init__(self, input_file):
		self.file = input_file

	def mean_patch_size(self):
		'''
		Calculates the mean patch size metric for each municipality
		Input: raw csv file on land use from GIS
		Output: table with mean patch size calculations for each residential, commercial and industrial land use type for each municipality
		'''

		#Import parcel data from csv file
		parcel_data = pandas.read_csv(self.file)
		year = self.file[-8:-4]

		#Extract only parcels that are 1) characterized by the target landuse codes for that particular & 2) developable
		developable_parcels = parcel_data
		#developable_parcels = parcel_data[(parcel_data[gis_field[year]].isin(landuse_codes)) & (parcel_data['MassGIS_Dev_Undev_LU_Ref_Not_Dev'] != 1)]

		#Create a table mapping each municipality to the parcels that are located in the municipality
		muni_parcel_map = developable_parcels.groupby('TOWN_ID')['OBJECTID'].unique()
		developable_parcels.set_index(['OBJECTID'], inplace = True)

		#Initiate a empty dictionary to store the mean patch sizes
		mean_patch_sizes = {}

		#Iterate through each municipality
		for muni, parcel_list in muni_parcel_map.iteritems():
			print muni 

			#Create a dictionary that keeps track of patches, where keys are land use codes and the values are lists of the area for each patch
			patch_sizes = [] 

			for parcel_id in parcel_list:
				
				#Store the area of each patch by landuse in the patch_sizes dictionary
				area = developable_parcels.loc[parcel_id][['Shape_Area']]
				patch_sizes.append(area)

			#Sum of all area of patches i with land use k, or a_(i,k)
			sum_of_patches = sum(patch_sizes)

			#Total number of patches with land use k, n_k
			number_of_patches = len(patch_sizes)

			#Mean patch size for the land use k
			if number_of_patches != 0:
				mean_patch_sizes[muni] = sum_of_patches/number_of_patches
			else:
				mean_patch_sizes[muni] = None

		mean_patch_size_table = pandas.DataFrame.from_dict(mean_patch_sizes, orient = 'index').sortlevel(axis=1)
		mean_patch_size_table.to_csv('Mean_Patch_Size_' + year + '.csv')

		return mean_patch_size_table

	def mean_perimeter_to_area(self):
		'''
		Calculates the mean perimeter to area metric for each municipality
		Input: raw csv file on land use from GIS
		Output: table with mean perimeter to area calculations for each residential, commercial and industrial land use type for each municipality
		'''

		#Import parcel data from csv file
		parcel_data = pandas.read_csv(self.file)
		year = self.file[-8:-4]

		#Extract only parcels that are 1) characterized by the target landuse codes for that particular & 2) developable
		developable_parcels = parcel_data
		#developable_parcels = parcel_data[(parcel_data[gis_field[year]].isin(landuse_codes)) & (parcel_data['MassGIS_Dev_Undev_LU_Ref_Not_Dev'] != 1)]

		#Create a table mapping each municipality to the parcels that are located in the municipality
		muni_parcel_map = developable_parcels.groupby('TOWN_ID')['OBJECTID'].unique()
		developable_parcels.set_index(['OBJECTID'], inplace = True)

		perimeter_to_area = {}

		for muni, parcel_list in muni_parcel_map.iteritems():
			print muni

			perimeter_area_ratios = []

			for parcel_id in parcel_list:
				perimeter, area = developable_parcels.loc[parcel_id][['Shape_Length','Shape_Area']]

				if area != 0:
					perimeter_area_ratios.append(perimeter/area)

			sum_of_ratios = sum(perimeter_area_ratios)

			number_of_ratios = len(perimeter_area_ratios)

			if number_of_ratios != 0:
				perimeter_to_area[muni] = sum_of_ratios/number_of_ratios
			else:
				perimeter_to_area[muni] = None

		perimeter_to_area_table = pandas.DataFrame.from_dict(perimeter_to_area, orient = 'index').sortlevel(axis=1)
		perimeter_to_area_table.to_csv('Mean_Perimeter_to_Area' + year + '.csv')

		return perimeter_to_area_table

	def descriptives(self):
		data = pandas.read_csv(self.file, index_col = 0)
		descriptive = data.describe()
		print descriptive
		descriptive.to_csv(self.file[:-8] + 'descriptive_' + self.file[-8:-4] + '.csv')


def main():
	#Global variables: Needed for reading of files. Adjust based on raw data
	global files, gis_field, dev_code
	files = [f for f in glob.glob("*.csv") if 'Dissolve_' in f[0:14]]
	gis_field = {'2005':'MassGIS_Dev_Undev_LU_Ref_Dev'}
	dev_code = [1]

	for file in files:
		frag_analysis = Fragmentation(file)
		frag_analysis.mean_patch_size()
		frag_analysis.mean_perimeter_to_area()

if __name__=='__main__':
    main()
