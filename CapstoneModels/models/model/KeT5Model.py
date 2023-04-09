import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, T5ForConditionalGeneration

from models import ModelManager
from models.dataset.core import UnsupervisedDataset, SummarizeDataset


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
        self.optimizer = AdamW(self.model.parameters(), lr=1e-4)

    def _load_unsupervised_game(self):
        unsupervised = []
        for processor in self.processors:
            if 'game_unsupervised' not in processor.get_tags():
                continue
            processor.load()
            t, d = processor.get()
            unsupervised += t

        return UnsupervisedDataset(tokenizer=self.tokenizer, corpus=unsupervised, max_length=128, stride=32, name='ket5_lol_unsupervised')

    def _load_summaries(self):
        test = []
        dev = []
        for processor in self.processors:
            if 'real_summarize' not in processor.get_tags():
                continue
            processor.load()
            t, d = processor.get()
            test += t
            dev += d

        testset = SummarizeDataset(tokenizer=self.tokenizer, corpus=test, name='ket5_summarize_train', context_max_length= 512, answer_max_length=128)
        devset = SummarizeDataset(tokenizer=self.tokenizer, corpus=dev, name='ket5_summarize_dev', context_max_length= 512, answer_max_length=128)
        return testset, devset

    def _internal_test(self, batch, is_supervised):
        iid = torch.stack(batch['input_ids'], dim=0).transpose(0, 1).cuda()
        msk = torch.stack(batch['attention_mask'], dim=0).transpose(0, 1).cuda()

        if is_supervised:
            lid = torch.stack(batch['label_ids'], dim=0).transpose(0, 1).cuda()
            lam = torch.stack(batch['label_attention_mask'], dim=0).transpose(0, 1).cuda()
            output = self.model(
                input_ids=iid,
                attention_mask=msk,
                labels=lid,
                decoder_attention_mask=lam,
            )
        else:
            output = self.model(
                input_ids=iid,
                attention_mask=msk,
                labels=iid,
            )

        return output.loss

    def _internal_train(self, loader, is_supervised:bool = False, gradient_accumulation_steps:int = 1):

        self.model.cuda().train()
        loss_sum = 0
        batches = 0

        for batch in tqdm(loader):
            if gradient_accumulation_steps == 1:
                self.optimizer.zero_grad()

            loss = self._internal_test(batch=batch, is_supervised=is_supervised)
            loss_sum += loss
            batches += 1
            loss.backward()

            if batches % gradient_accumulation_steps == 0:
                self.optimizer.step()
            if gradient_accumulation_steps > 1:
                self.optimizer.zero_grad()

        print(f'Final eval avg loss : {loss_sum / batches}')

    def _internal_dev(self, loader, is_supervised:bool = False):

        self.model.cuda().eval()
        loss_sum = 0
        batches = 0

        with torch.no_grad():
            with tqdm(total=len(loader), leave=False) as pbar:
                for batch in loader:
                    loss = self._internal_test(batch=batch, is_supervised=is_supervised)
                    loss_sum += loss.item()
                    batches += 1

                    pbar.set_description(f"loss : {loss.item()}")
                    pbar.update(1)

        print(f'Final eval avg loss : {loss_sum / batches}')


    def _internal_train_game(self, num_epochs:int, batch_size:int):
        unsupervised_dataset = self._load_unsupervised_game()
        unsupervised_loader = DataLoader(unsupervised_dataset, batch_size=batch_size, shuffle=True)

        # unsupervised train
        for epoch in range(num_epochs):
            print(f'[Game-Unsupervised] Epoch {epoch+1:02}')
            self._internal_train(unsupervised_loader)


    def _internal_summarize_supervised(self, num_epochs:int, batch_size:int, divide:int):
        batch_size = batch_size // divide
        train, dev = self._load_summaries()
        summarize_train = DataLoader(train, batch_size=batch_size, shuffle=True)
        summarize_dev = DataLoader(dev, batch_size=batch_size)

        for epoch in range(num_epochs):
            print(f'[Real-Summarize-Supervised] Epoch {epoch+1:02} - Train')
            self._internal_train(summarize_train, gradient_accumulation_steps=divide, is_supervised=True)
            print(f'[Real-Summarize-Supervised] Epoch {epoch+1:02} - Dev')
            self._internal_dev(summarize_dev, is_supervised=True)

        pass




    def start_train(self, batch_size:int = 4, unsupervised_epoch:int = 5, summarize_real_epoch:int = 3):

        # self._internal_train_game(unsupervised_epoch, batch_size)
        self._internal_summarize_supervised(num_epochs=summarize_real_epoch, batch_size=batch_size, divide=4)

        # ModelManager.save(self.model, self.tokenizer, self.ckpt_name)

