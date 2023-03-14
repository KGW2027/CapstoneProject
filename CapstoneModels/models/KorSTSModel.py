import torch
from torch.utils.data import Dataset, DataLoader
from torch import nn
from tqdm import tqdm
from models import KorporaWrapper


class KorSTSModel:
    def __init__(self, model, tokenizer, max_seq_len: int = 64, batch_size: int = 8, shuffle: bool = True):
        self.model = model
        model.hidden_dropout_prob=0.1
        model.attention_probs_drop_prob=0.1
        model.classifier_dropout_prob=0.1
        self.tokenizer = tokenizer
        self.dataset_name = "korsts"
        corpus = KorporaWrapper.load_corpus(self.dataset_name)

        self.batch_size = batch_size
        self.shuffle = shuffle

        self.train_dataset = KorSTSDataset(corpus.train, tokenizer, max_seq_len)
        self.dev_dataset = KorSTSDataset(corpus.dev, tokenizer, max_seq_len)
        self.test_dataset = KorSTSDataset(corpus.test, tokenizer, max_seq_len)


    def train(self, optimizer, num_epochs: int):
        train_loader = DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=self.shuffle)
        dev_loader = DataLoader(self.dev_dataset, batch_size=self.batch_size, shuffle=self.shuffle)
        crit = nn.MSELoss()

        self.model.cuda()

        for epoch in range(num_epochs):
            epoch_loss = 0.0
            epoch_loss_sum = 0.0
            count = 0

            self.model.train()
            with tqdm(total=len(train_loader), leave=False) as pbar:
                for i, data in enumerate(train_loader):
                    optimizer.zero_grad()

                    inputs, labels = data
                    inputs['input_ids'] = inputs['input_ids'].squeeze(1).cuda()
                    inputs['attention_mask'] = inputs['attention_mask'].squeeze(1).cuda()
                    labels = labels.cuda()

                    outputs = self.model(input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'])
                    clamp = torch.clamp(outputs.logits, min=0.0, max=5.0)
                    loss = crit(clamp, labels)
                    loss.backward()
                    optimizer.step()

                    epoch_loss_sum += loss
                    count += 1
                    epoch_loss = epoch_loss_sum / count

                    pbar.set_description(f"Epochs {epoch+1}/{num_epochs} :: loss : {epoch_loss}")
                    pbar.update(1)

            self.model.eval()
            with torch.no_grad():
                dev_loss = 0.0
                dev_loss_sum = 0.0
                count = 0
                with tqdm(total=len(dev_loader), leave=False) as pbar:
                    for i, data in enumerate(dev_loader):

                        inputs, labels = data
                        inputs['input_ids'] = inputs['input_ids'].squeeze(1).cuda()
                        inputs['attention_mask'] = inputs['attention_mask'].squeeze(1).cuda()
                        labels = labels.cuda()

                        outputs = self.model(input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'])
                        clamp = torch.clamp(outputs.logits, min=0.0, max=5.0)
                        loss = crit(clamp, labels)

                        dev_loss_sum += loss
                        count += 1
                        dev_loss = dev_loss_sum / count

                        pbar.set_description(f"Epochs {epoch+1}/{num_epochs} [DEV] :: loss : {dev_loss}")
                        pbar.update(1)

            print(f"Epoch {epoch+1} RESULT :: Loss {epoch_loss:.4f}, Dev_loss {dev_loss:.4f}")
            KorporaWrapper.save_ckpt(self.dataset_name, epoch, self.model, optimizer)


class KorSTSDataset(Dataset):
    def __init__(self, corpus, tokenizer, max_length):
        self.corpus = corpus
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __getitem__(self, index):
        data = self.corpus[index]
        context = self.tokenizer(data.text, data.pair, padding="max_length", truncation=True, max_length=self.max_length, return_tensors='pt')
        label = torch.FloatTensor([data.label])
        return context, label

    def __len__(self):
        return len(self.corpus.texts)