import re

from tqdm import tqdm

from models import DatasetManager
from models.dataset.core import DataProcessor


titles = {}

def preprocess(context:str, is_title:bool = False):
    context = re.sub('[0-9]+\n|\n[0-9]+', '', context)
    context = context.replace('\n', ' ')
    context = re.sub(r'([^0-9a-zA-Z가-힣])\1+', r'\1', context)
    context = re.sub(r'[“”]', '"', context)
    context = re.sub(r'[‘’]', '\'', context)
    context = re.sub(r'\(.*\)\s*|·', '', context)
    if is_title:
        context = re.sub('\(\w+\)', '', context)
        context = context.replace('_', ' ')
        context = context.split(':')[0]
        context = re.sub('Part [0-9]+', '', context)
        return context[1:]
    return context

def clear_tabKey(key:str):
    key = key.replace('/Lore/', '')
    return key

def get_nouns():
    return DatasetManager.load_dataset_ckpt('proper_nouns')

def ulrul(korean):
    code = (ord(korean[-1]) - 44032) % 28
    return '는' if code == 0 else '은'

def yi(korean):
    code = (ord(korean[-1]) - 44032) % 28
    return '는' if code == 0 else '은'

def long_sentence_cuts(text, cut_length:int = 256*3+128, stride:int=128):
    end_chars = ['.', '?', '!']
    end_poses = []
    for end_char in end_chars:
        cached_text = text
        idx = 0
        while True:
            find = cached_text[idx:].find(end_char)
            if find == -1 or idx >= len(text):
                break

            if end_char == '.' and len(cached_text) < find+1 and cached_text[find+1] == '.':
                idx += find + 2
                continue

            end_poses.append(idx + find)
            idx += find+1

    end_poses = sorted(end_poses)

    if len(end_poses) == 0:
        return []

    sentences = []

    try:
        # curr_start : 현재 문장을 자르기 시작한 위치
        curr_start = 0
        # next_start : 이번 문장을 자른 뒤 이전 문장을 자르기 시작할 위치
        next_start = 0
        # cut_ : 문장 분할 파라미터
        cut_gap = cut_length

        for pos in end_poses:
            stride_gap = abs((cut_length - stride) - (pos - curr_start))
            now_stride_gap = abs((cut_length - stride) - (next_start - curr_start))
            if stride_gap < now_stride_gap:
                next_start = pos

            sentence_length = (curr_start + cut_length) - pos
            if sentence_length > 0:
                cut_gap = pos
            else:
                sentence_length = abs(sentence_length)
                cut_pos = cut_gap if cut_gap < sentence_length else pos
                new_text = text[curr_start:cut_pos+1]
                if new_text[0] in end_chars:
                    new_text = new_text[1:]
                new_text = new_text.strip()
                sentences.append(new_text)
                curr_start = next_start

        if curr_start != end_poses[len(end_poses)-1]:
            new_text = text[curr_start:]
            if new_text[0] in end_chars:
                new_text = new_text[1:]
            new_text = new_text.strip()
            sentences.append(new_text)

        return sentences
    except:
        return sentences


def validate(text):
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'\.+\s+|\s+\.+', '.', text)
    text = re.sub(r'\.{2,}', '...', text)
    text = re.sub(r'\.(?=[^\s.])', '. ', text)

    last_char = text[len(text)-1:]
    pass_chars = ['?', '.', '!']
    if last_char not in '?.!':
        max_idx = -1
        for pass_char in pass_chars:
            find = text.rfind(pass_char)
            max_idx = max(find, max_idx)
        text = text[:max_idx+1]
        if max_idx == -1:
            return None

    if text == '':
        return None

    if len(text) > 256*3*2:
        return long_sentence_cuts(text)

    mismatches = [False, False]
    if len(text.split('\'')) % 2 == 0:
        text = text + '\''
        mismatches[0] = True
    if len(text.split('"')) % 2 == 0:
        text = text + '"'
        mismatches[1] = True
    if mismatches[0] and mismatches[1]:
        return None

    return text


def make_content(context, title):
    return {'context': context, 'summaries': f'이 이야기는 {title}에 관한 것이다.'}

class FandomProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.nouns = get_nouns()
        self.dialogues = []

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = False):
        super().load(train_suffix, dev_suffix, load_dev)

    def getName(self):
        return 'fandom-lol'

    def append(self, context):
        context = validate(preprocess(context)) if type(context) is str else context

        if type(context) is str:
            self.dialogues.append(context.lower().strip())

        elif type(context) is list:
            concat_length = 256*3
            concat = ''
            for text in context:
                if len(concat) + len(text) > concat_length:
                    self.append(concat)
                    concat = ''
                concat = f'{concat} {text}'
            if concat != '':
                self.append(concat)

    def process(self, datas):
        self.dialogues = []

        for data in tqdm(datas):

            title = preprocess(data['title'], is_title=True).strip()
            no_slash_title = re.sub('\s*/\s*', '', title)
            if no_slash_title not in self.nouns.keys():
                continue

            korean = False
            if self.nouns[no_slash_title]['korean'] != '':
                title = self.nouns[no_slash_title]['korean']
                korean = True

            if title not in titles and not korean:
                titles[title] = {'korean': '', 'tags': [], 'expired': False}

            realdata = data['data']
            for key, value in realdata.items():
                if key == 'tables':
                    for table in value[0]:
                        if type(table) is dict and 'Description' in table.keys():
                            self.append(table['Description'])
                        else:
                            print(value)
                    pass
                elif key == 'inner':
                    for tabs in value:
                        for tab_title, tab_value in tabs.items():
                            processed = None
                            if type(tab_value) is str:
                                processed = preprocess(tab_value)
                            elif type(tab_value) is list:
                                joined = " ".join(tab_value).replace('\n', ' ')
                                processed = preprocess(joined)

                            processed = validate(processed)
                            if processed is None or processed == '' or not korean:
                                continue

                            self.append(processed)
                elif key == 'quotes':
                    for quote in value:
                        if type(quote) is not dict or 'context' not in quote.keys() or not korean:
                            continue
                        self.append(quote['context'])

        print(f'length : {len(self.dialogues)}')
        return self.dialogues

    def get_tags(self):
        return ['game_unsupervised']

class UnivProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.dialogues = []

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = False):
        super().load(train_suffix, dev_suffix, load_dev)

    def getName(self):
        return 'univ-lol'

    def append(self, context):
        context = validate(preprocess(context)) if type(context) is str else context

        if type(context) is str:
            self.dialogues.append(context.lower().strip())

        elif type(context) is list:
            concat_length = 256*3
            concat = ''
            for text in context:
                if len(concat) + len(text) > concat_length:
                    self.append(concat)
                    concat = ''
                concat = f'{concat} {text}'
            if concat != '':
                self.append(concat)

    def process(self, datas):

        for value in tqdm(datas):
            data = value['data']
            for key, document in data.items():

                if key == 'document':
                    self.append(document)

                elif key == 'description':
                    self.append(document)

                elif key == 'quotes':
                    quote = document['quote']
                    by = document['by']
                    context = f'{by}{ulrul(by)} {quote}라고 말했다.'
                    self.append(context)

        return self.dialogues

    def get_tags(self):
        return ['game_unsupervised']