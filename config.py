import os

HOST = 'localhost'
PORT = 8082
APP_DIR = os.getcwd()
CSV_DIR = os.path.join(APP_DIR, 'csvs')
OUT_DIR = os.path.join(APP_DIR, 'out')
DB_DIR = os.path.join(APP_DIR, 'db')
LOG_DIR = os.path.join(APP_DIR, 'log')
MAX_UPLOAD_BYTE_LENGHT = 1024 * 1024  # 1M
API_URL = 'http://{}:{}'.format(HOST, PORT)

