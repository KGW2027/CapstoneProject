import gc
import json
import math
import os
import random
from collections import defaultdict

import torch
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

def padding(tokens, max_length:int, pad_token:int):
    length = len(tokens)
    remain = max_length - length
    input_ids = tokens + ([pad_token] * remain)
    attention_mask = [1] * length + [0] * remain
    return {'input_ids': input_ids, 'attention_mask': attention_mask}


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


class UnsupervisedDatasetWithLabel(Dataset):
    def add_all(self, array:list):
        for value in array:
            if type(value) is list:
                self.add_all(value)
            else:
                self.corpus.append(value)

    def __init__(self, tokenizer, corpus=None):
        self.corpus = []
        self.add_all(corpus)
        self.tokenizer = tokenizer

    def __getitem__(self, item):
        value = self.corpus[item]
        tokenize = self.tokenizer(value, max_length=512, padding="max_length", truncation=True)
        return {'input_ids': torch.tensor(tokenize['input_ids']), 'attention_mask': torch.tensor(tokenize['attention_mask']), 'labels': torch.tensor(tokenize['input_ids'])}

    def __len__(self):
        return len(self.corpus)


class UnsupervisedDataset(Dataset):
    def add_all(self, array: list):
        for value in array:
            if type(value) is list:
                self.add_all(value)
            else:
                self.corpus.append(value)

    def __init__(self, tokenizer, corpus=None):
        self.corpus = []
        self.add_all(corpus)
        self.tokenizer = tokenizer

    def __getitem__(self, item):
        value = self.corpus[item]
        tokenize = self.tokenizer(value, max_length=384, padding="max_length", truncation=True)
        return {'input_ids': torch.tensor(tokenize['input_ids']),
                'attention_mask': torch.tensor(tokenize['attention_mask']),
                'labels': torch.tensor(tokenize['input_ids'])}

    def __len__(self):
        return len(self.corpus)

class SummarizeDataset(Dataset):
    def __init__(self, tokenizer, corpus=None, context_max_length:int = 512, answer_max_length:int = 128):
        self.corpus = corpus
        self.tokenizer = tokenizer
        self.max_length = [context_max_length, answer_max_length]

    def __getitem__(self, item):
        value = self.corpus[item]
        context = value['context']
        summaries = value['summaries']

        inputs = self.tokenizer(f'summarize_summary: {context}', truncation=True, max_length=self.max_length[0], padding="max_length")
        if type(summaries) is list:
            summaries = summaries[1]

        label = self.tokenizer(summaries, truncation=True, max_length=self.max_length[1], padding="max_length")
        return {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
            'labels': label['input_ids'],
            # 'label_attention_mask': label['attention_mask'],
        }

    def __len__(self):
        return len(self.corpus)