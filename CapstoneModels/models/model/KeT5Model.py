import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, T5ForConditionalGeneration

from models import ModelManager
from models.dataset.core import UnsupervisedDataset
from models.dataset.lol import LOLProcessor


class KeT5Model:
    def __init__(self, data_processor: list, load_ckpt:bool = False, ckpt_name:str = 'ket5_qna'):
        if load_ckpt:
            model_path = ModelManager.load(ckpt_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        else:
            model_path = "KETI-AIR/ke-t5-base"
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)

        self.processors = data_processor
        self.ckpt_name = ckpt_name

    def load_unsupervised_dataset(self):
        unsupervised = []
        for processor in self.processors:
            if not processor.is_unsupervised():
                continue
            processor.load()
            t, d = processor.get()
            unsupervised += t

        return UnsupervisedDataset(tokenizer=self.tokenizer, corpus=unsupervised, max_length=128, stride=32, name='ket5_lol_unsupervised')

    def start_unsupervised_train(self, loader, optimizer):

        self.model.cuda().train()

        for batch in tqdm(loader):
            optimizer.zero_grad()

            iid_orig = torch.stack(batch['input_ids'], dim=0).transpose(0, 1)
            msk_orig = torch.stack(batch['attention_mask'], dim=0).transpose(0, 1)
            iid = iid_orig.cuda()
            msk = msk_orig.cuda()

            output = self.model(
                input_ids=iid,
                attention_mask=msk,
                labels=iid,
                return_dict=True
            )

            loss = output.loss
            loss.backward()
            optimizer.step()


    def start_train(self, unsupervised_epoch:int = 5, unsupervised_batch_size:int = 16):

        unsupervised_dataset = self.load_unsupervised_dataset()
        unsupervised_loader = DataLoader(unsupervised_dataset, batch_size=unsupervised_batch_size)
        optimizer = AdamW(self.model.parameters(), lr=1e-4)

        # unsupervised train
        for epoch in range(unsupervised_epoch):
            print(f'Epoch {epoch+1:02}')
            self.start_unsupervised_train(unsupervised_loader, optimizer)

        ModelManager.save(self.model, self.tokenizer, self.ckpt_name)

