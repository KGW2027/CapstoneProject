# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치
import os

os.environ['TRANSFORMERS_CACHE'] = './transformers/cache/'

import torch
from transformers import AlbertForSequenceClassification, BertTokenizerFast, ElectraForSequenceClassification, \
    ElectraTokenizer

from models.KorNLIModel import KorNLIModel
from models.KorSTSModel import KorSTSModel
from models.GameModel01 import GameLolModel_t1

def run_sts():
    model_name = "kykim/albert-kor-base"
    model = AlbertForSequenceClassification.from_pretrained(model_name, num_labels=1)
    tokenizer = BertTokenizerFast.from_pretrained(model_name)
    sts = KorSTSModel(model, tokenizer, batch_size=8, shuffle=True, max_seq_len=64)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-6, eps=1e-8)
    sts.train(optimizer, num_epochs=10)

def run_nli():
    # https://github.com/KLUE-benchmark/KLUE#baseline-scores 를 참고한 결과
    # base 크기에서 NLI, STS 성능이 가장 좋은 모델이 KoELECTRA 로 보이므로, KoELECTRA를 사용하여 진행

    model_name = "monologg/koelectra-base-v3-discriminator"
    model = ElectraForSequenceClassification.from_pretrained(model_name, num_labels=3)
    tokenizer = ElectraTokenizer.from_pretrained(model_name)
    nli = KorNLIModel(model, tokenizer)

    nli.train()
    nli.test()

def run_lol01():
    lol01 = GameLolModel_t1(max_length=64, batch_size=16, l_rate=5e-6)
    # lol01 = GameLolModel_t1()
    lol01.load_model('../ptunning/kogpt_lol_complete')
    # lol01.add_train_data()

    # lol01.print_distribution()
    # lol01.pretrain(num_epoch=10, save_step=30000, warm_up=25000)

    gens = lol01.generate_text(seed="자운의 말썽쟁이의 이름은")
    for idx in range(len(gens)):
        text = gens[idx].replace('. ', '.\n')
        print(f"결과 {idx+1} ::\n{text}\n")



run_lol01()
# run_nli()