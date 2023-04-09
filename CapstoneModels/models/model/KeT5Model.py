import gc

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, T5ForConditionalGeneration

from models import ModelManager
from models.dataset.core import UnsupervisedDataset, SummarizeDataset


def split_dataloader(dataloader, length):
    dataloaders = []
    current_start = 0

    print('chunking data_loader')
    while current_start < len(dataloader.dataset):
        indices = list(range(current_start, min(current_start + length, len(dataloader.dataset))))
        subset_sampler = torch.utils.data.SubsetRandomSampler(indices)
        new_dataloader = DataLoader(dataloader.dataset, batch_size=dataloader.batch_size, sampler=subset_sampler)
        dataloaders.append(new_dataloader)
        current_start += length

    print(f'chunked to {len(dataloaders)}')

    return dataloaders

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
        self.optimizer = None

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

    def _internal_train_chunks(self, loader, epoch_info:int, is_eval:bool = False, is_supervised:bool = False, gradient_accumulation_steps:int = 1, chunk_size:int = 10000):

        seps = split_dataloader(loader, chunk_size * loader.batch_size)
        for idx in range(len(seps)):
            desc = f'- Seperate {idx+1}/{len(seps)}'
            if is_eval:
                loss = self._internal_dev(seps[idx], is_supervised=is_supervised, desc=desc)
                print(f'Epochs {epoch_info+1}. Sep-{idx+1} Evaluation Result :: Loss - {loss:.4}')
            else:
                loss = self._internal_train(seps[idx], is_supervised=is_supervised, gradient_accumulation_steps=gradient_accumulation_steps, desc=desc)
                print(f'Epochs {epoch_info+1}. Sep-{idx+1} Train Result :: Loss - {loss:.4}')

            ModelManager.save(self.model, self.tokenizer, self.ckpt_name)
            del self.model
            del self.tokenizer
            gc.collect()

            model_path = ModelManager.load(self.ckpt_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)




    def _internal_train(self, loader, is_supervised:bool, gradient_accumulation_steps:int, desc:str=''):

        self.model.cuda().train()
        loss_sum = 0
        batches = 0

        print(f'\n\t=====> Train Info <=====')
        print(f'Datas : {len(loader) * loader.batch_size:,}')
        print(f'Gradient Accumulation Steps : {gradient_accumulation_steps}')
        print(f'Batch Size : {loader.batch_size}')
        print(f'Effective Batch Size : {gradient_accumulation_steps * loader.batch_size}')
        print(f'Effect Data Size : {len(loader)}')

        self.optimizer.zero_grad()

        for batch in tqdm(loader, desc=desc):
            loss = self._internal_test(batch=batch, is_supervised=is_supervised)
            loss_sum += loss.item()
            loss.backward()

            if batches % gradient_accumulation_steps == 0:
                self.optimizer.step()
            self.optimizer.zero_grad()

        return loss_sum / len(loader)

    def _internal_dev(self, loader, is_supervised:bool = False, desc:str = ''):

        self.model.cuda().eval()
        loss_sum = 0

        with torch.no_grad():
            with tqdm(total=len(loader), leave=False) as pbar:
                for batch in loader:
                    loss = self._internal_test(batch=batch, is_supervised=is_supervised)
                    loss_sum += loss.item()

                    pbar.set_description(f"{desc} :: loss : {loss.item()}")
                    pbar.update(1)

        return loss_sum / len(loader)


    def _internal_train_game(self, num_epochs:int, batch_size:int):
        unsupervised_dataset = self._load_unsupervised_game()
        unsupervised_loader = DataLoader(unsupervised_dataset, batch_size=batch_size, shuffle=True)
        self.optimizer = AdamW(self.model.parameters(), lr=1e-4)

        # unsupervised train
        for epoch in range(num_epochs):
            print(f'[Game-Unsupervised] Epoch {epoch+1:02}')
            self._internal_train_chunks(unsupervised_loader, chunk_size=60000, epoch_info=epoch)


    def _internal_summarize_supervised(self, num_epochs:int, batch_size:int, divide:int):
        batch_size = batch_size // divide
        train, dev = self._load_summaries()
        summarize_train = DataLoader(train, batch_size=batch_size, shuffle=True)
        summarize_dev = DataLoader(dev, batch_size=batch_size)
        self.optimizer = AdamW(self.model.parameters(), lr=5e-6)

        for epoch in range(num_epochs):
            print(f'[Real-Summarize-Supervised] Epoch {epoch+1:02} - Train')
            self._internal_train_chunks(summarize_train, gradient_accumulation_steps=divide, is_supervised=True, chunk_size=30000, epoch_info=epoch)
            print(f'[Real-Summarize-Supervised] Epoch {epoch+1:02} - Dev')
            self._internal_train_chunks(summarize_dev, is_eval=True, is_supervised=True, chunk_size=30000, epoch_info=epoch)



    def start_train(self, batch_size:int = 4, unsupervised_epoch:int = 5, summarize_real_epoch:int = 1):

        # self._internal_train_game(unsupervised_epoch, batch_size)
        self._internal_summarize_supervised(num_epochs=summarize_real_epoch, batch_size=batch_size, divide=4)

