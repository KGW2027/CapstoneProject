# PyTorch Install : pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
# Transformer Install : pip install transformers==4.10.0
# 그 외에 tqdm(progress_bar), Korpora(Korean dataset) 설치
import os

os.environ['TRANSFORMERS_CACHE'] = './transformers/cache/'

from models.model.GameModel01 import GameLolModel_t1


def run_lol01():
    lol01 = GameLolModel_t1(max_length=64, batch_size=16, l_rate=5e-6)
    # lol01 = GameLolModel_t1()
    lol01.load_model('../ptunning/kogpt_lol_complete')
    # lol01.add_train_data()

    # lol01.print_distribution()
    # lol01.pretrain(num_epoch=10, save_step=30000, warm_up=25000)

    gens = lol01.generate_text(seed="자운의 말썽쟁이의 이름은")
    for idx in range(len(gens)):
        text = gens[idx].replace('. ', '.\n')
        print(f"결과 {idx+1} ::\n{text}\n")

