import csv
import json
import re

from torch.utils.data import Dataset
from tqdm import tqdm

from models import korEDA, DatasetManager


def load_csv_data(path):
    datas = []
    with open(path, 'r', encoding='UTF-8') as csv_file:
        csv_data = csv.reader(csv_file)
        isFirst = True
        for row in csv_data:
            if isFirst:
                isFirst = False
            else:
                datas.append(row)
    return datas

def load_json_data(path):
    datas = []
    with open(path, 'r', encoding='UTF-8') as json_file:
        json_data = json.load(json_file)
        for key in json_data:
            eng = key.lower()
            kor = json_data[key]['korean'].lower()
            datas.append({'eng': eng, 'kor': kor})
    return datas

class GameDialogue:
    question = ''
    answer = ''
    attr = {}
    isKorean = False
    version = '4'

    keys = {
        'gender': ['gender', '성별'],
        'age': ['age', '나이', '연령'],
        'from': ['origin', '출신', '원산지', 'Hometown', '고향', '기원', 'region of origin', '출신 지역', '출신지역', '출신지', 'hometown', '기원 지역'],
        'now': ['region', '지역', 'current location', '현재', '현 위치', '현 거주지', 'current', '현재 위치', '현재위치', '현재 거주지',
                'current residence', 'currently living', '현생', '현', 'current region', '현재 지역', '현재지', '현재지역', '현 지역', '현지', '현재 사는 곳', '현재 거주', '거주지'],
        'race': ['race', '인종', '종족']
    }

    def convert_key(self, key):
        for real_key, values in self.keys.items():
            if key in values:
                return real_key
        return None

    def parse_attribute(self, attribute):
        split = attribute[0].split(',')

        for attr in split:
            split2 = attr.split(':')
            key = split2[0].strip().lower()
            cvt = self.convert_key(key)

            if cvt is None:
                print(f'Unknown Key :: {key}')
                continue

            self.attr[cvt] = split2[1].strip().lower()

    def __init__(self, data):
        if data[0] == '3.5':
            self.version = '3.5'

        kor_ptn = re.compile('[가-힣]')
        if len(kor_ptn.findall(data[1])) > 0:
            self.isKorean = True

        splits = data[1].split('\n')
        self.question = re.sub(r'Q[0-9]*\. ', '', splits[0]).strip().lower()

        attribute = re.findall(r'(?<=\().*?(?=\))', splits[1])
        splits2 = splits[1].split(')', 1)
        if len(splits2) >= 2:
            self.answer = splits2[1].strip().lower()
            self.parse_attribute(attribute)
        else:
            print(data)

