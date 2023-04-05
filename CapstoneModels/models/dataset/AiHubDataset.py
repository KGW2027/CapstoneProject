import math
from collections import defaultdict

import torch
from torch.utils.data import Dataset
from tqdm import tqdm

import GraphGenerator
from models import DatasetManager
from models.dataset import AiHubProcessor


def generate_SNS_dataset(tokenizer, use_ratio: float = 0.3, lm_mode:bool = True):
    datas = AiHubProcessor.load_aihub_sns()

    train = []
    dev = []
    test = []

    print(f'data set ratio : {use_ratio}')

    for key, sep in datas.items():
        length = math.ceil(len(sep) * use_ratio)
        train_cut = math.ceil(length * 0.8)
        dev_cut = math.ceil(length * 0.9)
        train = train + sep[0:train_cut]
        dev = dev + sep[train_cut + 1:dev_cut]
        test = test + sep[dev_cut + 1:length]

    train = AiHubKoreanSNSDataset(train, tokenizer, 'sns-train', lm_mode=lm_mode)
    dev = AiHubKoreanSNSDataset(dev, tokenizer, 'sns-dev', lm_mode=lm_mode)
    test = AiHubKoreanSNSDataset(test, tokenizer, 'sns-test', lm_mode=lm_mode)
    return {'train': train, 'dev': dev, 'test': test}


class AiHubKoreanSNSDataset(Dataset):
    def __init__(self, corpus, tokenizer, sid:str, use_cache:bool = True, lm_mode:bool = True, max_length: int = 64):
        self.corpus = None
        self.weight = None
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.use_cache = use_cache
        self.sid = sid
        self.lm = lm_mode

        if self.corpus is None:
            if lm_mode:
                self.sid += '-lm'
                self.load_LM(corpus)
            else:
                self.load_data(corpus)

    def load_data(self, corpus):
        if self.use_cache:
            self.corpus = DatasetManager.load_dataset_ckpt(self.sid)
            self.weight = DatasetManager.load_dataset_weight(self.sid)

        if self.corpus is None:
            self.corpus = []
            print(f"Make Dataset - SNS-{self.sid}")
            weight = [0]*20
            for contexts in tqdm(corpus):
                for dialogue in contexts['dialogue']:
                    tokens = self.tokenizer.encode(dialogue[1])
                    token_len = len(tokens)
                    if token_len > self.max_length:
                        continue

                    attention_mask = [1] * token_len + [0] * (64 - token_len)
                    tokens += [0] * (64 - token_len)
                    age = contexts['participant'][str(dialogue[0])]
                    labels = [0] * 20
                    labels[age] = 1
                    weight[age] += 1
                    self.corpus.append([tokens, attention_mask, labels])
            total = sum(weight)
            self.weight = [w / total for w in weight]
            DatasetManager.save_dataset_ckpt(self.sid, self.corpus)
            DatasetManager.save_dataset_weight(self.sid, self.weight)

    def load_LM(self, corpus):
        if self.use_cache:
            self.corpus = DatasetManager.load_dataset_ckpt(self.sid)

        if self.corpus is None:
            self.corpus = []
            print(f"Make Dataset - SNS-{self.sid}")
            lengths = defaultdict(int)
            for contexts in tqdm(corpus):
                for dialogue in contexts:
                    tokens = self.tokenizer.encode(dialogue)
                    token_len = len(tokens)
                    lengths[math.ceil(token_len/64)] += 1
                    if token_len > self.max_length:
                        continue

                    attention_mask = [1] * token_len + [0] * (self.max_length - token_len)
                    tokens += [0] * (self.max_length - token_len)
                    self.corpus.append([tokens, attention_mask])
            print(f'\n\n{self.sid}')
            for idx in range(len(lengths)):
                print(f'{idx} : {lengths[idx]}')
            GraphGenerator.generate_tokens_length(lengths, name=self.sid)
            DatasetManager.save_dataset_ckpt(self.sid, self.corpus)
        print(f'{self.sid} data-set count : {len(self.corpus)}')


    def get_weight(self):
        return torch.tensor(self.weight, dtype=torch.float64)

    def __getitem__(self, index):
        data = self.corpus[index]
        input_ids = torch.tensor(data[0], dtype=torch.int32).cuda()
        attention_mask = torch.tensor(data[1], dtype=torch.int32).cuda()
        if self.lm:
            return {'input_ids': input_ids, 'attention_mask': attention_mask}

        label = torch.tensor(data[2], dtype=torch.float32).cuda()
        return {'input_ids': input_ids, 'attention_mask': attention_mask}, label

    def __len__(self):
        return len(self.corpus)