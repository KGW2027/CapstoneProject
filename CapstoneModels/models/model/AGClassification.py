# Age Gender Classification With GPT2forSequenceClassification Class For GPT2-Small

import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import PreTrainedTokenizerFast, GPT2ForSequenceClassification

from models import ModelManager
from models.dataset.aihub import AiHubProcessor, AiHubDataset


class AGClassifier:
    def __init__(self, model_name: str):
        self.tokenizer = AiHubProcessor.add_tokens(PreTrainedTokenizerFast.from_pretrained(model_name))
        self.model = GPT2ForSequenceClassification.from_pretrained(model_name, num_labels=20)
        if model_name == 'skt/kogpt2-base-v2':
            self.tokenizer.add_special_tokens({'bos_token': '</s>', 'eos_token': '</s>', 'unk_token': '<unk>', 'pad_token': '<pad>', 'mask_token':'<mask>', 'sep_token': '<SEP>'})
        self.model.resize_token_embeddings(len(self.tokenizer))

        self.train = None
        self.dev = None
        self.test = None

    def load_ckpt(self, path: str):
        self.tokenizer = PreTrainedTokenizerFast.from_pretrained(path)
        self.model = GPT2ForSequenceClassification.from_pretrained(path, num_labels=20)


    def generate_dataset(self):
        load = AiHubDataset.generate_SNS_dataset(self.tokenizer, use_ratio=0.3)
        self.train = load['train']
        self.dev = load['dev']
        self.test = load['test']

    def view_length_distributes(self, datas):
        AiHubProcessor.view_tokens_length_statistics_sns(datas, self.tokenizer)

    def start_train(self, num_epoch:int = 1, batch_size:int = 32):
        train_loader = DataLoader(self.train, batch_size=batch_size, shuffle=True)
        dev_loader = DataLoader(self.dev, batch_size=batch_size)
        crit = nn.CrossEntropyLoss(weight=self.train.get_weight().cuda())
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-5)

        self.model.cuda()

        for epoch in range(num_epoch):
            epoch_loss = 0.0
            epoch_loss_sum = 0.0
            count = 0

            self.model.train()
            with tqdm(total=len(train_loader), leave=False) as pbar:
                for i, data in enumerate(train_loader):
                    optimizer.zero_grad()
                    text, label = data
                    outputs = self.model(input_ids=text['input_ids'], attention_mask=text['attention_mask'])
                    loss = crit(outputs.logits, label)
                    loss.backward()
                    optimizer.step()

                    epoch_loss_sum += loss
                    count += 1
                    epoch_loss = epoch_loss_sum / count

                    pbar.set_description(f"Epochs {epoch + 1}/{num_epoch} loss : {epoch_loss}")
                    pbar.update(1)

            self.model.eval()
            accuracy = 0.0
            with torch.no_grad():
                correct = 0.0
                total = 0
                with tqdm(total=len(dev_loader), leave=False) as pbar:
                    for i, data in enumerate(dev_loader):
                        text, label = data
                        outputs = self.model(input_ids=text['input_ids'], attention_mask=text['attention_mask'])
                        logit_indices = torch.argmax(outputs.logits, dim=1)
                        label_indices = torch.argmax(label, dim=1)

                        correct += torch.eq(label_indices, logit_indices).sum().item()
                        total += len(label_indices)
                        accuracy = correct / total
                        pbar.set_description(f"Epochs {epoch+1}/{num_epoch} loss : {epoch_loss}, accuracy={accuracy:06.2%}")
                        pbar.update(1)

            print(f"Epoch {epoch}\tLoss {epoch_loss:.4f}\tAccuracy - {accuracy:06.2%}")
        ModelManager.save(self.model, self.tokenizer, 'ag-classifier')

    def start_test(self, batch_size:int = 32):
        test_loader = DataLoader(self.test, batch_size=batch_size)

        self.model.cuda()
        self.model.eval()
        accuracy = 0.0
        with torch.no_grad():
            correct = 0.0
            total = 0
            with tqdm(total=len(test_loader), leave=False) as pbar:
                for i, data in enumerate(test_loader):
                    text, label = data
                    outputs = self.model(input_ids=text['input_ids'], attention_mask=text['attention_mask'])
                    logit_indices = torch.argmax(outputs.logits, dim=1)
                    label_indices = torch.argmax(label, dim=1)

                    correct += torch.eq(label_indices, logit_indices).sum().item()
                    total += len(label_indices)
                    accuracy = correct / total
                    pbar.set_description(f"TEST-Accuracy = {accuracy:06.2%}")
                    pbar.update(1)

        print(f"TEST RESULT :: {accuracy:06.2%}")

    # def generate_answer(self, gender:int, age:int, prompt):
    #     """
    #     AGClassification Model을 이용한 답변 생성 태스크
    #     :param gender: 0-남성, 1-여성
    #     :param age: 2-20대, 3-30대, 4-40대 // 20대에 특화되었으며 30,40도 일부 지원
    #     :param prompt: 프롬프트
    #     :return:
    #     """
    #     encoded_prompt = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors='pt')
    #     generated = self.model.generate(input_ids=encoded_prompt, labels=torch.tensor([gender*10+age]).unsqueeze(0), max_length=128, do_sample=True, top_p=0.95, top_k=50)
    #     output_sentence = self.tokenizer.decode(generated[0], skip_special_tokens=True)
    #
    #     return output_sentence