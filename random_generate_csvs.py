import random
import csv
from datetime import datetime
import logging
import config
import sys

log_file= f'{config.LOG_DIR}\\random_generate_csvs.log'
logging.basicConfig(filename=log_file, level=config.LOG_LEVEL)
log = logging.getLogger("random_generate.py")

def get_random_date(year):

	# try to get a date
	try:
		return datetime.strptime('{} {} {}'.format(random.randint(1, 366), year, random.randint(0,23)), '%j %Y %H')
	# if the value happens to be in the leap year range, try again
	except ValueError:
		get_random_date(year)

def get_random_line():
	year = random.randrange(2018, 2021) 
	date = get_random_date(year)
	utc_timestamp = f'{date}'
	
	installed_rand = random.randrange(0,2)
	temelin_actual = random.randrange(2045, 2445)
	temelin_installed = installed_rand*100 + 2500

	dukovany_actual = random.randrange(1300, 1900)
	dukovany_installed = installed_rand*100 + 1900

	pocerady_actual = random.randrange(500, 800)
	pocerady_installed = installed_rand*100 + 800
	return f'{utc_timestamp},{temelin_actual},{temelin_installed},{dukovany_actual},{dukovany_installed}, {pocerady_actual},{pocerady_installed}' 


def prepre_input(file_name, count):	
	log.debug (f"'prepare_report {file_name}'")
	with open(file_name , mode='w', newline='', encoding='UTF-8') as csv_stack:
		csv_writer = csv.writer(csv_stack, delimiter=',', quotechar="", quoting=csv.QUOTE_NONE)
		# log.debug(f'header  {self.field_list.split(",")}')
		row = "utc_timestamp,temelin_actual,temelin_installed,dukovany_actual,dukovany_installed, pocerady_actual,pocerady_installed".split(",")
		log.debug (row)
		csv_writer.writerow(row)			
		for x in range (count):
			row=get_random_line().split(",")
			csv_writer.writerow(row)

			

file_name = f'{config.APP_DIR}\\tests\\data\\'
file_name += datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'
#nuber records in batch, file name is generated 

if __name__ == '__main__':

    try:
        rows_count = int(sys.argv[1])
    except IndexError:
        TEST_DIR = os.path.join(config.APP_DIR, 'tests')
        file_path = os.path.join(TEST_DIR, 'data', 'simple.txt')
    log.info(f'file_name [{file_name}], rows_count = [{rows_count}]')
    prepre_input(file_name, rows_count)






# utc_timestamp,temelin_actual,temelin_installed,dukovany_actual,dukovany_installed, pocerady_actual,pocerady_installed
# 2020-05-01 12:00:00, 2345,2600, 1870, 2020, 700, 1000
# 2020-05-01 14:00:00, 2235,2600, 1900, 2020, 768, 1000
