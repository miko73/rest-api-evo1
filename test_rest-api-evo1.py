import os
import unittest
import time
import config
import csv
# import log_init

from os import path
from client import Client
from models import DBConnector, Batch, Reporter
import logging

TEST_DIR = os.path.join(config.APP_DIR, 'tests')

from parse_data import upload_batch, get_query

log_file= f'{config.LOG_DIR}\\unit_test.log'

logging.basicConfig(filename=log_file, level=config.LOG_LEVEL)
log = logging.getLogger("test_rest-api-evo1.py")

# Before testing it's necessary to modify TEST_MODE=True in config.py, to avoid data modification in production DB 

class TestFileUpload(unittest.TestCase):
    
    connector=None
    client=None
 
    # prepare class for file transport from client to server
    def setUp(self):
        log.info(f"setUp")
        self.client = Client(config.API_URL, config.MAX_UPLOAD_BYTE_LENGHT)

    # delete all data from le_plants and data_batch table 
    def init_db(self):
        self.connector = DBConnector()
        del_str=f"delete from el_plants;"
        log.info(f'test_batch_init = {del_str}')
        cur = self.connector.execute_one(del_str)

        del_str=f"delete from data_batches;"
        log.info(f'test_batch_init = {del_str}')
        cur = self.connector.execute_one(del_str)
        self.connector.commit_all()

    # file transfer test, empty file.
    def test_01_file_content(self):
        self.init_db()
        in_file_path = os.path.join(TEST_DIR, 'data', 'simple.txt')
        self.client.upload_file(in_file_path)
        time.sleep(2) # Sleep for 3 seconds
        file_path = os.path.join(config.CSV_DIR, os.path.basename(in_file_path))
        with open(file_path, 'r') as f:
            self.assertEqual(f.read(), "simple text\\n")

    # direct test of load of data batch file
    def test_02_upload_file_func(self):

        file_path = os.path.join(TEST_DIR, 'data', '20201221-212549.csv')
        log.info(f"file_path in test_upload_file_func [{file_path}]")
        result = upload_batch(file_path)
        msg=f"file_path [{file_path}], data upload"
        self.assertTrue(result, msg=None)

    # upload of batch through server (self.client.upload_file(in_file_path)) containig duplicate records 
    def test_03_5exist_20new(self):
        in_file_path = os.path.join(TEST_DIR, 'data', 'my_test_batch1.csv')
        log.info(f"file_path [{in_file_path}]")
        self.client.upload_file(in_file_path)

        time.sleep(2) # Sleep for 3 seconds

        select_str="select num_of_suc_rec, num_of_failed_rec from data_batches"
        if self.connector == None:
            self.connector = DBConnector()
        cur = self.connector.execute_one(select_str)
        if cur != None:
            rows = cur.fetchall()
        if len(rows)==3:
            if rows[1][0] != 7:
                self.assertTrue(False, msg=f"Number of successfully loaded records {rows[1][0]} and should be 7")
                log.info(f"first batch num_of_suc_rec, num_of_failed_rec [{rows[1]}]")
            else:
                self.assertTrue(True, "Batches allright")

            if rows[2][0] != 19:
                self.assertTrue(False, msg=f"Number of successfully loaded records {rows[2][0]} and should be 19")
                log.info(f"first batch num_of_suc_rec, num_of_failed_rec [{rows[2]}]")
            else:
                self.assertTrue(True, "Batches allright")

            if rows[2][1] != 5:
                self.assertTrue(False, msg=f"Number of doplicated records {rows[2][1]} and should be 5")
                log.info(f"first batch num_of_suc_rec, num_of_failed_rec [{rows[2]}]")
            else:
                self.assertTrue(True, "Batches allright")

        else:
            self.assertTrue(False, msg=f"Number of batche is {len(rows)} and should be 3")            

    # test quey, confirms is the fields and rows are properly generated accoding with incomming parameters.
    def test_04_get_query(self):
        result_file_name = get_query( '2019-11-27 00:00:00 - 2019-11-27 24:00:00', 'dukovany, pocerady, temelin')
        os_file_name=f'{config.OUT_DIR}\\{result_file_name}'
        file_exists = path.isfile(os_file_name)
        # print(f"file_path [{result_file_name}] file_exists [{file_exists}]")
        num_of_rec = self.get_linecount(os_file_name)
        num_of_rec -= 1
        log.info(f' test_04_get_query count num_of_rec [{num_of_rec}]')
        self.assertTrue(file_exists, f"file_path [{os_file_name}] file_exists [{file_exists}]")

        self.assertTrue(num_of_rec==5, f"Number of slots returned {num_of_rec} should be 5")

    # additional test of dispaly functionality whith onli one plant data
    def test_05_get_query(self):
        result_file_name = get_query( '2019-11-28 00:00:00 - 2019-11-28 24:00:00', 'temelin')
        os_file_name=f'{config.OUT_DIR}\\{result_file_name}'
        file_exists = path.isfile(os_file_name)
        # print(f"file_path [{result_file_name}] file_exists [{file_exists}]")
        num_of_rec = self.get_linecount(os_file_name)
        num_of_rec -= 1
        log.info(f' test_04_get_query count num_of_rec [{num_of_rec}]')
        self.assertTrue(file_exists, f"file_path [{os_file_name}] file_exists [{file_exists}]")
        self.assertTrue(num_of_rec==2, f"Number of slots returned {num_of_rec} should be 2")
        num_of_fields = self.get_fieldscount(os_file_name)
        self.assertTrue(num_of_fields==3, f"Number of fileds {num_of_fields} should be 3")


    def get_linecount(self, file_name):
        with open( file_name, encoding='UTF-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                line_count += 1
        return line_count


    def get_fieldscount(self, file_name):
        with open( file_name, encoding='UTF-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_len=0
            prev_len=0
            line_count = 0
            for row in csv_reader:
                line_len = len(row)
                if line_count > 0 and  line_len != prev_len:
                    return line_len 

                prev_len = line_len
                line_count += 1
        
        return line_len

        # Opening a file 
        file = open(file_name,"r") 
        counter = 0 
        # Reading from file 
        content = file.read() 
        colist = content.split("\n") 
          
        for i in colist: 
            if i: 
                counter += 1
        return counter


if __name__ == '__main__':
    if (config.TEST_MODE == True):
        # tests are started with pedefined oreder test_01.., test_02 -- test_05
        unittest.main(failfast=True, exit=False)
    else:
        print ("config.TEST_MODE has to set to True in config.py to enable test mode.")

