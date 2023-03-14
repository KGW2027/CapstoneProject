import os.path

import torch
from Korpora import Korpora

root_dir_prefix = "./datasets/"

def load_corpus(dataset_name):
    path = root_dir_prefix+dataset_name
    print(f"{path}에 {dataset_name} 다운로드")
    Korpora.fetch(dataset_name, root_dir=path)
    return Korpora.load(dataset_name, root_dir=path)

def save_ckpt(dataset_name, epoch, model, optimizer):
    print(f"{dataset_name}'s EPOCH_{epoch+1} checkpoint saving...")

    path = f'./ckpt/{dataset_name}/ckpt_{epoch+1}.pth'
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, path)

    print(f"{dataset_name}'s EPOCH_{epoch+1} checkpoint save complete!")