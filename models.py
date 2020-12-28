import os
import re

import config
# import log_init
import logging

import sqlite3
from sqlite3 import Error
import csv
from datetime import datetime

log = logging.getLogger("modules.py")



# Universal Db connector used by all classes
class DBConnector(object):

	def __init__(self):
		self.dbconn = None
		self.cursors = []

		# switch between test and production DB, for testing purposes
		if (config.TEST_MODE == True):
			db_file_name = f"{config.DB_DIR}\\energo_test.db"
		else:
			db_file_name = f"{config.DB_DIR}\\energo.db"

		try:
			if self.dbconn == None:
				self.dbconn = sqlite3.connect(db_file_name)
		except Error as e:
			log.debug(e)

		log.debug(f"in DBConnector __init__ db_file_name [{db_file_name}]")
	

	def execute_one(self, sql_string):
		try:
			cur=self.dbconn.cursor()
		except Error as e:
			return None

		try:
			log.debug (f"in execute_one {sql_string}")
			cur.execute(sql_string)
		except Error as e:
			log.debug(f"error message: {e} ")
			return None

		return cur
	
	def get_cur(self):
		cur=self.dbconn.cursor()
		self.cursors.append(cur)
		return cur
		
	def __del__(self):
		log.debug(f"in DBConnector __del__ {len(self.cursors)}")
		if self.dbconn != None:
			self.dbconn.commit()
			self.dbconn.close()

	def commit_all(self):
		if self.dbconn != None:
			self.dbconn.commit()

	def rollback_all(self):
		if self.dbconn != None:
			self.dbconn.rollback()

# Reporter is the object for trating user data request in display function
class Reporter:
	"""docstring 
	for ClassName"""
	def __init__(self, time_slot, plants_list):
		
		self.time_slot = ws = time_slot.replace("'", "").split(" - ")
		self.plants_list = plants_list.replace("'", "").replace(" ", "").split(",")	# list = temelin, dukovany, pocerady
		self.field_list = ""
		self.init_header()
		self.connector=None
		self.result_file_name=None


	def int_db_connector(self):
		if self.connector == None: 
			self.connector = DBConnector()
		cur = self.connector.get_cur()
		cur.execute("PRAGMA database_list;")
		curr_table = cur.fetchall()
		for table in curr_table:
			log.debug("PRAGMA database_list - {}".format(table))
		cur.close()
	

	def __str_ (self):
		pass	

	# parse incomming parameter and prepare requestd head set
	def init_header(self):
		self.field_list = "utc_timestamp"
#		log.debug (f"self.plants_list [{self.plants_list}]")
		for pl in self.plants_list:
			if pl == 'temelin':
				self.field_list += ",temelin_actual,temelin_installed"
			elif pl == 'dukovany':
				self.field_list += ",dukovany_actual,dukovany_installed"
			elif pl == 'pocerady':
				self.field_list += ",pocerady_actual,pocerady_installed"

	# retrieve data from database and generate file, fils is then returend to clinet in server api
	def prepre_report(self):		
		select_str=f"select {self.field_list} from el_plants where utc_timestamp BETWEEN '{self.time_slot[0]}' and '{self.time_slot[1]}';"
		log.debug(f'prepare_report select = {select_str}')
		cur = self.connector.execute_one(select_str)
		rows = cur.fetchall()
		file_name = f'{config.OUT_DIR}\\'
		self.result_file_name = datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'
		file_name += self.result_file_name
		log.debug (f"'prepare_report {file_name}'")
		try:
			with open(file_name , mode='w', newline='', encoding='UTF-8') as csv_stack:
				csv_writer = csv.writer(csv_stack, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				log.debug(f'header  {self.field_list.split(",")}')
				csv_writer.writerow(self.field_list.split(","))			
				for row in rows:
					csv_writer.writerow(row)
				# self.result_file_name = file_name	
		except:
				self.result_file_name = None
		
		log.debug(f'self.result_file_name [{self.result_file_name}]')
		return self.result_file_name


	def __del__(self):
		if self.connector == None: 
		   del self.connector
		   self.connector = None	

	def __str__(self):
		pass

# Batch is the class for any incomming batch of data
class Batch:
	def __init__(self, batch_date, batch_file_name):
		self.batch_date = batch_date
		self.num_of_suc_rec = 0
		self.num_of_failed_rec = 0
		self.commited = 0
		self.batch_file_name = batch_file_name 
		self.batch_end_date = None
		self.connector=None
		self.db_id=None

	def int_db_connector(self):
		if self.connector == None: 
			self.connector = DBConnector()
		cur = self.connector.get_cur()
		cur.execute("PRAGMA database_list;")
		curr_table = cur.fetchall()
		for table in curr_table:
			log.debug("PRAGMA database_list - {}".format(table))
		cur.close()

	def __del__(self):
		if self.connector == None: 
		   del self.connector
		   self.connector = None	

	def __str__(self):
		return "Batch submition time {0} \nNumber for successfully inserter records {1} \nNumber for dubplicated, or wrong records {2}\nBatch completion time {3}\nBatch file name {4}\nBatch commited {5}\n".format(
			self.batch_date, 
			self.num_of_suc_rec, 
			self.num_of_failed_rec, 
			self.batch_end_date, 
			self.batch_file_name,
			self.commited)


	def batch_insert(self):
		insert_str  =f"insert into data_batches (batch_date, num_of_suc_rec, num_of_failed_rec, commited, batch_file_name) values ('{self.batch_date}', {self.num_of_suc_rec}, {self.num_of_failed_rec}, {self.commited}, '{self.batch_file_name}' ) "
		if self.connector.execute_one(insert_str) != None:
			self.get_db_id()	
		return self.db_id     

	def get_db_id(self):
		select_str="select max(seq) from sqlite_sequence where name='data_batches'"
		cur = self.connector.execute_one(select_str)
		if cur != None:
			rows = cur.fetchall()
			log.debug(rows[0])
			self.db_id = rows[0][0]
		return self.db_id     

	# pares incomming data and store to DB
	def load_from_file(self):
		with open( self.batch_file_name, encoding='UTF-8') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			line_count = 0
			for row in csv_reader:
				if line_count == 0:
					# log.debug(f'Column names are {", ".join(row)}')
					line_count += 1
					self.num_of_suc_rec = 0
					self.num_of_failed_rec = 0
				else:
					# log.debug(f'\t{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}')
					if len(row) == 7:
						insert_str  =f"insert into el_plants (utc_timestamp,temelin_actual,temelin_installed,dukovany_actual,dukovany_installed, pocerady_actual,pocerady_installed, batch_num) values ('{row[0]}', {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {self.db_id} )"
						if self.connector.execute_one(insert_str) != None:
							self.num_of_suc_rec += 1
						else:
							self.num_of_failed_rec += 1
					else:
						self.num_of_failed_rec += 1
				line_count += 1

	# updates the results od Batch data load and commits data inserted to DB
	def close_batch(self):
		self.batch_end_date = datetime.today().isoformat()
		batch_update_str=f"update data_batches set num_of_suc_rec={self.num_of_suc_rec}, num_of_failed_rec={self.num_of_failed_rec}, commited=1, batch_end_date='{self.batch_end_date}' where id = {self.db_id}"
		log.debug (batch_update_str)
		cur = self.connector.get_cur()
		try:
			cur.execute(batch_update_str)
			self.commited=1
			log.debug ("commit")
			self.connector.commit_all()

		except Error as e:
			log.debug(e)