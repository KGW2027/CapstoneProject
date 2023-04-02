import os


def save(model, tokenizer, name):
    path = 'ckpt/'+name+'/'
    os.makedirs(path, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)
