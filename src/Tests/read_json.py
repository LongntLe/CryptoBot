import json
from os.path import getmtime
import time

WATCHED_FILES = './src/Backend/params.json'
watched_files_mtimes = [(WATCHED_FILES, getmtime(WATCHED_FILES))]


def check_file_change():
    global watched_files_mtimes
    for f, mtime in watched_files_mtimes:
        #print(f, mtime)
        if getmtime(f) > mtime:
            watched_files_mtimes = [(f, getmtime(f))]
            with open('./src/Backend/params.json') as f:
                data = json.load(f)
    
                print (data['take_profit'], data['stop_loss'])
                
                return
                
while True:
    check_file_change()
    time.sleep(5)
