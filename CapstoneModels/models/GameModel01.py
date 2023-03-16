import collections
import json
import math
import re

from tqdm import tqdm

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


    def __init__(self, tokenizer):
        train01_dir = "../data_crawler/data/univ_ko/Univ-Ko.json"
        train02_dir = "../data_crawler/data/FandomEnTranslated/Fandom-EnKo.json"
        train03_dir = "../data_crawler/data/UniverseEnTranslated/Univ-EnKo.json"

        self.train_sentences = []
        self.load_def(train01_dir)
        self.load_translated(train02_dir)
        self.load_translated(train03_dir)

        distribution = collections.defaultdict(int)
        cut64 = collections.defaultdict(int)
        with tqdm(total=len(self.train_sentences), leave=True) as pbar:
            for sentence in self.train_sentences:
                token = tokenizer(sentence)
                length = len(token['input_ids'])
                distribution[length] += 1
                key = f"{math.floor(length/64)*64} ~ {math.ceil(length/64)*64}"
                cut64[key] += 1
                pbar.update(1)

        print(cut64)

        GraphGenerator.generate_tokens_length(distribution)