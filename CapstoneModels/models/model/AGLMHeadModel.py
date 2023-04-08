import math
import re

from transformers import GPT2LMHeadModel, TrainingArguments, Trainer, IntervalStrategy, \
    GPT2TokenizerFast, DataCollatorForLanguageModeling

from models import ModelManager
from models.dataset.core import UnsupervisedDataset


class AGLMHeadModel:
    def __init__(self, model_name: str, data_processor: list, load_ckpt:bool = False, ckpt_name:str = 'aglm'):
        if load_ckpt:
            path = ModelManager.load(ckpt_name)
            self.tokenizer = GPT2TokenizerFast.from_pretrained(path)
            self.model = GPT2LMHeadModel.from_pretrained(path, use_cache=False)
        else:
            # Initial Load
            self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
            self.model = GPT2LMHeadModel.from_pretrained(model_name, use_cache=False)

            # Key Tuning
            if model_name == 'skt/kogpt2-base-v2':
                self.tokenizer.add_special_tokens({'bos_token': '</s>', 'eos_token': '</s>', 'unk_token': '<unk>', 'pad_token': '<pad>', 'mask_token':'<mask>', 'sep_token': '<s>'})
            self.tokenizer.add_special_tokens({'additional_special_tokens': ['<ag>', '<act>', '<response>']})

            before_length = len(self.tokenizer)
            for processor in data_processor:
                new_tokens = processor.tokens()
                print(f'add new tokens : {len(new_tokens)}')
                self.tokenizer.add_tokens(new_tokens)
            self.model.resize_token_embeddings(len(self.tokenizer))
            print(f'Changed Tokenizer Length : {before_length} -> {len(self.tokenizer)}')
        print(f'tokenizer length : {len(self.tokenizer)}')

        self.processors = data_processor
        self.ckpt_name = ckpt_name

    def load_processors(self):
        train = []
        dev = []

        for processor in self.processors:
            processor.load()
            t, d = processor.get()
            train += t
            dev += d

        return train, dev

    def start_train(self, num_epochs: int = 1, batch_size: int = 32, gradient_accumulation_steps: int = 1, gradient_checkpointing:bool = False):

        train, dev = self.load_processors()
        collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

        train_dataset = UnsupervisedDataset(train, tokenizer=self.tokenizer, max_length=128)

        train_args = TrainingArguments(
            output_dir='G:/',
            learning_rate=1e-5,
            save_strategy=IntervalStrategy.NO,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=num_epochs,
            weight_decay=0,
            push_to_hub=False,
            do_eval=False,
            fp16=True,
            gradient_accumulation_steps=gradient_accumulation_steps,
            gradient_checkpointing=gradient_checkpointing,
            logging_steps=10000,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=train_dataset,
            data_collator=collator,
        )

        trainer.train()
        ModelManager.save(tokenizer=self.tokenizer, model=self.model, name=self.ckpt_name)

    def generate_sentence(self, gender: str, age: int, prompt:str):
        '''
        모델을 이용해 문장 생성
        :param gender: male / female
        :param age: 십의 자리수만 체크, (20~29 -> 20대, 30~39 -> 30대)
        :param prompt: 입력값
        :return:
        '''
        ag = (0 if gender.lower() == 'female' else 1) * 10 + math.floor(age / 10)
        context = f'{prompt}<ag>{ag}<response> '
        input_ids = self.tokenizer.encode(context, return_tensors='pt')

        output = self.model.generate(input_ids=input_ids,
                                     num_return_sequences = 4,
                                     max_length=64,
                                     no_repeat_ngram_size=2,
                                     temperature=1.0,
                                     do_sample=True,
                                     top_k=50,
                                     top_p=0.92,
                                     )
        response = []
        for sentence in output:
            sentence = self.tokenizer.decode(sentence, skip_special_tokens=False)
            sentence = sentence.replace('<bored>', '').replace('<scare>', 'ㄷㄷ').replace('<laugh>', 'ㅋㅋ').replace('<sad>', 'ㅠㅠ').replace('<unk>', '')
            sentence = re.findall('<response>([^<]*)', sentence)[0].strip()
            response.append(sentence)

        return response