# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치

import torch
from transformers import AlbertForSequenceClassification, BertTokenizerFast
from models.KorSTSModel import KorSTSModel


model_name = "kykim/albert-kor-base"
model = AlbertForSequenceClassification.from_pretrained(model_name, num_labels=1)
tokenizer = BertTokenizerFast.from_pretrained(model_name)
sts = KorSTSModel(model, tokenizer, batch_size=8, shuffle=True, max_seq_len=64)

optimizer = torch.optim.AdamW(model.parameters(), lr=5e-6, eps=1e-8)
sts.train(optimizer, num_epochs=10)
