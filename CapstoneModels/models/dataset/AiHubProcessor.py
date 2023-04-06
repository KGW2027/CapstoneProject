import json
import math
import os
import re
from collections import defaultdict

from tqdm import tqdm

import GraphGenerator
from models import DatasetManager

emotes = {
    "<laugh>": r'(?!ㄱ)[ㅋㄱ]+|[ㅋㅎ]+|(ㅋㅅㅋ)|키키+|크크+|하하+',
    "<slur>": r'\.\.+',
    "<surprise>": r'(ㅗㅜㅑ)|(ㅁㅊㄷ)+|(ㅁㅊ)+|(ㅁㅊㅇ)+',
    "<weak_abuse>": r'(ㅈㄹ)+|(ㅈㄹㄴ)+|(ㄷㅊ)+|(ㄲㅈ)+|(ㅆㄺ)+|(ㅆㄹㄱ)+|(ㅉ)+',
    "<strong_abuse>": r'(ㅅㅂ)+|(ㅆㅂ)+|(ㅄ)+|(ㅗ)+',
    "<wait>": r'(ㄱㄷ)+',
    "<ty>": r'(ㄱㅅ)+|(ㄳ)+',
    "<no>": r'(ㄴ)+|(ㅅㄹㄷ)+|(ㅅㄹ)+',
    "<ok>": r'(ㅇㅋ)+|ㅇ+|[ㅔㅖㅓ]+|(ㅁㅈ)+',
    "<expect>": r'(ㄷㄱ)+',
    "<sry>": r'(ㅈㅅ)+',
    "<hurry>": r'(ㅃㄹ)+',

    "<sad>": r'[ㅜㅠ]+|(ㅜ+ㅠ+)+|(ㅠ+ㅜ+)+|ㄸ[ㄹ]+',
    "<scare>": r'(ㄷ)+|(ㄸ)+',
    "<celebrate>": r'(?!ㅈ)[ㅈㅊ]+',
    "<run>": r'[ㅌ]+',
    "<why>": r'[ㅞㅙ]+',
    "<go>": r'[ㄱ]+',
    "<bored>": r'[ㅡ]+',
    "<bye>": r'ㅂ(ㅂ)+|(ㅃ)+',
    "<hello>": r'(ㅑ)+',
}

aihub20_acts = {
    '질문하기': 0,
    '주장하기': 1,
    '진술하기': 2,
    '턴토크 사인': 3,
    '충고제안하기': 4,
    '약속하기': 5,
    '명령요구하기': 6,
    '부탁하기': 7,
    '반박하기': 8,
    '긍정감정 표현하기': 9,
    '감사하기': 10,
    '부정감정 표현하기': 11,
    '거절하기': 12,
    '위협하기': 13,
    '사과하기': 14,
    '인사하기': 15,
}

emote_keys = ['<laugh>', '<surprise>', '<weak_abuse>', '<strong_abuse>', '<wait>', '<ty>', '<no>', '<ok>', '<expect>', '<sry>', '<hurry>',
              '<sad>', '<scare>', '<celebrate>', '<run>', '<why>', '<go>', '<bored>', '<bye>', '<hello>']

ag_token = '<ag>'
act_token = '<act>'
res_token = '<response>'

def add_tokens(tokenizer):
    tokenizer.add_tokens(list(emotes.keys()) + ['<name>', '<belong>', '<place>'])
    return tokenizer

def load_aihub_sns():
    filepath = 'datasets/aihub/result.json'
    with open(filepath, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
    return json_data

def view_tokens_length_statistics_sns(json_obj, tokenizer):
    lengths = defaultdict(int)
    lengths_64 = defaultdict(int)
    for _, datas in json_obj.items():
        for data in tqdm(datas):
            for dialogue in data['dialogue']:
                tokens = tokenizer(dialogue[1])
                length = len(tokens['input_ids'])
                lengths[length] += 1
                lengths_64[math.floor(length/64)] += 1

    GraphGenerator.generate_tokens_length(lengths)
    GraphGenerator.generate_tokens_length(lengths_64)
    for idx in range(len(lengths_64)):
        print(f"[{idx*64}, {(idx+1)*64}) :: {lengths_64[idx]}")


def preprocess_message(message):
    # Specific Token Replacing & Masking
    replaces = {
        "<name>": ["이름", "신원", "계정", "번호", "전번"],
        "<belong>": ["소속", "주소"],
        "<place>": ['장소', '위치']
    }
    for k, v in replaces.items():
        for tgt in v:
            message = message.replace('#@' + tgt + '#', k)

    for key in emote_keys:
        message = re.sub(emotes[key], key, message)

    # remove all not seeds
    message = re.sub(r'#@[가-힣]+(#[가-힣]+)?#', '', message)
    message = re.sub(r'[^<>\[\]()가-힣a-z0-9. !?]|#@\w+#', '', message)

    # Special Character Short
    message = re.sub(r"!+\?+|\?+!+", '?!', message)
    message = re.sub(r'\.{3,}', '...', message)
    message = re.sub(r'\s+', ' ', message)

    return message



def getPath(name:str):
    parent = f'G:/Datasets/{name}/'
    return parent+'train', parent+'valid'

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

    def load(self):
        train, valid = getPath(self.getName())
        self.internal_load(getFiles(train), self.train)
        self.internal_load(getFiles(valid), self.dev, train_mode=False)

    def internal_load(self, files: list, array: list, train_mode: bool = True, save_cache: bool = True, load_cache: bool = True):
        mode = 'train' if train_mode else 'dev'

        if load_cache:
            load = DatasetManager.load_dataset_ckpt(f'{self.getName()}-{mode}')
            if load is not None:
                print('load dataset cache')
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

    def getName(self):
        return None

    def process(self, data):
        return None

    def get(self):
        return self.train, self.dev



class AiHub20(DataProcessor):
    def __init__(self):
        super().__init__()
        self.acts = defaultdict(int)
        self.ags = defaultdict(int)

    def getName(self):
        return 'aihub_20'

    def get_ag(self, speaker):
        return str((0 if speaker['sex'] == '여성' else 1) * 10 + int(speaker['age'][:1]))

    def get_act(self, act):
        act = re.sub(r'(?=\().*?(?<=\))', '', act).strip().replace('/', '')
        if act not in aihub20_acts.keys():
            return '16'
        return str(aihub20_acts[act])

    def process(self, data):
        dialogues = []

        info = data['info'][0]
        annotations = info['annotations']

        if annotations['speaker_type'] != '1:1':
            return None

        lines = annotations['lines']
        bef_pid = -1
        bef_act = -1
        prev_context = ''
        now_context = ''
        for line in lines:
            context = preprocess_message(line['norm_text']).strip()
            persona = self.get_ag(line['speaker'])
            act = self.get_act(line['speechAct'])
            pid = line['speaker']['id'][:1]
            self.acts[act] += 1

            now_context = context if now_context == '' else (now_context + '<s>' + context)
            if bef_pid != pid:
                if prev_context != '':
                    concat = prev_context + ag_token + persona + act_token + bef_act + res_token + now_context
                    dialogues.append(concat)
                    self.ags[persona] += 1
                prev_context = now_context
                bef_act = act
                now_context = ''
            bef_pid = pid

        return dialogues

    def check(self):
        print(self.ags)
        print(self.acts)
        print(len(self.train))
        print(len(self.dev))