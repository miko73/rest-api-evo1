import os
import sys
import logging
import config
log_file= f'{config.LOG_DIR}\\uploader.log'

logging.basicConfig(filename=log_file, level=config.LOG_LEVEL)
log = logging.getLogger("uploader.py")


from client import Client

if __name__ == '__main__':
    client = Client(config.API_URL, config.MAX_UPLOAD_BYTE_LENGHT)

    try:
        file_path = sys.argv[1]
    except IndexError:
        TEST_DIR = os.path.join(config.APP_DIR, 'tests')
        file_path = os.path.join(TEST_DIR, 'data', 'simple.txt')

    log.debug(f'Uploading file:{file_path}')
    client.upload_file(file_path)
