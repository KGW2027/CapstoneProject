import json
import math
import os
from collections import defaultdict

from torch.utils.data import Dataset
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

    def get_tags(self):
        return []

    def getName(self):
        return None

    def process(self, data):
        return None

    def get(self):
        return self.train, self.dev

    def formatting(self, prev_text, ag_value, next_text):
        return f'{prev_text}{self.ag_token}{ag_value}{self.response_token}{next_text}'

    def tokens(self):
        return []


class UnsupervisedDataset(Dataset):
    def __init__(self, tokenizer, corpus=None, name:str = 'aglm_train', max_length:int = 128, stride: int = 32):
        self.corpus = DatasetManager.load_dataset_ckpt(name)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.pad_token = self.tokenizer(self.tokenizer.pad_token)['input_ids'][0]

        if self.corpus is None:
            self.corpus = []
            for value in tqdm(corpus):
                for context in value:
                    if type(context) is not str:
                        continue
                    tokens = self.tokenizer(context)
                    length = len(tokens['input_ids'])

                    adds = []
                    if length <= self.max_length:
                        adds.append(self.padding(tokens['input_ids']))
                    else:
                        # Sliding Window
                        end_length = self.max_length
                        while length > end_length:
                            adds.append(self.padding(tokens['input_ids'][end_length-self.max_length:end_length]))
                            end_length += stride
                        adds.append(self.padding(tokens['input_ids'][end_length-self.max_length:end_length]))

                    self.corpus += adds
            DatasetManager.save_dataset_ckpt(name, self.corpus, indent='')

    def __getitem__(self, item):
        return self.corpus[item]

    def __len__(self):
        return len(self.corpus)

    def padding(self, tokens):
        length = len(tokens)
        remain = self.max_length - length
        input_ids = tokens + ([self.pad_token] * remain)
        attention_mask = [1] * length + [0] * remain
        return {'input_ids': input_ids, 'attention_mask': attention_mask}

class SummarizeDataset(Dataset):
    def __init__(self, tokenizer, corpus=None, name:str='summarize_aihub', context_max_length:int = 512, answer_max_length:int = 128, stride: int = 32):
        self.corpus = DatasetManager.load_dataset_ckpt(name)

        if self.corpus is None:
            self.corpus = []
            for value in tqdm(corpus):
                context = value['context']
                inputs = tokenizer(f'summarize: {context}', truncation=True, max_length=context_max_length, padding="max_length")
                for output in value['summaries']:
                    label = tokenizer(output, truncation=True, max_length=answer_max_length, padding="max_length")
                    data = {
                        'input_ids': inputs['input_ids'],
                        'attention_mask': inputs['attention_mask'],
                        'label_ids': label['input_ids'],
                        'label_attention_mask': label['attention_mask'],
                    }
                    self.corpus.append(data)
            DatasetManager.save_dataset_ckpt(name, self.corpus, indent='')

    def __getitem__(self, item):
        return self.corpus[item]

    def __len__(self):
        return len(self.corpus)