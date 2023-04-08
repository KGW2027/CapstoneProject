# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# T5 모델 학습을 위해서는 sentencepiece와 protobuf==3.20.0 필요
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치
import os
import random

from models.dataset.aihub import AiHubProcessor
from models.dataset.nikl import NIKLProcessor
from models.model.AGLMHeadModel import AGLMHeadModel
from models.model.KeT5Model import KeT5Model

os.environ['TRANSFORMERS_CACHE'] = './transformers/cache/'

from models.model.GameModel01 import GameLolModel_t1

def run_lol01():
    lol01 = GameLolModel_t1(max_length=64, batch_size=16, l_rate=5e-6)
    lol01.load_model('../ptunning/kogpt_lol_complete')
    gens = lol01.generate_text(seed="자운의 말썽쟁이의 이름은")
    for idx in range(len(gens)):
        text = gens[idx].replace('. ', '.\n')
        print(f"결과 {idx+1} ::\n{text}\n")

def loadAIHUB20():
    model = AGLMHeadModel(model_name='skt/kogpt2-base-v2', data_processor=[AiHubProcessor.AiHub20()], load_ckpt=True)
    # model.start_train(num_epochs=10, batch_size=32, gradient_checkpointing=False, gradient_accumulation_steps=1)

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
    KeT5Model()

main()