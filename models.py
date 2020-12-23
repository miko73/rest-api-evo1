import os
import re

# from bottle import run, route, request, BaseRequest, respons

import config
import sqlite3
from sqlite3 import Error
import csv
from datetime import datetime


class DBConnector(object):

	def __init__(self, db_file_name):
		self.dbconn = None
		self.cursors = []
		try:
			if self.dbconn == None:
				self.dbconn = sqlite3.connect(db_file_name)
		except Error as e:
			print(e)
		print("in DBConnector __init__")
	
	def execute_one(self, sql_string):
		try:
			cur=self.dbconn.cursor()
		except Error as e:
			return None

		try:
			print (f"in execute_one {sql_string}")
			cur.execute(sql_string)
		except Error as e:
			print(f"error message: {e} ")
			return None

		return cur
	
	def get_cur(self):
		cur=self.dbconn.cursor()
		self.cursors.append(cur)
		return cur
		
	def __del__(self):
		print(f"in DBConnector __del__ {len(self.cursors)}")
		if self.dbconn != None:
			self.dbconn.commit()
			self.dbconn.close()

	def commit_all(self):
		if self.dbconn != None:
			self.dbconn.commit()

	def rollback_all(self):
		if self.dbconn != None:
			self.dbconn.rollback()


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


	def int_db_connector(self, db_file_name):
		if self.connector == None: 
			self.connector = DBConnector(db_file_name)
		cur = self.connector.get_cur()
		cur.execute("PRAGMA database_list;")
		curr_table = cur.fetchall()
		for table in curr_table:
			print("skupiny - {}".format(table))
		cur.close()
	

	def __str_ (self):
		pass	


	def init_header(self):
		self.field_list = "utc_timestamp"
#		print (f"self.plants_list [{self.plants_list}]")
		for pl in self.plants_list:
			if pl == 'temelin':
				self.field_list += ",temelin_actual,temelin_installed"
			elif pl == 'dukovany':
				self.field_list += ",dukovany_actual,dukovany_installed"
			elif pl == 'pocerady':
				self.field_list += ",pocerady_actual,pocerady_installed"

	def prepre_report(self):		
		select_str=f"select {self.field_list} from el_plants where utc_timestamp BETWEEN '{self.time_slot[0]}' and '{self.time_slot[1]}';"
		print(f'prepare_report select = {select_str}')
		cur = self.connector.execute_one(select_str)
		rows = cur.fetchall()
		file_name = f'{config.OUT_DIR}\\'
		file_name += datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'
		print (f"'prepare_report {file_name}'")
		try:
			with open(file_name , mode='w', newline='', encoding='UTF-8') as csv_stack:
				csv_writer = csv.writer(csv_stack, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				print(f'header  {self.field_list.split(",")}')
				csv_writer.writerow(self.field_list.split(","))			
				for row in rows:
					csv_writer.writerow(row)
				self.result_file_name = file_name	
		except:
				self.result_file_name = None
		
		return self.result_file_name


	def __del__(self):
		if self.connector == None: 
		   del self.connector
		   self.connector = None	

	def __str__(self):
		pass


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

	def int_db_connector(self, db_file_name):
		if self.connector == None: 
			self.connector = DBConnector(db_file_name)
		cur = self.connector.get_cur()
		cur.execute("PRAGMA database_list;")
		curr_table = cur.fetchall()
		for table in curr_table:
			print("skupiny - {}".format(table))
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
			print(rows[0])
			self.db_id = rows[0][0]
		return self.db_id     

	def load_from_file(self):
		with open( self.batch_file_name, encoding='UTF-8') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			line_count = 0
			for row in csv_reader:
				if line_count == 0:
					# print(f'Column names are {", ".join(row)}')
					line_count += 1
					self.num_of_suc_rec = 0
					self.num_of_failed_rec = 0
				else:
					# print(f'\t{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}')
					if len(row) == 7:
						insert_str  =f"insert into el_plants (utc_timestamp,temelin_actual,temelin_installed,dukovany_actual,dukovany_installed, pocerady_actual,pocerady_installed, batch_num) values ('{row[0]}', {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {self.db_id} )"
						if self.connector.execute_one(insert_str) != None:
							self.num_of_suc_rec += 1
						else:
							self.num_of_failed_rec += 1
					else:
						self.num_of_failed_rec += 1
				line_count += 1


	def close_batch(self):
		self.batch_end_date = datetime.today().isoformat()
		batch_update_str=f"update data_batches set num_of_suc_rec={self.num_of_suc_rec}, num_of_failed_rec={self.num_of_failed_rec}, commited=1, batch_end_date='{self.batch_end_date}' where id = {self.db_id}"
		print (batch_update_str)
		cur = self.connector.get_cur()
		try:
			cur.execute(batch_update_str)
			self.commited=1
			print ("commit")
			self.connector.commit_all()

		except Error as e:
			print(e)