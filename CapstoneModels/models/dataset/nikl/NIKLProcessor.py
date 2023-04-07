import re
from collections import defaultdict

from models.dataset.core import DataProcessor


def preprocess_message(message):
    message = re.sub(r'&name\d*&', '<name>', message)
    message = re.sub(r'&address\d*&', '<place>', message)
    message = re.sub(r'&brands\d*&', '<brand>', message)
    message = re.sub(r'&others\d*&', '<etc>', message)
    message = re.sub(r'&affiliation\d*&', '', message)
    message = message.replace('{laughing}', '<laugh>').replace('{clearing}', '').replace('{singing}', '').replace('{applauding}', '')

    # x prefix
    message = re.sub(r'x[^ >]*랑', '<name>랑', message)
    message = re.sub(r'x[^ >]*가', '<name>가', message)
    message = re.sub(r'x[^ >]*역', '<place>역', message)
    message = re.sub(r'x[^ >]*에서는', '<place>에서는', message)
    message = re.sub(r'x[^ >]*에', '<place>에', message)
    message = re.sub(r'x[^ >]*로', '<place>로', message)
    message = re.sub(r'x[^ >]*이나', '<place>이나', message)
    message = re.sub(r'[^ >]*x[^ <]* ', '', message)

    # remove all not seeds
    message = re.sub(r'#@[가-힣]+(#[가-힣]+)?#', '', message)
    message = re.sub(r'[^<>가-힣a-z0-9. !?]|#@\w+#', '', message)

    # Special Character Short
    message = re.sub(r"!+\?+|\?+!+", '?!', message)
    message = re.sub(r'\.{3,}', '<mop>', message)
    message = re.sub(r'\s+', ' ', message)

    return message


def mask_tokens(context):
    return re.sub('<\w+>', '', context).strip()


class NiklDialogueProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.topics = defaultdict(int)
        self.settings = defaultdict(int)
        self.ag_distribute = defaultdict(int)
        self.dialogues = 0

    def load(self, train_suffix:str = '', dev_suffix:str = '', load_dev:bool = False):
        super().load(train_suffix, dev_suffix, load_dev)

    def getName(self):
        return 'NIKL_DIALOGUE_2021_v1.0'

    def check_token(self, context):
        specials = re.findall('&\w+&', context) + re.findall('(?=\{).*?(?<=\})', context)
        for special in specials:
            if special not in self.tokens:
                self.tokens.append(special)

    def process(self, data):
        dialogues = []

        documents = data['document']
        for document in documents:
            meta = document['metadata']
            title = meta['title']
            if title != '2인 일상 대화':
                continue
            topic = meta['topic'].split('>')[0].strip()
            relation = meta['setting']['relation']
            self.topics[topic] += 1
            self.settings[relation] += 1

            speakers = {}
            for speaker in meta['speaker']:
                pid = speaker['id']
                agt = (0 if speaker['sex'] == '여성' else 1) * 10 + int(speaker['age'][:1])
                speakers[pid] = agt

            prev_talk = ''
            prev_talker = -1
            curr_talk = ''

            for utterance in document['utterance']:
                talker = utterance['speaker_id']
                context = preprocess_message(utterance['original_form'])
                self.check_token(context)


                if prev_talker != -1 and prev_talker != talker:
                    if prev_talk != '' and curr_talk != '':
                        concat = self.formatting(prev_talk, speakers[talker], curr_talk)
                        self.ag_distribute[speakers[talker]] += 1
                        dialogues.append(concat)
                    if mask_tokens(curr_talk) == '':
                        prev_talk = ''
                    else:
                        prev_talk = curr_talk
                    curr_talk = ''
                curr_talk = context if curr_talk == '' else f'{curr_talk} {context}'
                prev_talker = talker

            if prev_talk != '' and curr_talk != '':
                concat = self.formatting(prev_talk, speakers[talker], curr_talk)
                dialogues.append(concat)

        self.dialogues += len(dialogues)
        return dialogues

    def tokens(self):
        return ['<name>', '<place>', '<brand>', '<etc>', '<laugh>']

    def check(self):
        print(f'total : {self.ag_distribute}')