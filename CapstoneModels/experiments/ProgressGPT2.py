import math

from transformers import AutoTokenizer, TrainingArguments, \
    Trainer, DataCollatorForLanguageModeling, AutoModelForCausalLM

from experiments.Datasets import GameDialogueDataset
from models import DatasetManager, ModelManager
from models.dataset.core import UnsupervisedDataset


class MoreTrainGPT2:
    tokenizer = None
    model = None
    def __init__(self):
        self.load()

    def load(self, model_path:str = "skt/kogpt2-base-v2"):
        if model_path != "skt/kogpt2-base-v2":
            model_path = ModelManager.load(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, bos_token='</s>', eos_token='</s>', unk_token='<unk>', pad_token='<pad>', mask_token='<mask>')
        self.model = AutoModelForCausalLM.from_pretrained(model_path)

    def dataset(self):
        ckpts = [
            'game_augments',
            'game_summarizes',
            'gpt2_augment',
            'fandom-lol-train',
            'univ-lol-train'
        ]
        datasets = []
        for ckpt in ckpts:
            dsm = DatasetManager.load_dataset_ckpt(ckpt)
            if type(dsm[0]) is list:
                dsm = dsm[0]
            datasets += dsm

        cut = math.floor(len(datasets)*0.9)
        return datasets[:cut], datasets[cut:]

    def pre_train(self):
        self.load()
        t, d = self.dataset()

        trains = UnsupervisedDataset(tokenizer=self.tokenizer, corpus=t)
        dev = UnsupervisedDataset(tokenizer=self.tokenizer, corpus=d)
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, return_tensors='pt')

        train_args = TrainingArguments(
            adafactor=True,
            output_dir='G:/trains/train_game_gpt2',
            per_device_train_batch_size=2,
            gradient_accumulation_steps=16,
            num_train_epochs=1,

            learning_rate=1e-6,
            weight_decay=0.01,
            warmup_steps=2000,
            warmup_ratio=0.02,

            do_eval=True,
            eval_steps=1000,
            save_steps=1000,
            save_total_limit=3,
            logging_steps=500,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=trains,
            eval_dataset=dev,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        trainer.train()
        ModelManager.save(self.model, self.tokenizer, 'train_game_gpt2')

    def pretrain_test(self):
        self.load('train_game_gpt2')
        t, d = self.dataset()
        for idx in range(5):
            context = f'{d[idx]}라는 질문에 대해 20대 여성의 말투로 답변하라.'
            print(f'Context : {context}')
            token = self.tokenizer.encode(context, return_tensors='pt')
            output_tokens = self.model.generate(
                token,
                max_length=256,
                # num_beams=5,
                # no_repeat_ngram_size=2,

                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                top_k=10,
                num_return_sequences=3,

                early_stopping=True,
            )
            for output in output_tokens:
                decodes = self.tokenizer.decode(output, skip_special_tokens=True)
                print(decodes)

    def train_dialogue(self, new_train:bool = True, N_EPOCH:int = 20):
        path = 'train_game_gpt2' if new_train else f'train_dialogue_gpt2'
        self.load(path)
        trains = GameDialogueDataset(self.tokenizer, form='gpt2')
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, return_tensors='pt')

        train_args = TrainingArguments(
            # adafactor=True,
            output_dir='G:/trains/train_dialogue_gpt2',
            per_device_train_batch_size=4,
            gradient_accumulation_steps=8,
            num_train_epochs=N_EPOCH,

            learning_rate=1e-4,
            weight_decay=0.01,
            # warmup_steps=2000,
            # warmup_ratio=0.02,

            save_steps=500,
            save_total_limit=3,
            logging_steps=300,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=trains,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        trainer.train()
        ModelManager.save(self.model, self.tokenizer, 'train_dialogue_gpt2')

    def test_dialogue(self, question:str, age:int = 2, is_male:bool = True):
        self.load('train_dialogue_gpt2')
        gender = '남성' if is_male else '여성'
        input_text = f'{question}라는 질문에 대해 {age}0대 {gender}의 말투로 답변하라.'

        print(f'Prompt ->\t{input_text}')

        inputs = self.tokenizer.encode(input_text, return_tensors='pt')
        self.model = self.model.cuda()
        inputs = inputs.cuda()
        output_tokens = self.model.generate(
            inputs,
            max_length=128,

            no_repeat_ngram_size=1,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            top_k=5,
            num_return_sequences=3,

            early_stopping=True,
        )

        for output in output_tokens:
            decodes = self.tokenizer.decode(output, skip_special_tokens=True)
            print(decodes)



mgpt2 = MoreTrainGPT2()
#mgpt2.pre_train()
#mgpt2.pretrain_test()
mgpt2.train_dialogue(new_train=True, N_EPOCH=20)
mgpt2.test_dialogue('아이오니아는 어떤 곳입니까?', age=5, is_male=True)
mgpt2.test_dialogue('아이오니아는 어떤 곳입니까?', age=3, is_male=False)
mgpt2.test_dialogue('아이오니아는 어떤 곳입니까?', age=2, is_male=True)