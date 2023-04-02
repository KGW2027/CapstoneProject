import json
import math
import os
import re
from collections import defaultdict

from tqdm import tqdm

import GraphGenerator

emotes = {
    "<LAUGH>": r'[ㅋㅎ]+|(ㅋㅅㅋ)|ㅋ+ㄱ+|ㄱ+ㅋ+|ㅋ+',
    "<INTERJECTION>": r'(ㅗㅜㅑ)|(ㅁㅊㄷ)+|(ㅁㅊ)+',
    "<ABUSE_W>": r'(ㅈㄹ)|(ㄷㅊ)|(ㄲㅈ)|(ㅆㄺ)|(ㅆㄹㄱ)|(ㅉ)+',
    "<ABUSE_S>": r'(ㅅㅂ)+|(ㅆㅂ)|(ㅄ)+|(ㅗ)+',
    "<WAIT>": r'(ㄱㄷ)+',
    "<THANKS>": r'(ㄱㅅ)+|(ㄳ)+',
    "<NO>": r'(ㄴ)+|(ㅅㄹㄷ)+|(ㅅㄹ)+',
    "<OK>": r'(ㅇㅋ)|[ㅇ]+|[ㅔㅖㅓ]+|(ㅁㅈ)+',
    "<EXPECT>": r'(ㄷㄱ)+',
    "<SORRY>": r'(ㅈㅅ)+',
    "<HURRY>": r'(ㅃㄹ)',

    "<SAD>": r'[ㅜ]+|[ㅠ]+|[ㅜ]+[ㅠ]+|[ㅠ]+[ㅜ]+|ㄸ[ㄹ]+',
    "<SCARE>": r'(ㄷ)+|(ㄸ)+',
    "<CELEBRATE>": r'(ㅊ)+',
    "<RUN>": r'[ㅌ]+',
    "<WHY>": r'[ㅞㅙ]',
    "<GO>": r'[ㄱ]+',
    "<BORED>": r'[ㅡ]+',
    "<BYE>": r'ㅂ(ㅂ)+|(ㅃ)+',
    "<HELLO>": r'(ㅑ)',
}

def add_tokens(tokenizer):
    for token in emotes.keys():
        tokenizer.add_tokens(token)
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

##### Parsers


class AiHubKoreanSNS:
    # AI HUB Dataset ( 일상 대화 ) Structure
    # numberOfItems: 총 데이터 개수
    # data: 데이터 JSONArray
    #   header:
    #       dialogueInfo:
    #           dialogueID: 채팅 ID
    #           numberOfParticipants: 채팅 참여자 수
    #           numberOfUtterances: 채팅 개수
    #           numberOfTurns: 대화를 주고 받은 수(한 사람이 연속 3개 : 채팅 개수 3개, 1턴)
    #           topic: 주제
    #       participantsInfo: 참가자 Array
    #           participantID: ID
    #           gender: 성별
    #           age: 나이(10살 단위)
    #  body: 채팅 Array
    #   utteranceID : 채팅 Index
    #   turnID : 담화 Index
    #   participantID : 말하는 사람
    #   utterance : 채팅

    def parse_category(self, topic: str):
        categories = {"개인및관계": 0, "미용과건강": 1, "상거래(쇼핑)": 2, "시사교육": 3, "식음료": 4, "여가생활": 5, "일과직업": 6, "주거와생활": 7,
                      "행사": 8}
        return categories.get(topic)

    def replace(self, match):
        return match.group(1)

    def preprocess_message(self, message):
        # Specific Token Replacing & Masking
        replaces = {
            "<NAME>": ["이름", "신원", "계정", "번호", "전번"],
            "<BELONG>": ["소속", "주소"],
        }
        for k, v in replaces.items():
            for tgt in v:
                message = message.replace('#@' + tgt + '#', k)
        message = re.sub(r'#@\w+#', '', message)
        message = re.sub(r'\s+', ' ', message)

        for token, regex in emotes.items():
            message = re.sub(regex, token, message)

        # Special Character Short
        message = re.sub(r"!+\?+|\?+!+", '?!', message)
        message = re.sub(r'([^.\w])\1+', r'\1', message)
        message = re.sub(r'([가-힣]+#)|@', '', message)

        pattern = re.compile(r"(<[a-zA-Z0-9]+>)+")
        message = re.sub(pattern, self.replace, message)
        message = re.sub(r'<(\w+)>ㅅ<\1>', r'<\1>', message)
        message = re.sub(r'[ㄱ-ㅎ]ㅅ[ㄱ-ㅎ]', '', message)

        return message

    def merge_data(self):
        path_dir = 'datasets/aihub/'

        datas = {}

        for raw_data in os.listdir(path_dir):
            if raw_data == 'result.json':
                continue

            with open(path_dir + raw_data, "r", encoding='utf-8') as read_json:
                print(f"Start load {raw_data}")
                json_data = json.load(read_json)['data']
                multiturn_dataset = []
                for item in tqdm(json_data):
                    # 대화 참가자 추상화 ( 성별 : 남성은 0, 여성은 1, 나이 : 10대 단위로 자름 )
                    # P1 -> index 0, P2 -> index 1 ...
                    participants = {}
                    for participant in item['header']['participantsInfo']:
                        gender = participant['gender']
                        gender = 0 if gender == '남성' else 1
                        age = int(int(participant['age'][:2]) / 10)
                        pid = int(participant['participantID'][1:]) - 1

                        compress = gender * 10 + age
                        participants[pid] = compress
                        # statistic[compress] += 1

                    # 채팅 추상화 ( [담화자, 텍스트] )
                    dialogues = []
                    prev_talker = -1
                    msg_concat = ''
                    for dialogue in item['body']:
                        # 발화자와 텍스트 파싱
                        talker = int(dialogue['participantID'][1:]) - 1
                        utterance = dialogue['utterance']

                        # 광고/카드결제 메시지가 있을 경우 건너뜀.
                        if 'Web발신' in utterance.lower():
                            continue

                        # 대화 등록
                        if prev_talker >= 0 and prev_talker != talker:
                            msg_concat = re.sub(r'(<SEP>)+', '<SEP>', msg_concat)

                            if msg_concat.endswith('<SEP>'):
                                msg_concat = msg_concat.rstrip('<SEP>')
                            if msg_concat.startswith('<SEP>'):
                                msg_concat = msg_concat.lstrip('<SEP>')

                            if msg_concat != '' and msg_concat != ' ':
                                dialogues.append([talker, msg_concat])
                            msg_concat = ''

                        # 대화 Append
                        msg_concat = msg_concat + '<SEP>' + self.preprocess_message(utterance)
                        prev_talker = talker

                    if msg_concat != '':
                        dialogues.append([prev_talker, msg_concat])

                    multiturn_dataset.append({'participant': participants, 'dialogue': dialogues})
                datas[raw_data.split(".")[0]] = multiturn_dataset

        with open('datasets/aihub/result.json', 'w', encoding='utf-8') as json_output:
            json.dump(datas, json_output, ensure_ascii=False)
