# Define mask tokens function
from typing import Optional, Any, Tuple

import torch
from transformers import DataCollatorForLanguageModeling, PreTrainedTokenizer




# Define data collator
class SNSMaskCollator(DataCollatorForLanguageModeling):
    def __init__(self, tokenizer, mlm_probability):
        super().__init__(tokenizer=tokenizer, mlm_probability=mlm_probability)
        self.tokenizer = tokenizer
        self.ag_token = '<ag>'

    def torch_mask_tokens(self, inputs: Any, special_tokens_mask: Optional[Any] = None) -> Tuple[Any, Any]:
        """
        Prepare masked tokens inputs/labels for masked language modeling: 80% MASK, 10% random, 10% original.
        """
        import torch

        labels = inputs.clone()
        # We sample a few tokens in each sequence for MLM training (with probability `self.mlm_probability`)
        probability_matrix = torch.full(labels.shape, self.mlm_probability)
        if special_tokens_mask is None:
            special_tokens = self.tokenizer.all_special_tokens
            special_tokens.append(self.ag_token)
            special_tokens = [self.tokenizer(token)['input_ids'][0] for token in special_tokens]
            special_tokens_mask = [
                [token in special_tokens for token in val] for val in labels.tolist()
            ]
            special_tokens_mask = torch.tensor(special_tokens_mask, dtype=torch.bool)
        else:
            special_tokens_mask = special_tokens_mask.bool()

        probability_matrix.masked_fill_(special_tokens_mask, value=0.0)
        masked_indices = torch.bernoulli(probability_matrix).bool()
        labels[~masked_indices] = -100  # We only compute loss on masked tokens (-100인 label은 mlm check를 하지 않음)

        # 80% of the time, we replace masked input tokens with tokenizer.mask_token ([MASK])
        indices_replaced = torch.bernoulli(torch.full(labels.shape, 0.8)).bool() & masked_indices
        inputs[indices_replaced] = self.tokenizer.convert_tokens_to_ids(self.tokenizer.mask_token)

        # 10% of the time, we replace masked input tokens with random word
        indices_random = torch.bernoulli(torch.full(labels.shape, 0.5)).bool() & masked_indices & ~indices_replaced
        random_words = torch.randint(len(self.tokenizer), labels.shape, dtype=torch.long)
        inputs[indices_random] = random_words[indices_random]

        # The rest of the time (10% of the time) we keep the masked input tokens unchanged
        return inputs, labels

