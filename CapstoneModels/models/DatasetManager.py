import json
import os.path


dir_prefix = 'G:/Dataset-ckpt/'
weight_suffix = '-weight'
file_suffix = '.json'

def is_exist(name):
    os.makedirs(dir_prefix, exist_ok=True)
    path = f'{dir_prefix}{name}{file_suffix}'
    if os.path.exists(path):
        return path
    return None

def load_dataset_ckpt(name):
    file = is_exist(name)
    if file is not None:
        with open(file, 'r', encoding='utf-8') as ckpt_file:
            print(f'load_dataset-{name}')
            return json.load(ckpt_file)
    return None

def load_dataset_weight(name):
    file = is_exist(f'{name}{weight_suffix}')
    if file is not None:
        with open(file, 'r', encoding='utf-8') as weight_file:
            return json.load(weight_file)
    return None

def save_dataset_ckpt(name, value, indent:str = ' '):
    os.makedirs(dir_prefix, exist_ok=True)
    path = f'{dir_prefix}{name}{file_suffix}'
    with open(path, 'w+', encoding='utf-8') as ckpt_file:
        print(f'save_dataset-{name} -> {len(str(value)):,3} Chars')
        if indent == '':
            json.dump(value, ckpt_file)
        else:
            json.dump(value, ckpt_file, ensure_ascii=False, indent=indent)

def save_dataset_weight(name, value):
    os.makedirs(dir_prefix, exist_ok=True)
    path = f'{dir_prefix}{name}{weight_suffix}{file_suffix}'
    with open(path, 'w+', encoding='utf-8') as weight_file:
        json.dump(value, weight_file, ensure_ascii=False, indent=' ')
