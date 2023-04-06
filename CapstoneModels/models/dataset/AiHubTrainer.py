import re

import torch
from transformers import Trainer


class AgActTrainer(Trainer):
    def __init__(self, model, args, train_dataset, eval_dataset, data_collator, tokenizer):
        super().__init__(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )
        ag_counts = dict(
            {'13': 101008, '2': 304262, '12': 159823, '3': 231398, '11': 7823, '5': 21505, '1': 3365, '4': 39559,
             '16': 5535, '15': 4647, '14': 36115, '6': 9277})
        act_counts = dict(
            {'0': 233440, '1': 521134, '2': 331718, '3': 6968, '4': 33322, '5': 15900, '16': 3291, '6': 3125, '7': 4582,
             '8': 3226, '9': 6212, '10': 2085, '11': 5852, '12': 471, '13': 54, '14': 550, '15': 1017})

        total_ag_samples = sum(ag_counts.values())
        total_act_samples = sum(act_counts.values())
        self.ag_weights = {ag: total_ag_samples / count for ag, count in ag_counts.items()}
        self.act_weights = {act: total_act_samples / count for act, count in act_counts.items()}
        self.tokenizer = tokenizer

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        # Create a mask with weights for each example based on ag or act
        mask = []
        for example in inputs["input_ids"]:
            text = self.tokenizer.decode(example[0])
            ag = re.findall('\d+<act>', text)[0].replace('<act>', '')
            act = re.findall('\d+<response>', text)[0].replace('<response>', '')

            ag_weight = self.ag_weights.get(ag, 1.0)
            act_weight = self.act_weights.get(act, 1.0)

            # Combine ag and act weights (you can choose other strategies to combine weights)
            weight = ag_weight + act_weight
            mask.append(weight)

        mask = torch.tensor(mask, device=self.args.device).unsqueeze(1)

        # Compute the weighted loss
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        loss = loss_fct(logits.view(-1, logits.shape[-1]), labels.view(-1))
        loss = loss.view_as(mask)
        loss = (loss * mask).mean()

        return (loss, outputs) if return_outputs else loss