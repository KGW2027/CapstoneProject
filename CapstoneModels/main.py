# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치

import torch
from transformers import AlbertForSequenceClassification, BertTokenizerFast, ElectraForSequenceClassification, ElectraTokenizer

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
    model_name = "monologg/koelectra-base-v3-discriminator"
    tokenizer = ElectraTokenizer.from_pretrained(model_name)
    lol01 = GameLolModel_t1(tokenizer)


run_lol01()
# run_nli()