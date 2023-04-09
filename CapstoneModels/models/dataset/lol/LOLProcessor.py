import re

from tqdm import tqdm

from models import DatasetManager
from models.dataset.core import DataProcessor


titles = {}

def preprocess(context:str, is_title:bool = False):
    context = re.sub('[0-9]+\n|\n[0-9]+', '', context)
    context = context.replace('\n', '')
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

class FandomProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.propers = get_nouns()

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = False):
        super().load(train_suffix, dev_suffix, load_dev)

    def getName(self):
        return 'fandom-lol'

    def process(self, datas):
        dialogues = []

        for data in tqdm(datas):

            title = preprocess(data['title'], is_title=True).strip()
            no_slash_title = re.sub('\s*/\s*', '', title)
            korean = False
            if no_slash_title in self.propers.keys():
                if self.propers[no_slash_title]['korean'] != '':
                    title = self.propers[no_slash_title]['korean']
                    korean = True
            else:
                continue
            if title not in titles and not korean:
                titles[title] = {'korean': '', 'tags': [], 'expired': False}

            realdata = data['data']
            for key, value in realdata.items():
                if key == 'tables':
                    pass
                elif key == 'inner':
                    for tabs in value:
                        for tab_title, tab_value in tabs.items():
                            processed = None
                            if type(tab_value) is str:
                                processed = preprocess(tab_value).strip()
                            elif type(tab_value) is list:
                                joined = " ".join(tab_value).replace('\n', '')
                                processed = preprocess(joined).strip()
                            if processed is not None and processed != '':
                                if korean:
                                    dialogues.append(f'{title}{ulrul(title)} {processed}')
                                else:
                                    continue
                                    # dialogues.append(f'{title}는 {processed}')
                elif key == 'quotes':
                    for quote in value:
                        if type(quote) is not dict or 'context' not in quote.keys():
                            continue
                        context = preprocess(quote['context']).strip()
                        if korean:
                            dialogues.append(f'{title}{ulrul(title)} {context}')
                        else:
                            continue
                            # dialogues.append(f'{title}는 {context}')

        DatasetManager.save_dataset_ckpt('doc_names', titles, indent=' ')
        return dialogues

    def get_tags(self):
        return ['game_unsupervised']

class UnivProcessor(DataProcessor):
    def __init__(self):
        super().__init__()

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = False):
        super().load(train_suffix, dev_suffix, load_dev)

    def getName(self):
        return 'univ-lol'

    def process(self, datas):
        dialogues = []

        for value in tqdm(datas):
            data = value['data']
            for key, document in data.items():
                if key == 'description':
                    dialogues.append(document)
                elif key == 'document':
                    dialogues += document

        return dialogues

    def get_tags(self):
        return ['game_unsupervised']