# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# T5 모델 학습을 위해서는 sentencepiece와 protobuf==3.20.0 필요
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치
import os
import random

from tqdm import tqdm

import datasets
from models import korEDA, DatasetManager, DataAugmenter
from transformers import AutoTokenizer, T5ForConditionalGeneration
from models.dataset.aihub import AiHubProcessor
from models.dataset.lol import LOLProcessor
from models.dataset.nikl import NIKLProcessor
from models.model import GameSummarization
from models.model.AGLMHeadModel import AGLMHeadModel
from models.model.KeT5Model import KeT5Model
from models.model.GameModel01 import GameLolModel_t1

os.environ['TRANSFORMERS_CACHE'] = './transformers/cache/'

def run_lol01():
    lol01 = GameLolModel_t1(max_length=64, batch_size=16, l_rate=5e-6)
    lol01.load_model('../ptunning/kogpt_lol_complete')
    gens = lol01.generate_text(seed="자운의 말썽쟁이의 이름은")
    for idx in range(len(gens)):
        text = gens[idx].replace('. ', '.\n')
        print(f"결과 {idx+1} ::\n{text}\n")

def loadAIHUB20():
    model = AGLMHeadModel(model_name='skt/kogpt2-base-v2', data_processor=[AiHubProcessor.AiHub20()], load_ckpt=True)
    model.start_train(num_epochs=10, batch_size=32, gradient_checkpointing=False, gradient_accumulation_steps=1)

    gender = 'female'
    age = 20

    test_case = [
        ['질문하기', '오늘 저녁 뭐 먹었어?'],
        ['질문하기', '떡볶이 좋아하니?'],
        ['인사하기', '안녕, 오늘 날씨가 참 좋네'],
        ['부정감정 표현하기', '아.. 진짜 쓰레기같다'],
        ['긍정감정 표현하기', '고마워 친구야'],
        ['약속하기', '오늘 오후 8시에 보는거야'],
        ['거절하기', '아.. 그건 좀 힘들거같은데'],
        ['질문하기', '그 오빠 알아?']
    ]

    print(f'Test case : {gender} / {age}')

    for test in test_case:
        sentences = model.generate_sentence(gender, age, test[0], test[1])
        print(f'Q : {test[1]} / {test[0]}')
        print(f'A : {sentences[random.randint(0, len(sentences)-1)]}')
        print(f'전체 후보 : {sentences}\n')

    gender = 'male'
    age = 20

    print(f'\n\nTest case : {gender} / {age}')

    for test in test_case:
        sentences = model.generate_sentence(gender, age, test[0], test[1])
        print(f'Q : {test[1]} / {test[0]}')
        print(f'A : {sentences[random.randint(0, len(sentences)-1)]}')
        print(f'전체 후보 : {sentences}\n')


    # sentences = model.generate_sentence('female', 20, '질문하기', '오늘 저녁 뭐 먹었어?')
    # print(sentences)

def gpt_test2():
    processor = [
        AiHubProcessor.AiHub20(),
        NIKLProcessor.NiklDialogueProcessor(),
    ]
    model = AGLMHeadModel(model_name='skt/kogpt2-base-v2', data_processor=processor, load_ckpt=True, ckpt_name='aglm2')
    # model.start_train(num_epochs=5, batch_size=32)

    questions = [
        '오늘 저녁은 뭐먹었어?',
        '안녕? 이름이 뭐니?',
        '그 영화 재밌더라',
        '광주 비엔날레 가본적 있어?',
        '<name>이 알아?'
    ]

    personas = [
        ['female', 10],
        ['female', 20],
        ['male', 10],
        ['male', 20]
    ]

    for persona in personas:
        print(f'-----\t----> Persona : Gender : {persona[0]}, Age : {persona[1]} <----\t-----')
        for question in questions:
            sentences = model.generate_sentence(gender=persona[0], age=persona[1], prompt=question)
            print(f'Q : {question}\nA : {sentences[random.randint(0, len(sentences)-1)]}')
            print(f'전체 후보군 : {sentences}\n')

def main():
    processors = [
        LOLProcessor.FandomProcessor(),
        LOLProcessor.UnivProcessor(),
        AiHubProcessor.AiHub22()
    ]
    ket5_lol = KeT5Model(data_processor=processors, load_ckpt=True, ckpt_name='ket5_lol')
    ket5_lol.start_train(batch_size=2, unsupervised_epoch=0, summarize_real_epoch=1)

    hub22 = AiHubProcessor.AiHub22()
    hub22.load()
    t, d = hub22.get()
    print_cases = 1
    for idx in range(print_cases):
        print(f'\n\t=====\t=====> Case {idx+1} <=====\t=====')
        context = d[idx]['context']
        print(f'Context : {context}')
        summarize = ket5_lol.generate_summarize(context)
        print(f'Generated Summarize : {summarize}')

        for sentence in d[idx]['summaries']:
            print(f'Summarize Sentence : {sentence}')

def main2():
    model = GameSummarization.GameSummarizationModel(ckpt_name='game_ust', load_ckpt=False)
    # model.train_game(gradient_step=8, batch_size=2, num_epochs=1, )
    # model.train_summarize(gradient_step=8, batch_size=2, num_epochs=1,)
    # model.test_summarize()
    # model.test_game()
    model.augment_game()


def eda():
    processors = [
        LOLProcessor.FandomProcessor(),
        LOLProcessor.UnivProcessor(),
    ]
    datas = []
    for processor in processors:
        processor.load()
        t, d = processor.get()
        datas += t[0]

    augmented = []
    for data in datas:
        augmented += korEDA.EDA(data)
    random.shuffle(augmented)
    DatasetManager.save_dataset_ckpt('game_augments', augmented)

    print(f'before : {len(datas)}\nafter : {len(augmented)}')

def eda2():
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
        augmented += korEDA.EDA(data, num_aug=4)
    random.shuffle(augmented)
    print(f'{len(datas)} -> {len(augmented)}')
    DatasetManager.save_dataset_ckpt('game_augments', augmented)


eda2()
# DataAugmenter.augment_with_gpt()