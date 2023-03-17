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
        sentence = GameLanguage.replace(sentence)
        if len(sentence) > 256:
            for splited in sentence.split(". "):
                self.train_sentences.append(splited)
        else:
            self.train_sentences.append(sentence)

    def load_translated(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
            for text in json_file:
                start_with_num = re.match(r"^[0-9] ", text)
                if start_with_num and re.search(r" [0-9]\.[0-9] ", text):
                    continue
                elif 'riot games' in text:
                    continue
                else:
                    self.add_sentence(text)


    def load_def(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
            for texts in json_file:
                texts = texts['data']['Header']
                for text in texts:
                    if len(text) < 10 or len(text.split(" ")) < 3:
                        continue
                    else:
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



    def pretrain(self):
        train01_dir = "../data_crawler/data/univ_ko/Univ-Ko.json"
        train02_dir = "../data_crawler/data/FandomEnTranslated/Fandom-EnKo.json"
        train03_dir = "../data_crawler/data/UniverseEnTranslated/Univ-EnKo.json"

        self.load_def(train01_dir)
        self.load_translated(train02_dir)
        self.load_translated(train03_dir)

        self.dataset = GameDataset(self.tokenizer, self.train_sentences)
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=True, mlm_probability=0.15)
        train_args = TrainingArguments(output_dir='../ptunning/kogpt_lol_ckpt', num_train_epochs=5,
                                       per_device_train_batch_size=self.batch_size, per_gpu_train_batch_size=self.batch_size,
                                       warmup_steps=40000, weight_decay=0.01, save_steps=40000)
        trainer = Trainer(model=self.model, args=train_args, data_collator=data_collator, train_dataset=self.dataset)

        self.clean()
        self.model = self.model.cuda()
        trainer.train()

        save_path = '../ptunning/kogpt_lol_complete'
        trainer.save_model(save_path)
        self.tokenizer.save_pretrained(save_path)


    def train(self):
        print('a')


    def test(self):
        print('b')


    def clean(self):
        gc.collect()
        torch.cuda.empty_cache()


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


    def __init__(self):

        self.train_sentences = []

        self.max_length = 64
        self.batch_size = 4
        self.tokenizer = None
        self.model = None
        self.dataset = None
        self.dataloader = None



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

