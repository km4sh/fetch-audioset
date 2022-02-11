from tqdm import tqdm
import os
from time import sleep

meta_file = "/server20/datasets/AudioSet/fetch-audioset/tsv/unbalanced_train_segments.csv"
save_dir = "/server20/datasets/AudioSet/fetch-audioset/audiosetdata/original"
save_dir = os.path.join(
    save_dir, os.path.basename(meta_file).replace(".tsv", "").replace(".csv", "")
)
save_dir += "/audio"
with open(meta_file, "r") as f:
    total = len(f.readlines()[3:])
pbar = tqdm(total=total)
current = len(os.listdir(save_dir))
pbar.update(current)
while True:
    sleep(1)
    prev = current
    current = len(os.listdir(save_dir))
    diff = current - prev
    pbar.update(diff)
pbar.close()

