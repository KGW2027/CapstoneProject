from transformers import AutoTokenizer, T5ForConditionalGeneration


class KeT5Model:
    def __init__(self):
        model_path = "KETI-AIR/ke-t5-base"

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)