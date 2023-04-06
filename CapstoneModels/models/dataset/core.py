import json
import os

from tqdm import tqdm

from models import DatasetManager


def getPath(name:str, train_suffix:str = '', dev_suffix:str = ''):
    parent = f'G:/Datasets/{name}/'
    return parent+train_suffix, parent+dev_suffix

def getFiles(path:str):
    files = []
    for fname in os.listdir(path):
        file = path + '/' + fname
        if os.path.isfile(file):
            files.append(file)
        elif os.path.isdir(file):
            files += getFiles(file)
    return files


class DataProcessor:
    def __init__(self):
        self.train = []
        self.dev = []
        self.sep_token = '<s>'
        self.response_token = '<response>'
        self.ag_token = '<ag>'

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = True):
        train, valid = getPath(self.getName())
        self.internal_load(getFiles(f'{train}/{train_suffix}'), self.train)
        if load_dev:
            self.internal_load(getFiles(f'{valid}/{dev_suffix}'), self.dev, train_mode=False)

    def internal_load(self, files: list, array: list, train_mode: bool = True, save_cache: bool = True, load_cache: bool = True):
        mode = 'train' if train_mode else 'dev'

        if load_cache:
            load = DatasetManager.load_dataset_ckpt(f'{self.getName()}-{mode}')
            if load is not None:
                print('load dataset cache')
                if train_mode:
                    self.train += load
                else:
                    self.dev += load
                return None


        for file_name in tqdm(files):
            with open(file_name, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                process = self.process(data)
                if process is None:
                    continue
                array.append(process)

        if save_cache:
            DatasetManager.save_dataset_ckpt(f'{self.getName()}-{mode}', array)

    def getName(self):
        return None

    def process(self, data):
        return None

    def get(self):
        return self.train, self.dev

    def formatting(self, prev_text, ag_value, next_text):
        return f'{prev_text}{self.ag_token}{ag_value}{self.response_token}{next_text}'