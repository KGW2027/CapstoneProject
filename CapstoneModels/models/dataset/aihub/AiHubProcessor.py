import json
import math
import re
from collections import defaultdict

from tqdm import tqdm

import GraphGenerator
from models.dataset.core import DataProcessor

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
    specials = re.findall('[*#@]+', message)

    message = re.sub(r'\*+', '<name>', message)

    for key in emote_keys:
        message = re.sub(emotes[key], key, message)

    # remove all not seeds
    message = re.sub(r'#@[가-힣]+(#[가-힣]+)?#', '', message)
    message = re.sub(r'[^<>\[\]()가-힣a-z0-9. !?]|#@\w+#', '', message)

    # Special Character Short
    message = re.sub(r"!+\?+|\?+!+", '?!', message)
    message = re.sub(r'\.{3,}', '<mop>', message)
    message = re.sub(r'\s+', ' ', message)

    return message

class AiHub20(DataProcessor):
    def __init__(self):
        super().__init__()
        self.acts = defaultdict(int)
        self.ags = defaultdict(int)

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = True):
        super().load(train_suffix='train', dev_suffix='valid', load_dev=True)

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

        prev_talker = -1
        prev_talk = ''
        curr_talk = ''
        for line in annotations['lines']:
            context = preprocess_message(line['norm_text']).strip()
            persona = self.get_ag(line['speaker'])
            pid = line['speaker']['id'][:1]

            curr_talk = context if curr_talk == '' else (curr_talk + '<s>' + context)
            if prev_talker != pid:
                if prev_talk != '':
                    concat = self.formatting(prev_talk, persona, curr_talk)
                    dialogues.append(concat)
                    self.ags[persona] += 1
                prev_talk = curr_talk
                curr_talk = ''
            prev_talker = pid

        if prev_talk != '' and curr_talk != '':
            concat = self.formatting(prev_talk, persona, curr_talk)
            dialogues.append(concat)


        return dialogues

    def tokens(self):
        return list(emotes.keys()) + ['<name>', '<belong>', '<place>']

    def check(self):
        print(self.ags)
        print(self.acts)
        print(len(self.train))
        print(len(self.dev))

class AiHub22(DataProcessor):
    def clean_message(self, text):
        text = text.replace('\n', ' ')
        text = re.sub(r'([^0-9a-zA-Z가-힣])\1+', r'\1', text)
        text = re.sub(r'\(.*\)\s*|[\'"‘’“”·]', '', text)

        return text.lower().strip()

    def __init__(self):
        super().__init__()
        self.acts = defaultdict(int)
        self.ags = defaultdict(int)

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = True):
        super().load(train_suffix='train', dev_suffix='valid', load_dev=True)

    def getName(self):
        return 'aihub_22'

    def process(self, data):

        context = self.clean_message(data['Meta(Refine)']['passage'])
        summaries = []
        for k, v in data['Annotation'].items():
           if type(v) is str:
                summaries.append(self.clean_message(v))

        return {'context': context, 'summaries': summaries}

    def get_tags(self):
        return ['real_summarize']
