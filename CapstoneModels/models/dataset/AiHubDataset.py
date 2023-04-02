import torch
from torch.utils.data import Dataset
from tqdm import tqdm

from models import DatasetManager


class AiHubKoreanSNSDataset(Dataset):
    def __init__(self, corpus, tokenizer, sid:str, use_cache:bool = True):
        self.corpus = None
        self.weight = None
        self.tokenizer = tokenizer
        self.max_length = 64
        needSave = False

        if use_cache:
            self.corpus = DatasetManager.load_dataset_ckpt(sid)
            self.weight = DatasetManager.load_dataset_weight(sid)

        if self.corpus is None:
            self.corpus = []
            needSave = True
            print(f"Make Dataset - SNS-{sid}")
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

        if use_cache and needSave:
            DatasetManager.save_dataset_ckpt(sid, self.corpus)
            DatasetManager.save_dataset_weight(sid, self.weight)

    def get_weight(self):
        return torch.tensor(self.weight, dtype=torch.float64)

    def __getitem__(self, index):
        data = self.corpus[index]
        input_ids = torch.tensor(data[0], dtype=torch.int32).cuda()
        attention_mask = torch.tensor(data[1], dtype=torch.int32).cuda()
        label = torch.tensor(data[2], dtype=torch.float32).cuda()
        return {'input_ids': input_ids, 'attention_mask': attention_mask}, label

    def __len__(self):
        return len(self.corpus)