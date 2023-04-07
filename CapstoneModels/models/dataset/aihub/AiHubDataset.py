from torch.utils.data import Dataset
from tqdm import tqdm

from models import DatasetManager


class AiHub20Dataset(Dataset):
    def __init__(self, corpus, tokenizer, train_mode: bool = True):

        name = 'ai_hub_20-' + ('train' if train_mode else 'dev')
        self.corpus = DatasetManager.load_dataset_ckpt(name)
        self.tokenizer = tokenizer
        self.max_length = 64

        if self.corpus is None:
            self.corpus = []
            for value in tqdm(corpus):
                for context in value:
                    if len(self.tokenizer(context)['input_ids']) > self.max_length:
                        continue
                    self.corpus.append(context)
            DatasetManager.save_dataset_ckpt(name, self.corpus)

    def __getitem__(self, item):
        context = self.tokenizer(self.corpus[item], padding="max_length", truncation=True, max_length=self.max_length, return_tensors='pt')
        return context

    def __len__(self):
        return len(self.corpus)