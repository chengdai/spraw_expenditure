import sqlite3
import glob
import pandas

#Name of SQL database
sql_schema = 'Dissolve.db'

files = [f for f in glob.glob("*.csv") if "Dissolve_" in f]

#Create table names for the SQL database. 
#Table names will have 'landuse_' as prefix and the year and length as the ending in the format 'YYYY_Length'
#Store table names in a dictonary (table_names) with the .csv file name as key and SQL table name as value
table_names = {}
for f in files:
	table_names[f] = 'dissolve_' + f[-8:-4]

conn = sqlite3.connect(sql_schema)
c = conn.cursor()

#Convert each .csv file into a SQL database
#Iterate through all .csv file, convert each file into a Pandas DataFrame and then insert into SQL schema
for f in files:
	raw_dataset = pandas.read_csv(f, index_col = 0)
	raw_dataset.to_sql(table_names[f],conn)
