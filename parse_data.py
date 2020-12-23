import os
import re

# from bottle import run, route, request, BaseRequest, respons

import config
import sqlite3
from sqlite3 import Error
import csv
from datetime import datetime
from models import DBConnector, Batch, Reporter
import json


# Maximum size of memory buffer for request body in bytes.
# BaseRequest.MEMFILE_MAX = MAX_UPLOAD_BYTE_LENGHT


def load_batch(file_name):
	# dbcon = create_connection(f"{DB_DIR}/energo.db")
	now = datetime.today().isoformat()
	act_batch = Batch(now, file_name )
	act_batch.int_db_connector(f"{config.DB_DIR}/energo.db")


	if act_batch.batch_insert() == None:
		print ("error in act_batch")
		act_batch.connector.rollback_all()
		del act_batch
		return
	else:
		print ( f'Batch num - {act_batch.db_id}')
			# print (act_batch)

	act_batch.load_from_file()
	act_batch.close_batch()
	print (act_batch)
	del act_batch
	return True 


def get_query(time_slot, plants_list):	
	try:
		repo_1 = Reporter(time_slot, plants_list)
		print(f'repo_1.time_slot - {repo_1.time_slot}')
		print(f'repo_1.field_list - {repo_1.field_list}')
	except:
		if repo_1 != None:
			print(f'repo_1.time_slot - {repo_1.time_slot}')
			print(f'repo_1.field_list - {repo_1.field_list}')
		return	
	repo_1.int_db_connector(f"{config.DB_DIR}/energo.db")
	file_name = repo_1.prepre_report()
	print (f'file_name [{file_name}]')
	return file_name


#get_query( '2020-05-01 20:00:00 - 2020-05-01 21:00:00', 'dukovany, pocerady')

# load_batch("C:\\Users\\micha\\Projects\\python-chunked-upload-example\\csvs\\simple.txt")



