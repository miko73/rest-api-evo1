import os
import re
import sys
import csv
import logging


import config
from bottle import Bottle, request, response, BaseRequest, route, post
from models import DBConnector, Batch, Reporter
from parse_data import load_batch, get_query
from json import dumps


BaseRequest.MEMFILE_MAX = config.MAX_UPLOAD_BYTE_LENGHT

app = Bottle()


#file_handler = logging.FileHandler(f"{config.LOG_DIR}/app.log")
#app.logger.addHandler(file_handler)
#app.logger.setLevel(logging.INFO)


post_template = """
<html>
<body>
<form action="/upload_file" method="post" enctype="multipart/form-data">
  Category:      <input type="text" name="category" />
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
@app.route('/upload_file', method='POST')
def upload_file_on_form_post():
	category   = request.forms.get('category')
	upload     = request.files.get('upload')
	name, ext = os.path.splitext(upload.filename)
	print (f'name {name}, ext {ext}')
	file_path=f'{config.CSV_DIR}\\{name}{ext}'	
	try:
		upload.save(config.CSV_DIR) # appends upload.filename automatically
	except IOError as e:		
		return f"File exists {file_path}"

	load_batch(file_path)
	return 'OK'

"""
retrun to client page with file upload functionality
"""
@app.route('/upload_file', method='GET')
def upload_file_on_form_get():
   return post_template


"""
This function is server part of uploader client. 
"""
@app.route('/store', method='POST')
def upload():
	range_header = request.headers.get('Range')
	match = re.search('(?P<start>\d+)-(?P<end>\d+)/(?P<total_bytes>\d+)', range_header)
	start = int(match.group('start'))
	end = int(match.group('end'))
	total_bytes = int(match.group('total_bytes'))

	print ('in upload', request.body)

	file_name = os.path.basename(request.headers.get('Filename'))
	file_path = os.path.join(config.CSV_DIR, file_name)
	print (f'file_name in STORE {file_name}' )
	# append chunk to the file or create file if not exist
	with open(file_path, 'rb+' if os.path.exists(file_path) else 'wb+') as f:
		f.seek(start)
		act_chunk = request.body.read(config.MAX_UPLOAD_BYTE_LENGHT)
		f.write(act_chunk)
		if len (act_chunk) == config.MAX_UPLOAD_BYTE_LENGHT:
			print ("file to large")

		print("start={}, byte_len={}, pos={}".format(start, len(act_chunk), f.tell()))
	# data are saved to file  
	load_batch(file_path)
	response.status = 200
	return response

@app.route('/display', method='GET')
def dispaly_get():
	output = ""
	if len (request.params) == 2:
		time_slot = request.params.get('time_slot')
		plants_list = request.params.get('plant_list')
		result_file_name = get_query(time_slot, plants_list)
		reslut_text=f"Successuflly uploaded {result_file_name}"
	else:
		reslut_text = "Parameters error. \n Use parameter in format like http://localhost:8082/display?time_slot='2020-05-01 20:00:00 - 2020-05-01 21:00:00'&plant_list='temelin,dukovany,pocerady'"	
		reslut_text += "<br>"
		reslut_text += back_button_templ
		return reslut_text

	response.content_type = 'text/csv'
	# read csv file

	csv_file = open(result_file_name, "r")
	allLines = csv_file.readlines()
	csv_file.close()
	print("File contents:", allLines)  #Prints the list of strings
#	return dumps(allLines)
	return allLines

@app.route('/x', method='GET')
def func_x():

	result_text=""	
	for item in request.forms:
		result_text += "forms [{}]{}".format(item, request.forms.get(item))

	for item in request.query:
		result_text+="<br> query [{}]{}".format(item,request.query.get(item))
	
	for item in request.GET:
		result_text+="<br> GET [{}]{}".format(item,request.GET.get(item))

	for item in request.POST:
		result_text+="<br> POST [{}]{}".format(item,request.POST.get(item))
	
	for item in request.params:
		result_text+="<br> params [{}]{}".format(item,request.params.get(item))

	return result_text





# if __name__ == '__main__':
    # run(app=app, host=config.HOST, port=config.PORT, debug=True)

if __name__ == "__main__":
	print("Starting")
	app.run(host=config.HOST, port=config.PORT, debug=True)
# run(host=config.HOST, port=config.PORT, debug=True)
