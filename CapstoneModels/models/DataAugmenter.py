import random

import torch
from tqdm import tqdm
from transformers import PreTrainedTokenizerFast, AutoModelForCausalLM, TrainingArguments, Trainer, \
    DataCollatorForLanguageModeling

from models import DatasetManager, korEDA, ModelManager
from models.dataset.core import UnsupervisedDataset
from models.dataset.lol import LOLProcessor

def eda_all():
    datas = DatasetManager.load_dataset_ckpt('game_summarizes')

    processors = [
        LOLProcessor.FandomProcessor(),
        LOLProcessor.UnivProcessor(),
    ]
    for processor in processors:
        processor.load()
        t, d = processor.get()
        datas += t[0]

    random.shuffle(datas)

    augmented = []
    for data in tqdm(datas):
        augmented += korEDA.EDA(data)
    random.shuffle(augmented)
    DatasetManager.save_dataset_ckpt('game_augments', augmented)

def load_uniques():
    uniques = DatasetManager.load_dataset_ckpt('proper_nouns')
    map = {}
    lang_map = {}
    for key, value in uniques.items():
        lang_map[key] = value['korean']
        for tag in value['tags']:
            if tag not in map.keys():
                map[tag] = []
            map[tag].append(value['korean'])

    return map, lang_map

def load_game_gpt(model_name):
    tokenizer = PreTrainedTokenizerFast.from_pretrained(model_name,
                                                        bos_token='</s>', eos_token='</s>', unk_token='<unk>',
                                                        pad_token='<pad>', mask_token='<mask>')
    model = AutoModelForCausalLM.from_pretrained(model_name, pad_token_id=tokenizer.eos_token_id)
    return model, tokenizer

def train_game_gpt():
    augment = DatasetManager.load_dataset_ckpt('game_augments')
    model_name = ModelManager.load('game_gpt2')
    model, tokenizer = load_game_gpt(model_name)
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    textset = UnsupervisedDataset(tokenizer=tokenizer, corpus=augment)
    train_args = TrainingArguments(
        adafactor=True,
        output_dir='G:/trains/game_gpt',
        per_device_train_batch_size=4,
        gradient_accumulation_steps=16,
        num_train_epochs=1,
        learning_rate=1e-4,
        save_steps=3000,
    )
    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=textset,
        data_collator=collator,
        tokenizer=tokenizer,
    )
    trainer.train()
    ModelManager.save(model, tokenizer, 'game_gpt2')

def ulrul(korean):
    code = (ord(korean[-1]) - 44032) % 28
    return '는' if code == 0 else '은'

def yi(korean):
    code = (ord(korean[-1]) - 44032) % 28
    return '' if code == 0 else '이'

def create_data():
    tags, langs = load_uniques()
    model_name = ModelManager.load('game_gpt2')
    model, tokenizer = load_game_gpt(model_name)

    one_hot = []
    for tag, keywords in tags.items():
        for keyword in keywords:
            if keyword == '':
                continue
            tag_suffix = '' if tag == '' else f'{tag}{ulrul(tag)}'
            one_hot.append(f'{keyword}{yi(keyword)}라는 {tag_suffix} ')

    with torch.no_grad():
        model.eval()
        model.cuda()

        augments = []
        for seed_text in tqdm(one_hot):
            input_tokens = tokenizer.encode(seed_text, return_tensors='pt').cuda()
            output_tokens = model.generate(
                input_tokens,

                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                top_k=10,
                num_return_sequences=3,

                max_length=256,
                early_stopping=True,
            )

            for output in output_tokens:
                decodes = tokenizer.decode(output)
                if len(decodes) < 10:
                    continue
                cuts = LOLProcessor.long_sentence_cuts(decodes, cut_length=128, stride=0)
                if len(cuts) > 0:
                    cuts.remove(cuts[-1])

                for sentence in cuts:
                    if '<unk>' in sentence:
                        continue
                    augments.append(sentence)

        print(f'data length : {len(augments)}')
        DatasetManager.save_dataset_ckpt('gpt2_augment', augments)


def augment_with_gpt():
    # train_game_gpt()
    create_data()