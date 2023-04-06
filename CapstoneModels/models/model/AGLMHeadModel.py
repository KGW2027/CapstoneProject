import math
import re

from transformers import GPT2LMHeadModel, TrainingArguments, Trainer, IntervalStrategy, \
    GPT2TokenizerFast, DataCollatorForLanguageModeling

from models import ModelManager
from models.dataset import AiHubProcessor
from models.dataset.AiHubDataset import AiHub20Dataset
from models.dataset.AiHubProcessor import DataProcessor


class AGLMHeadModel:
    def __init__(self, model_name: str, data_processor: DataProcessor, load_ckpt:bool = False, ckpt_name:str = 'aglm'):
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
            self.tokenizer.add_tokens(list(AiHubProcessor.emotes.keys()))
            self.model.resize_token_embeddings(len(self.tokenizer))

        self.processor = data_processor
        self.ckpt_name = ckpt_name

    def start_train(self, num_epochs: int = 1, batch_size: int = 32, gradient_accumulation_steps: int = 2, gradient_checkpointing:bool = True):

        self.processor.load()
        train, dev = self.processor.get()
        collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

        train_dataset = AiHub20Dataset(train, self.tokenizer)
        dev_dataset = AiHub20Dataset(dev, self.tokenizer, train_mode=False)

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
            logging_steps=3000,
        )

        trainer = Trainer(
            model=self.model,
            args=train_args,
            train_dataset=train_dataset,
            eval_dataset=dev_dataset,
            data_collator=collator,
            # tokenizer=self.tokenizer
        )

        trainer.train()
        ModelManager.save(tokenizer=self.tokenizer, model=self.model, name=self.ckpt_name)

    def generate_sentence(self, gender: str, age: int, talk_type: str, prompt):
        '''
        모델을 이용해 문장 생성
        :param gender: male / female
        :param age: 십의 자리수만 체크, (20~29 -> 20대, 30~39 -> 30대)
        :param talk_type: '질문하기', '주장하기', '진술하기', '턴토크 사인', '충고제안하기', '약속하기', '명령요구하기',
        '부탁하기', '반박하기', '긍정감정 표현하기', '감사하기', '부정감정 표현하기', '거절하기', '위협하기', '사과하기', '인사하기'
        :param prompt: 입력값
        :return:
        '''
        ag = (0 if gender.lower() == 'female' else 1) * 10 + math.floor(age / 10)
        act = AiHubProcessor.aihub20_acts[talk_type]
        context = f'{prompt} <ag> {ag}<act> {act}<response> '
        input_ids = self.tokenizer.encode(context, return_tensors='pt')

        output = self.model.generate(input_ids=input_ids,
                                     num_return_sequences = 4,
                                     max_length=64,
                                     return_dict_in_generate=True,
                                     temperature=0.9,
                                     do_sample=True,
                                     top_k=50,
                                     top_p=0.92,
                                     )
        response = []
        remove = f'{prompt}  {ag} {act} '
        for sentence in output['sequences']:
            sentence = self.tokenizer.decode(sentence, skip_special_tokens=False)
            sentence = sentence.replace('<bored>', '').replace('<scare>', 'ㄷㄷ').replace('<laugh>', 'ㅋㅋ').replace('<sad>', 'ㅠㅠ').replace('<unk>', '')
            sentence = re.findall('<response>([^<]*)', sentence)[0].strip()
            response.append(sentence)

        return response