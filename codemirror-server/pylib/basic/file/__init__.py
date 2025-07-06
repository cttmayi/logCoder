import csv
import json
import gzip
from pylib.basic.file.log_parser import auto_parser, set_auto_parser


def file_name_extension(file_name, extension):
    if not extension.startswith('.'):
        extension = '.' + extension

    if file_name.endswith(extension):
        return file_name
    return file_name + extension
    # 


def file_read(data_path):
    if data_path.endswith('.gz'):
        return gzip_read(data_path)
    elif data_path.endswith('.jsonl'):
        return jsonl_read(data_path)
    elif data_path.endswith('.json'):
        return json_read(data_path)
    elif data_path.endswith('.csv'):
        return csv_read(data_path)
    elif data_path.endswith('.log'):
        return log_read(data_path)
    return None



def csv_read(data_path):
    data_path = file_name_extension(data_path, 'csv')
    with open(data_path, mode='r', encoding='utf-8') as file:
        # 创建一个csv读取器
        csv_reader = csv.reader(file)
        
        rows = []
        for l, row in enumerate(csv_reader):
            if l == 0:
                headers = row
                continue
            row_dict = dict(zip(headers, row))
            rows.append(row_dict)
        return rows
    return None


def csv_write(data_path, data, header=None):
    data_path = file_name_extension(data_path, 'csv')
    with open(data_path, mode='w', encoding='utf-8') as file:
        csv_writer = csv.writer(file)

        if header is None:
            header = data[0].keys()
        csv_writer.writerow(header)

        for row in data:
            row = [row[key] for key in header]
            csv_writer.writerow(row)


def jsonl_read(data_path):
    data_path = file_name_extension(data_path, 'jsonl')
    with open(data_path, mode='r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]
        return data
    return None


def jsonl_write(data_path, data):
    data_path = file_name_extension(data_path, 'jsonl')
    with open(data_path, mode='w', encoding='utf-8') as file:
        for row in data:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')


def log_read(data_path):
    with open(data_path, mode='r', encoding='utf-8') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]
        data, type = auto_parser(lines)
        return data, type
    return None, None


def log_set_auto_parser(type, regex, parser_or_header):
    set_auto_parser(type, regex, parser_or_header)


def json_read(data_path):
    data_path = file_name_extension(data_path, 'json')
    with open(data_path, mode='r', encoding='utf-8') as file:
        loaded_data = json.load(file)
        return loaded_data
    return None


def json_write(data_path, data):
    data_path = file_name_extension(data_path, 'json')
    with open(data_path, mode='w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def gzip_read(data_path):
    data_path = file_name_extension(data_path, 'json.gz')
    with gzip.open(data_path, "rt", encoding="utf-8") as f:
        loaded_data = json.load(f)
        return loaded_data

def gzip_write(data_path, data):
    data_path = file_name_extension(data_path, 'json.gz')
    with gzip.open(data_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 加载数据
