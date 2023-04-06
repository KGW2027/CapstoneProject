# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치
import os
import random

from models.dataset import AiHubProcessor
from models.model.AGLMHeadModel import AGLMHeadModel

os.environ['TRANSFORMERS_CACHE'] = './transformers/cache/'

from models.model.GameModel01 import GameLolModel_t1

def run_lol01():
    lol01 = GameLolModel_t1(max_length=64, batch_size=16, l_rate=5e-6)
    lol01.load_model('../ptunning/kogpt_lol_complete')
    gens = lol01.generate_text(seed="자운의 말썽쟁이의 이름은")
    for idx in range(len(gens)):
        text = gens[idx].replace('. ', '.\n')
        print(f"결과 {idx+1} ::\n{text}\n")

def main():
    model = AGLMHeadModel(model_name='skt/kogpt2-base-v2', data_processor=AiHubProcessor.AiHub20(), load_ckpt=True)
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

main()