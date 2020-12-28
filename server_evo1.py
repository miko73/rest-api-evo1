import os
import re
import sys
import csv
#app config
import config
#log module
import logging
# server
from bottle import Bottle, request, response, BaseRequest, route, post, static_file
# app classes
from models import DBConnector, Batch, Reporter
# connecting functions
from parse_data import upload_batch, get_query
import requests

# BaseRequest.MEMFILE_MAX = config.MAX_UPLOAD_BYTE_LENGHT

app = Bottle()
log_file= f'{config.LOG_DIR}\\master.log'
logging.basicConfig(filename=log_file, level=config.LOG_LEVEL)

log = logging.getLogger("server_evo1")

# 
#file_handler = logging.FileHandler(f"{config.LOG_DIR}/app.log")
#app.logger.addHandler(file_handler)
#app.logger.setLevel(logging.INFO)


post_template = """
<html>
<body>
<form action="/upload_file" method="post" enctype="multipart/form-data">
  Select a file: <input type="file" name="upload" />
  <input type="submit" value="Start upload" />
</form> 
</body>
</html>"""

back_button_templ="""
<button onclick="goBack()">Go Back</button>
<script>
function goBack() {
  window.history.back();
}
</script>
"""

"""
read the file from browser on client opened by upload_file_on_form_get()
"""

"""
when file selected in browser page, uploads file to server
"""
@app.route('/upload_file', method='POST')
def upload_file_on_form_post():
	upload     = request.files.get('upload')
	name, ext = os.path.splitext(upload.filename)
	log.debug (f'name {name}, ext {ext}')
	file_path = f'{config.CSV_DIR}\\{name}{ext}'	

	if os.path.exists(file_path):
		log.debug("removing file in upload_file_on_form_post")
		os.remove(file_path)

	try:
		upload.save(config.CSV_DIR) # appends upload.filename automatically
	except IOError as e:		
		return f"File exists {file_path}"
	# parse incomming date and store to DB (interface between server nad class structure)
	result = upload_batch(file_path)
	log.info (f"Batch stored {result}")
	return result.replace('\n', '<br>') 

"""
retrun to client page with file upload functionality
"""
@app.route('/upload_file', method='GET')
def upload_file_on_form_get():
   return post_template


"""
This function is server part of uploader client. (comand line client/server interface) 
"""
@app.route('/store', method='POST')
def upload():
	range_header = request.headers.get('Range')
	match = re.search('(?P<start>\d+)-(?P<end>\d+)/(?P<total_bytes>\d+)', range_header)
	
	start = int(match.group('start'))
	end = int(match.group('end'))
	total_bytes = int(match.group('total_bytes'))


	file_name = os.path.basename(request.headers.get('Filename'))
	file_path = os.path.join(config.CSV_DIR, file_name)
	log.debug (f'file_name in STORE [{file_name}]' )
	if os.path.exists(file_path) and start==0:
		log.debug("removing file in upload")
		os.remove(file_path)
	# append chunk to the file or create file if not exist
	with open(file_path, 'rb+' if os.path.exists(file_path) else 'wb+') as f:
		f.seek(start)
		act_chunk = request.body.read(config.MAX_UPLOAD_BYTE_LENGHT)
		f.write(act_chunk)
		if len (act_chunk) == config.MAX_UPLOAD_BYTE_LENGHT:
			log.debug ("file to large")

		log.debug("start={}, byte_len={}, pos={}".format(start, len(act_chunk), f.tell()))

	# data are saved to file
	if total_bytes == end:	
		# log.info (f"batch file successfully stored {file_path}")
		result = upload_batch(file_path)
		log.info (f"Batch stored {result}")
		return result.replace('\n', '<br>')

	response.status = 200
	return response


"""
received the user request for date according with spefication

"""
@app.route('/display', method='GET')
def dispaly_get():
	output = ""
	if len (request.params) == 2:
		time_slot = request.params.get('time_slot')
		plants_list = request.params.get('plant_list')
		result_file = get_query(time_slot, plants_list)			
		os_file_name = f'{config.OUT_DIR}\\{result_file}'
		reslut_text=f"Successuflly uploaded {os_file_name}"
	else:
		reslut_text = "Parameters error. \n Use parameter in format like http://localhost:8082/display?time_slot='2020-05-01 20:00:00 - 2020-05-01 21:00:00'&plant_list='temelin,dukovany,pocerady'"	
		reslut_text += "<br>"
		reslut_text += back_button_templ
		return reslut_text
	log.debug(reslut_text)
	folder_name = f'{config.OUT_DIR}\\'
	
	if os.path.exists(os.path.join(folder_name, result_file)):
		return static_file(os_file_name, root=folder_name)


if __name__ == "__main__":

	# log.debug('Debug message, should only appear in the file.')
	# log.info('Info message, should appear in file and stdout.')
	# log.warning('Warning message, should appear in file and stdout.')
	# log.error('Error message, should appear in file and stdout.')
	port = int(config.PORT)
	if (config.TEST_MODE == True):
		log.warning("!!!!! Server Started in test mode !!!!!.")


	app.run(host=config.HOST, port=port, debug=True)
