import os


def save(model, tokenizer, name):
    path = 'G:/trains/'+name+'/'
    os.makedirs(path, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)

def load(name):
    return 'G:/trains/'+name+'/'
