import os
import sys
import logging
HOST = '127.0.0.1'
PORT = 8082
# switch between test and production DB, for testing purposes, it's necesary to bounce server
TEST_MODE=False
# app root dir
APP_DIR = os.getcwd()
# incomming files with batches,  through the REST-API are stored in  CSV_DIR
CSV_DIR = os.path.join(APP_DIR, 'csvs')
# output dir for reports, display function is generating data in OUT_DIR
OUT_DIR = os.path.join(APP_DIR, 'out')
# db files are stored in DB_DIR
DB_DIR = os.path.join(APP_DIR, 'db')
# master.log - REST-API server log, unit_test.log - test client log, random_generate.log - test data generator, 
LOG_DIR = os.path.join(APP_DIR, 'log')
# test data are generated in tests\data\ (random_generate.py)
TEST_DIR = os.path.join(APP_DIR, 'test')
# log level
LOG_LEVEL=logging.DEBUG
# chunk size, devides the file trasfer to chunks, used in clinet class
MAX_UPLOAD_BYTE_LENGHT = 1024 * 1024  # 1M
# server hsot : prot
API_URL = 'http://{}:{}'.format(HOST, PORT)



