import pandas as pd
import os
import logging
import helper.lparser.conf as conf


PATH = 'work_dir/debug'


if conf.DEBUG:
    os.makedirs(PATH, exist_ok=True)
    log_file = os.path.join(PATH, 'debug.log')
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

def file(value, file_name):
    if conf.DEBUG:
        if isinstance(value, pd.DataFrame):
            value.to_csv(os.path.join(PATH, file_name + '.csv'), index=False, encoding='utf-8-sig', )

