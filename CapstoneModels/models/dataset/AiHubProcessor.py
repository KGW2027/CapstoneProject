import json
import math
import os
import re
from collections import defaultdict

from tqdm import tqdm

import GraphGenerator

emotes = {
    "<laugh>": r'(?!ㄱ)[ㅋㄱ]+|[ㅋㅎ]+|(ㅋㅅㅋ)',
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

emote_keys = ['<laugh>', '<surprise>', '<weak_abuse>', '<strong_abuse>', '<wait>', '<ty>', '<no>', '<ok>', '<expect>', '<sry>', '<hurry>',
              '<sad>', '<scare>', '<celebrate>', '<run>', '<why>', '<go>', '<bored>', '<bye>', '<hello>']

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

    def preprocess_message(self, message):
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

    def merge_data(self):
        path_dir = 'datasets/aihub/'

        datas = {'2': [], '3': [], '12': [], '13': []}
        limit = 500000

        for raw_data in os.listdir(path_dir):
            if raw_data.startswith('result'):
                continue

            with open(path_dir + raw_data, "r", encoding='utf-8') as read_json:
                print(f"Start load {raw_data}")
                json_data = json.load(read_json)['data']
                for item in tqdm(json_data):

                    # 대화 참가자 추상화 ( 성별 : 남성은 0, 여성은 1, 나이 : 10대 단위로 자름 )
                    participants = {}
                    for participant in item['header']['participantsInfo']:
                        gender = participant['gender']
                        gender = 0 if gender == '남성' else 1
                        age = int(int(participant['age'][:2]) / 10)
                        pid = int(participant['participantID'][1:]) - 1

                        compress = gender * 10 + age
                        participants[pid] = compress

                    # 채팅 추상화 ( [담화자, 텍스트] )
                    # 같은 화자의 텍스트는 <s>를 사이에 두고 concatenation한다.
                    # 서로 다른 화자의 텍스트 2개를 묶고, 사이에는 </s>를 넣는다.
                    sep_token = '<s>'
                    ag_token = '<ag>'
                    end_token = '</s>'

                    cont_talker = -1
                    prev_msg = ''
                    now_msg = ''
                    last_msg_time = -9999

                    for dialogue in item['body']:
                        # 발화자와 텍스트 파싱
                        talker = int(dialogue['participantID'][1:]) - 1
                        utterance = dialogue['utterance'].lower()
                        msg_time = int(dialogue['time'][:2]) * 60 + int(dialogue['time'][3:5])
                        if last_msg_time == -9999:
                            last_msg_time = msg_time

                        # 광고/카드결제 메시지가 있을 경우 건너뜀.
                        if 'web발신' in utterance:
                            continue

                        # 대화 등록
                        time_gap = msg_time - last_msg_time
                        if time_gap < 0:
                            time_gap += (60*24)

                        if cont_talker != talker or (cont_talker == talker and time_gap >= 30):
                            if now_msg == '':
                                prev_msg = ''
                            elif prev_msg == '':
                                prev_msg = now_msg
                                now_msg = ''
                            else:
                                ag_value = str(participants[talker])
                                if ag_value not in datas.keys():
                                    continue
                                if len(datas[ag_value]) > limit:
                                    continue
                                concat = prev_msg + ' ' + ag_token + ag_value + end_token + now_msg
                                datas[ag_value].append(concat)
                                prev_msg = now_msg if cont_talker != talker else ''
                                now_msg = ''

                        # 대화 Append
                        new_msg = self.preprocess_message(utterance)
                        if new_msg != '':
                            now_msg = (now_msg + ' ' + new_msg) if now_msg != '' else new_msg
                        cont_talker = talker
                        last_msg_time = msg_time

                    if now_msg != '' and prev_msg != '':
                        concat = prev_msg + ' ' + ag_token + ag_value + end_token + now_msg
                        if ag_value not in datas.keys():
                            continue
                        if len(datas[ag_value]) > limit:
                            continue
                        datas[ag_value].append(concat)

        for key, value in datas.items():
            print(f'{key} : {len(value)}')
        with open('datasets/aihub/result.json', 'w', encoding='utf-8') as json_output:
            json.dump(datas, json_output, ensure_ascii=False)
