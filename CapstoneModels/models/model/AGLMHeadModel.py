import math

from transformers import GPT2LMHeadModel, TrainingArguments, Trainer, IntervalStrategy, \
    GPT2TokenizerFast

from models import ModelManager
from models.dataset import AiHubProcessor, AiHubDataset, AiHubCollator


class AGLMHeadModel:
    def __init__(self, model_name: str):
        self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
        self.tokenizer.add_tokens(['<AG>'] + list(AiHubProcessor.emotes.keys()))
        self.model = GPT2LMHeadModel.from_pretrained(model_name, use_cache=False)
        if model_name == 'skt/kogpt2-base-v2':
            self.tokenizer.add_special_tokens({'bos_token': '</s>', 'eos_token': '</s>', 'unk_token': '<unk>', 'pad_token': '<pad>', 'mask_token':'<mask>', 'sep_token': '<s>'})
        self.model.resize_token_embeddings(len(self.tokenizer))

        self.train = None
        self.dev = None
        self.test = None

    def load_ckpt(self, path: str):
        self.tokenizer = GPT2TokenizerFast.from_pretrained(path)
        self.model = GPT2LMHeadModel.from_pretrained(path, use_cache=False)
        self.model.resize_token_embeddings(len(self.tokenizer))

    def generate_dataset(self):
        load = AiHubDataset.generate_SNS_dataset(self.tokenizer, use_ratio=0.4)
        self.train = load['train']
        self.dev = load['dev']
        self.test = load['test']

    def start_train(self, num_epochs: int = 1, batch_size: int = 32, gradient_accumulation_steps: int = 2, gradient_checkpointing:bool = True):
        # collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=True, mlm_probability=0.15)
        train_collator = AiHubCollator.SNSMaskCollator(tokenizer=self.tokenizer, mlm_probability=0.15)

        train_args = TrainingArguments(
            output_dir='G:/trains/AGLMHeadModel/',
            learning_rate=1e-5,
            save_strategy=IntervalStrategy.NO,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=num_epochs,
            weight_decay=1e-3,
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
            train_dataset=self.train,
            data_collator=train_collator,
            # data_collator=collator
        )

        trainer.train()

        ModelManager.save(tokenizer=self.tokenizer, model=self.model, name='aglm2')

    def generate_sentence(self, gender: str, age: int, prompt):
        ag = (0 if gender.lower() == 'male' else 1) * 10 + math.floor(age / 10)
        context = f'{prompt} <AG> {ag} </s>'
        input_ids = self.tokenizer.encode(context, return_tensors='pt')

        output = self.model.generate(input_ids=input_ids,
                                     max_length=128,
                                     repetition_penalty=2.0,
                                     pad_token_id=self.tokenizer.pad_token_id,
                                     eos_token_id=self.tokenizer.eos_token_id,
                                     bos_token_id=self.tokenizer.bos_token_id,
                                     do_sample=True,
                                     temperature=0.7,
                                     top_k=50
                                     )
        response = self.tokenizer.decode(output[0], skip_special_tokens=False)
        response = response.replace('<HELLO>', 'ㅎㅇ').replace('<SORRY>', 'ㅈㅅ').replace('<SCARE>', 'ㄷㄷ').replace('<SAD>', 'ㅠㅠ')

        return response