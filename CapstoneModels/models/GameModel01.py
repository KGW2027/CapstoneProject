import collections
import gc
import json
import math
import re

import torch.cuda
from torch.utils.data import Dataset
from tqdm import tqdm
from transformers import DataCollatorForLanguageModeling, TrainingArguments, Trainer, AutoTokenizer, \
    AutoModelForCausalLM

import GameLanguage
import GraphGenerator


class GameLolModel_t1:

    def add_sentence(self, sentence):
        self.train_sentences.append(sentence)

    def load_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
            for text in json_file:
                self.add_sentence(text)

    def load_model(self, path: str = None):
        if path is None:
            model_name = 'skt/kogpt2-base-v2'
            self.tokenizer = AutoTokenizer.from_pretrained(model_name,
                                                      bos_token='</s>',
                                                      eos_token='</s>',
                                                      unk_token='<unk>',
                                                      pad_token='<pad>',
                                                      mask_token='<mask>')
            self.model = AutoModelForCausalLM.from_pretrained(model_name, pad_token_id=self.tokenizer.eos_token_id)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(path,
                                                      bos_token='</s>',
                                                      eos_token='</s>',
                                                      unk_token='<unk>',
                                                      pad_token='<pad>',
                                                      mask_token='<mask>')
            self.model = AutoModelForCausalLM.from_pretrained(path, pad_token_id=self.tokenizer.eos_token_id)



    def pretrain(self, num_epoch:int = 1, warm_up:int = 40000, save_step:int = 40000):

        self.dataset = GameDataset(self.tokenizer, self.train_sentences)
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=True, mlm_probability=0.15)
        train_args = TrainingArguments(output_dir='../ptunning/kogpt_lol_ckpt', num_train_epochs=num_epoch,
                                       per_device_train_batch_size=self.batch_size, per_gpu_train_batch_size=self.batch_size,
                                       warmup_steps=warm_up, weight_decay=0.001, save_steps=save_step, learning_rate=self.learning_rate)
        trainer = Trainer(model=self.model, args=train_args, data_collator=data_collator, train_dataset=self.dataset)

        self.clean()
        self.model = self.model.cuda()
        trainer.train()

        save_path = '../ptunning/kogpt_lol_complete'
        trainer.save_model(save_path)
        self.tokenizer.save_pretrained(save_path)

    def clean(self):
        gc.collect()
        torch.cuda.empty_cache()


    def add_train_data(self):
        train01_dir = "../data_crawler/data/univ_ko/Univ-Ko-process.json"
        train02_dir = "../data_crawler/data/FandomEnTranslated/Fandom-EnKo-DeepL-process.json"
        train03_dir = "../data_crawler/data/UniverseEnTranslated/Univ-EnKo-DeepL-process.json"
        self.load_data(train01_dir)
        self.load_data(train02_dir)
        self.load_data(train03_dir)


    def print_distribution(self):
        with tqdm(total=len(self.train_sentences), leave=False) as pbar:
            for text in self.train_sentences:
                token = self.tokenizer(text)
                length = len(token['input_ids'])
                if length > 256:
                    continue
                self.distribution[length] += 1
                pbar.update(1)

        print(self.distribution)
        GraphGenerator.generate_tokens_length(self.distribution)



    def generate_text(self, seed, max_length: int = 128, gen_seqs: int = 5):
        input_ids = self.tokenizer.encode(seed, return_tensors='pt')
        gen_ids = self.model.generate(
            input_ids,
            max_length=max_length,
            repetition_penalty=2.0,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            bos_token_id=self.tokenizer.bos_token_id,
            top_k=50,
            do_sample=True,
            num_return_sequences=gen_seqs
        )

        seqs = [self.tokenizer.decode(v) for v in gen_ids]
        return seqs


    def __init__(self, max_length:int = 128, batch_size:int = 4, l_rate:float = 5):

        self.train_sentences = []

        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = l_rate
        self.tokenizer = None
        self.model = None
        self.dataset = None
        self.dataloader = None

        self.distribution = collections.defaultdict(int)



class GameDataset(Dataset):
    def __init__(self, tokenizer, datas: list, max_length: int = 128):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = datas

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        tokenize = self.tokenizer(self.data[idx], padding="max_length", truncation=True, max_length=self.max_length, return_tensors='pt')
        tokenize['input_ids'] = tokenize['input_ids'].squeeze(0).cuda()
        tokenize['attention_mask'] = tokenize['attention_mask'].squeeze(0).cuda()
        return {'input_ids': tokenize['input_ids'], 'attention_mask': tokenize['attention_mask']}