class GameDialogueDatas:
    changes = {    }
    dialogues = []
    parent = 'G:/Datasets/data-xlsx'

    unmatches = []


    def load_changes(self):
        change_path = f'{self.parent}/Changes.csv'
        changes = load_csv_data(change_path)
        for row in changes:
            row = [d.lower() for d in row]
            if row[1] not in self.changes.keys():
                self.changes[row[1]] = []
            self.changes[row[1]].append(row[0])

        nouns_path = f'{self.parent}/proper_nouns.json'
        nouns = load_json_data(nouns_path)
        for row in nouns:
            if row['kor'] not in self.changes.keys():
                self.changes[row['kor']] = []
            self.changes[row['kor']].append(row['eng'])


    def postprocess(self, data: GameDialogue):
        eng_ptn = re.compile(r'(?=[a-zA-Z])[a-zA-Z\'.\-\s]+')
        for aft, befs in self.changes.items():
            for bef in befs:
                data.question = data.question.replace(bef, aft)
                data.answer = data.answer.replace(bef, aft)

        # Find English words
        if data.isKorean:
            data.question = re.sub('s|the', '', data.question)
            data.question = data.question.replace('아아이오니아', '아이오니아')

            data.answer = re.sub('s|the', '', data.answer)
            data.answer = data.answer.replace('아아이오니아', '아이오니아')

            matches = eng_ptn.findall(data.question) + eng_ptn.findall(data.answer)
            for m in matches:
                m = m.strip()
                if m not in self.unmatches:
                    self.unmatches.append(m)


    def load_dialogues(self):
        dialogues = ['Dialogue1.csv']
        for file_name in dialogues:
            datas = load_csv_data(f'{self.parent}/{file_name}')
            for data in datas:
                gd = GameDialogue(data)
                self.postprocess(gd)
                self.dialogues.append(gd)

    @staticmethod
    def parse_area(area):
        areas = {
            '0': ['데마시아'],
            '1': ['녹서스'],
            '2': ['프렐요드'],
            '3': ['빌지워터'],
            '4': ['그림자 군도'],
            '5': ['아이오니아', '이오니아'],
            '6': ['슈리마'],
            '7': ['이쉬탈'],
            '8': ['이케시아'],
            '9': ['공허'],
        }
        for idx, lists in areas.items():
            if area in lists:
                return int(idx)
        return -1

    def parse_prefix(self, attribute):
        male_filter = ['남성', '남자', '남', 'male']
        gender = 0 if attribute['gender'] in male_filter else 1
        age = int(attribute['age'][:2]) // 10
        fc = self.parse_area(attribute['from']) if 'from' in attribute.keys() else None
        nc = self.parse_area(attribute['now']) if 'now' in attribute.keys() else None

        prefixes = []

        prefix = f'talk_g{gender}_a{age}'
        if fc is not None and fc >= 0 and nc is not None and nc >= 0:
            prefix += f'_f{fc}_n{nc}'
            prefixes.append(prefix)
        else:
            prefixes.append(f'{prefix}_f0_n0')
            prefixes.append(f'{prefix}_f1_n1')
            prefixes.append(f'{prefix}_f2_n2')
            prefixes.append(f'{prefix}_f3_n3')
            prefixes.append(f'{prefix}_f5_n5')

        return prefixes

    def formatting(self, task, question, answer):
        if self.form == 't5':
            return {'input': f'{task} : {question}', 'label': answer}
        elif self.form == 'gpt2':
            age = task.split('_a')[1][:1]
            gender = '남성' if task.split('_f')[1][:1] == '0' else '여성'
            return {'input': f'{question}에 대해 {age}0대 {gender}의 말투로 답변하라.'}


    def check_dup(self, arr:list, new: dict):
        for data in arr:
            if data['input'] == new['input'] and (self.form == 't5' and data['label'] == new['label']):
                return True
        return False

    def processing_data(self, data: GameDialogue):
        datas = []

        prefixes = self.parse_prefix(data.attr)
        aug_questions = korEDA.EDA(data.question, num_aug=4)
        aug_answers = korEDA.EDA(data.answer, num_aug=4)

        datas.append(self.formatting(prefixes[0], data.question, data.answer))

        for idx in range(0, 5):
            prefix = prefixes[0] if len(prefixes) == 1 else prefixes[idx]
            question = aug_questions[idx]
            answer = aug_answers[idx]
            new = self.formatting(prefix, question, answer)
            if self.check_dup(datas, new):
                continue
            datas.append(self.formatting(prefix, question, answer))

        return datas

    def get_datas(self, need_korean:bool = True, need_english:bool = False):
        datas = []
        for data in self.dialogues:
            if data.answer == '':
                continue

            if (data.isKorean and need_korean) or (not data.isKorean and need_english):
                processed = self.processing_data(data)
                datas += processed

        return datas

    def __init__(self, form:str):
        self.load_changes()
        self.load_dialogues()
        self.form = form
        # print(self.unmatches)

class GameDialogueDataset(Dataset):
    def __init__(self, tokenizer, kor:bool = True, eng:bool = False, form:str = 't5'):
        gdd = GameDialogueDatas(form=form)
        self.tokenizer = tokenizer
        self.datas = gdd.get_datas(need_korean=kor, need_english=eng)
        self.form = form

    def __getitem__(self, item):
        data = self.datas[item]
        inputs = data['input']
        input_text = self.tokenizer(inputs, max_length=128, padding='max_length', truncation=True, return_tensors='pt')
        tens = {
            'input_ids': input_text.input_ids.squeeze(0),
            'attention_mask': input_text.attention_mask.squeeze(0),
        }

        if self.form == 't5':
            outputs = data['label']
            label_text = self.tokenizer(outputs, max_length=256, padding='max_length', truncation=True,
                                        return_tensors='pt')
            tens['labels'] = label_text.input_ids.squeeze(0)

        return tens

    def __len__(self):
        return len(self.datas)