import random

import torch
from tqdm import tqdm
from transformers import AutoTokenizer, T5ForConditionalGeneration, Seq2SeqTrainer, DataCollatorForSeq2Seq, \
    Seq2SeqTrainingArguments

from models import ModelManager, DatasetManager
from models.dataset.aihub import AiHubProcessor
from models.dataset.core import UnsupervisedDatasetWithLabel, SummarizeDataset
from models.dataset.lol import LOLProcessor


class GameSummarizationModel:
    def __init__(self, load_ckpt:bool = False, ckpt_name:str = 'game_ust'):
        if load_ckpt:
            model_path = ModelManager.load(ckpt_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        else:
            model_path = "psyche/KoT5-summarization"
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)

    def train_game(self, batch_size:int = 2, gradient_step: int = 4, num_epochs: int = 5):
        game_texts = DatasetManager.load_dataset_ckpt('game_augments')

        textset = UnsupervisedDatasetWithLabel(tokenizer=self.tokenizer, corpus=game_texts)
        collator = DataCollatorForSeq2Seq(self.tokenizer, model=self.model)

        train_args = Seq2SeqTrainingArguments(
            adafactor=True,
            output_dir='G:/trains/newgame',
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_step,
            num_train_epochs=num_epochs,
            learning_rate=1e-5,
            save_steps=300,
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=train_args,
            train_dataset=textset,
            data_collator=collator,
            tokenizer=self.tokenizer,
        )

        self.model = self.model.cuda()
        trainer.train()
        ModelManager.save(self.model, self.tokenizer, name='game_ust')

    def train_summarize(self, batch_size:int = 2, gradient_step: int = 8, num_epochs: int = 1):
        processors = [
            AiHubProcessor.AiHub22()
        ]

        summarize_train = []
        summarize_dev = []
        for processor in processors:
            processor.load()
            t, d = processor.get()
            summarize_train += t
            summarize_dev += d

        train_set = SummarizeDataset(tokenizer=self.tokenizer, corpus=summarize_train)
        dev_set = SummarizeDataset(tokenizer=self.tokenizer, corpus=summarize_dev)
        collator = DataCollatorForSeq2Seq(self.tokenizer, model=self.model)

        train_args = Seq2SeqTrainingArguments(
            adafactor=True,
            output_dir='G:/trains/newgame',
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_step,
            num_train_epochs=num_epochs,
            learning_rate=1e-3,
            logging_steps=1500,
            save_steps=1500,
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=train_args,
            train_dataset=train_set,
            eval_dataset=dev_set,
            data_collator=collator,
            tokenizer=self.tokenizer,
        )

        self.model = self.model.cuda()
        trainer.train()
        ModelManager.save(self.model, self.tokenizer, name='game_ust')




    def test_game(self, tests:int = 3):
        processors = [
            LOLProcessor.FandomProcessor(),
            LOLProcessor.UnivProcessor(),
            ]

        game_texts = []
        for processor in processors:
            processor.load()
            t, d = processor.get()
            game_texts += t[0]

        random.shuffle(game_texts)

        with torch.no_grad():
            self.model.eval()
            for idx in range(tests):
                text = f'summarize_summary: {game_texts[idx]}'
                input_tokens = self.tokenizer.encode(text, return_tensors='pt')

                output_tokens = self.model.generate(
                    input_tokens,
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
                print(f'\nContext : {text}')
                for output in output_tokens:
                    decodes = self.tokenizer.decode(output, skip_special_tokens=True)
                    print(f' - Summarize >> {decodes}')

    def test_summarize(self, tests:int = 3):
        processors = [
            AiHubProcessor.AiHub22()
        ]

        dev_texts = []
        for processor in processors:
            processor.load()
            t, d = processor.get()
            dev_texts += d
        random.shuffle(dev_texts)


        with torch.no_grad():
            self.model.eval()
            for idx in range(tests):
                example = dev_texts[idx]
                context = example['context']
                text = f'summarize_summary: {context}'
                input_tokens = self.tokenizer.encode(text, return_tensors='pt')

                output_tokens = self.model.generate(
                    input_tokens,
                    max_length=128,

                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    top_k=10,

                    early_stopping=True,
                )
                summarize = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)
                print(f'\nContext : {text}\nSummarize : {summarize}')
                for example_summaries in example['summaries']:
                    if example_summaries is not None:
                        print(f'Summary Example : {example_summaries}')


    def augment_game(self):
        processors = [
            LOLProcessor.FandomProcessor(),
            LOLProcessor.UnivProcessor(),
            ]

        game_texts = []
        for processor in processors:
            processor.load()
            t, d = processor.get()
            game_texts += t[0]

        random.shuffle(game_texts)

        splits = []
        for text in game_texts:
            if text == '':
                continue
            splits += LOLProcessor.long_sentence_cuts(text, cut_length=256+128, stride=64)

        augments = []
        with torch.no_grad():
            self.model.eval()
            self.model.cuda()

            for text in tqdm(splits):
                text = f'summarize_summary: {text}'
                input_tokens = self.tokenizer.encode(text, return_tensors='pt').cuda()

                output_tokens = self.model.generate(
                    input_tokens,
                    max_length=128,

                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    top_k=10,
                    num_return_sequences=2,

                    early_stopping=True,
                )

                for output in output_tokens:
                    summarize = self.tokenizer.decode(output, skip_special_tokens=True)
                    if summarize == text or summarize in augments:
                        continue
                    augments.append(summarize)

        DatasetManager.save_dataset_ckpt('game_summarizes', augments)



