import csv
import math
import os
import re

from torch.utils.data import Dataset
from transformers import AutoTokenizer, T5ForConditionalGeneration, TrainingArguments, \
    Trainer, DataCollatorForSeq2Seq

from experiments.Datasets import GameDialogueDataset
from models import DatasetManager, ModelManager
from models.dataset.core import UnsupervisedDataset


class MoreTrainT5:
    tokenizer = None
    model = None
    def __init__(self):
        self.load()

    def load(self, model_path:str = 'KETI-AIR/ke-t5-base'):
        if model_path != 'KETI-AIR/ke-t5-base':
            model_path = ModelManager.load(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)

    def dataset(self):
        ckpts = [
            'game_augments',
            'game_summarizes',
            'gpt2_augment',
            'fandom-lol-train',
            'univ-lol-train'
        ]
        datasets = []
        for ckpt in ckpts:
            dsm = DatasetManager.load_dataset_ckpt(ckpt)
            if type(dsm[0]) is list:
                dsm = dsm[0]
            datasets += dsm

        cut = math.floor(len(datasets)*0.9)
        return datasets[:cut], datasets[cut:]

    def pre_train(self):
        self.load()
        t, d = self.dataset()

        trains = UnsupervisedDataset(tokenizer=self.tokenizer, corpus=t)
        dev = UnsupervisedDataset(tokenizer=self.tokenizer, corpus=d)
        data_collator = DataCollatorForSeq2Seq(tokenizer=self.tokenizer, model=self.model, max_length=128, padding='max_length', return_tensors='pt')

        train_args = TrainingArguments(
            adafactor=True,
            output_dir='G:/trains/train_game',
            per_device_train_batch_size=2,
            gradient_accumulation_steps=16,
            num_train_epochs=1,

            learning_rate=1e-6,
            weight_decay=0.01,
            warmup_steps=2000,
            warmup_ratio=0.02,

            do_eval=True,
            eval_steps=1000,
            save_steps=1000,
            save_total_limit=3,
            logging_steps=500,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=trains,
            eval_dataset=dev,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        trainer.train(resume_from_checkpoint=True)
        ModelManager.save(self.model, self.tokenizer, 'train_game')

    def pretrain_test(self):
        self.load('train_game')
        t, d = self.dataset()
        for idx in range(5):
            context = f'dialogue_a2_gf : {d[idx]}'
            print(f'Context : {context}')
            token = self.tokenizer.encode(context, return_tensors='pt')
            output_tokens = self.model.generate(
                token,
                max_length=256,
                # num_beams=5,
                # no_repeat_ngram_size=2,

                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                top_k=10,
                num_return_sequences=3,

                early_stopping=True,
            )
            for output in output_tokens:
                decodes = self.tokenizer.decode(output, skip_special_tokens=True)
                print(decodes)

    def train_dialogue(self, new_train:bool = True):
        path = 'train_game' if new_train else f'train_dialogue'
        self.load(path)
        trains = GameDialogueDataset(self.tokenizer)
        data_collator = DataCollatorForSeq2Seq(tokenizer=self.tokenizer, model=self.model, max_length=256, padding='max_length', return_tensors='pt')

        train_args = TrainingArguments(
            # adafactor=True,
            output_dir='G:/trains/train_dialogue',
            per_device_train_batch_size=4,
            gradient_accumulation_steps=8,
            num_train_epochs=20,

            learning_rate=1e-4,
            weight_decay=0.01,
            # warmup_steps=2000,
            # warmup_ratio=0.02,

            save_steps=300,
            save_total_limit=3,
            logging_steps=100,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=trains,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        trainer.train()
        ModelManager.save(self.model, self.tokenizer, 'train_dialogue')

    def test_dialogue(self, question:str, age:int = 2, is_male:bool = True):
        self.load('train_dialogue')
        gender = 0 if is_male else 1
        input_text = f'talk_g{gender}_a{age}_f0_n5 : {question}'

        print(f'Prompt ->\t{input_text}')

        inputs = self.tokenizer.encode(input_text, return_tensors='pt')
        output_tokens = self.model.generate(
            inputs,
            max_length=256,

            do_sample=True,
            temperature=0.8,
            top_p=0.95,
            top_k=10,
            num_return_sequences=3,

            early_stopping=True,
        )
        for output in output_tokens:
            decodes = self.tokenizer.decode(output, skip_special_tokens=True)
            print(decodes)



mtt5 = MoreTrainT5()
# mtt5.pre_train()
# mtt5.pretrain_test()
mtt5.train_dialogue(new_train=False)
mtt5.test_dialogue('거대한 해적 집단에 대해 알려주세요.', age=5, is_male=True)