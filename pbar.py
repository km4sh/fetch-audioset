from more_itertools import padded
from tqdm import tqdm
import os
from time import sleep
from ffcount import ffcount

meta_file = "/server20/datasets/AudioSet/fetch-audioset/tsv/unbalanced_train_segments.csv"
original_dir = "/server20/datasets/AudioSet/fetch-audioset/audiosetdata/original"
original_dir = os.path.join(
    original_dir, os.path.basename(meta_file).replace(".tsv", "").replace(".csv", "")
)
original_dir += "/audio"
padded_dir = "/server20/datasets/AudioSet/fetch-audioset/audiosetdata/padded"
padded_dir = os.path.join(
    padded_dir, os.path.basename(meta_file).replace(".tsv", "").replace(".csv", "")
)
with open(meta_file, "r") as f:
    total = len(f.readlines()[3:])
pbar = tqdm(total=total)
current = ffcount(original_dir)[0] + ffcount(padded_dir)[0]
pbar.update(current)
while True:
    sleep(60)
    prev = current
    current = ffcount(original_dir)[0] + ffcount(padded_dir)[0]
    diff = current - prev
    pbar.update(diff)
