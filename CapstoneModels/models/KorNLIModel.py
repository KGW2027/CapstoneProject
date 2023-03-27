import torch.optim
import torch.nn.functional as F
from torch import nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from models import KorporaWrapper

class KorNLIModel:
    def append_train_dev(self, label_map, corpus, train_size: float = 0.9):
        dev_start = len(corpus) * train_size
        for idx in range(len(corpus)):
            self.weight[label_map[corpus[idx].label]] += 1

            if idx < dev_start:
                self.trains.append(corpus[idx])
            else:
                self.evals.append(corpus[idx])

    def make_dataset(self, corpus):
        label_map = {'neutral': 0, 'contradiction': 1, 'entailment': 2}
        self.append_train_dev(label_map, corpus.multinli_train, train_size=0.9)
        self.append_train_dev(label_map, corpus.snli_train, train_size=0.9)
        test_start = len(corpus.xnli_dev) * 0.5
        for idx in range(len(corpus.xnli_dev)):
            if idx < test_start:
                self.weight[label_map[corpus.xnli_dev[idx].label]] += 1
                self.evals.append(corpus.xnli_dev[idx])
            else:
                self.tests.append(corpus.xnli_dev[idx])

        for item in corpus.xnli_test:
            self.tests.append(item)

        self.train_dataset = KorNLIDataset(self.trains, self.tokenizer, self.max_length)
        self.eval_dataset = KorNLIDataset(self.evals, self.tokenizer, self.max_length)
        self.test_dataset = KorNLIDataset(self.tests, self.tokenizer, self.max_length)

    def tokenize(self, pair):
        return self.tokenizer(pair.text, pair.pair, padding="max_length", truncation=True, max_length=self.max_length, return_tensor='pt')

    def execute_model(self, inputs):
        inputs['input_ids'] = inputs['input_ids'].squeeze(1).cuda()
        inputs['attention_mask'] = inputs['attention_mask'].squeeze(1).cuda()

        return self.model(input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'])

    def get_correct(self, logits, labels):
        prob = F.softmax(logits, dim=-1)[:, :3]
        _, indices_logit = torch.max(prob, dim=-1)
        _, indices_label = torch.max(labels, dim=-1)

        return (indices_label == indices_logit).sum().item()


    def __init__(self, model, tokenizer, max_length: int = 64, num_epochs: int = 3, batch_size: int = 16):
        # 기본 설정

        self.model = model
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        
        # Corpus를 불러오고 데이터셋 제작
        self.corpus_name = "kornli"
        corpus = KorporaWrapper.load_corpus(self.corpus_name)
        self.weight = [0] * 3
        self.trains = []
        self.evals = []
        self.tests = []
        self.test_dataset = None
        self.eval_dataset = None
        self.train_dataset = None
        self.make_dataset(corpus)

    def train(self):
        self.model.cuda()

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-6, eps=1e-8)
        sums = sum(self.weight)
        self.weight = [v / sums for v in self.weight]
        print(self.weight)
        crit = nn.CrossEntropyLoss(weight=torch.FloatTensor(self.weight).cuda())

        train_loader = DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True)
        eval_loader = DataLoader(self.eval_dataset, batch_size=self.batch_size, shuffle=True)

        max_accuracy = 0.0

        for epoch in range(self.num_epochs):
            sum_loss = 0.0
            total = 0

            # Train
            self.model.train()
            with tqdm(total=len(train_loader), leave=False) as pbar:
                for _, data in enumerate(train_loader):
                    optimizer.zero_grad()

                    inputs, labels = data
                    labels = labels.cuda()
                    outputs = self.execute_model(inputs)

                    prob = F.softmax(outputs.logits, dim=-1)
                    loss = crit(prob, labels[:, :3].float())
                    loss.backward()
                    optimizer.step()

                    sum_loss += loss
                    total += 1

                    pbar.set_description(f"[TRAIN] Epochs {epoch+1} / {self.num_epochs} :: [LOSS VALUE : {sum_loss / total:.4f}]")
                    pbar.update(1)

            # Evaluation
            self.model.eval()
            total = 0
            correct = 0
            accuracy = 0.0
            with torch.no_grad():
                with tqdm(total=len(eval_loader), leave=False) as pbar:
                    for _, data in enumerate(eval_loader):
                        inputs, labels = data
                        labels = labels.cuda()
                        outputs = self.execute_model(inputs)

                        correct += self.get_correct(outputs.logits, labels)
                        total += outputs.logits.shape[0]
                        accuracy = 100 * correct / total

                        pbar.set_description(f"[EVAL] Epochs {epoch+1} / {self.num_epochs} :: [Accuracy : {accuracy:.2f}%]")
                        pbar.update(1)

            print(f"Epoch {epoch+1} Result :: [ Loss : {sum_loss / total:.4f}, Accuracy : {accuracy:.2f}% ]")
            if accuracy > max_accuracy:
                max_accuracy = accuracy
                KorporaWrapper.save_ckpt(self.corpus_name, epoch, self.model, optimizer)

        print("TRAIN END")

    def test(self):
        self.model.cuda()
        test_loader = DataLoader(self.test_dataset, batch_size=self.batch_size)

        correct = 0
        total = 0
        with tqdm(total=len(test_loader), leave=True) as pbar:
            for _, data in enumerate(test_loader):
                inputs, labels = data
                labels = labels.cuda()
                outputs = self.execute_model(inputs)

                correct += self.get_correct(outputs.logits, labels)
                total += outputs.logits.shape[0]
                accuracy = 100 * correct / total

                pbar.set_description(f"[TEST] :: [Accuracy : {accuracy:.2f}%]")
                pbar.update(1)

        print("TEST END")


class KorNLIDataset(Dataset):
    def encode_one_hot(self, label):
        label_map = {'neutral': 0, 'contradiction': 1, 'entailment': 2}
        return torch.nn.functional.one_hot(torch.tensor(label_map[label]), 3)
    def __init__(self, corpus, tokenizer, max_length):
        self.corpus = corpus
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __getitem__(self, idx):
        dt = self.corpus[idx]
        context = self.tokenizer(dt.text, dt.pair, padding="max_length", truncation=True, max_length=self.max_length, return_tensors='pt')
        label = self.encode_one_hot(dt.label)
        return context, label

    def __len__(self):
        return len(self.corpus)
