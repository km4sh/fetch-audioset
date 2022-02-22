import os
import soundfile as sf


def post_process(meta, count):
    original_path = "./audiosetdata/original/unbalanced_train_segments/audio"
    padded_path = "./audiosetdata/padded/unbalanced_train_segments/audio"
    new_wav_dir = "./audiosetdata/wav"
    new_flac_dir = "./audiosetdata/flac"
    os.makedirs(new_wav_dir, exist_ok=True)
    os.makedirs(new_flac_dir, exist_ok=True)

    original_text = []
    padded_text = []
    from tqdm import tqdm
    for ytid, suffix in meta:
        if os.path.exists(os.path.join(original_path, f"AudioSet.{ytid}.wav")):
            old_path = os.path.join(original_path, f"AudioSet.{ytid}.wav")
            data, sr = sf.read(old_path)
            if len(data) != 441000:
                with open("./bad.txt", "a") as f:
                    f.write(f"{old_path}\n")
                continue
            new_name = f"Y{ytid}{suffix}.wav"
            new_path = os.path.join(new_wav_dir, new_name)
            if not os.path.exists(new_path):
                sf.write(new_path, data, sr, subtype="PCM_16")
            new_name = f"Y{ytid}{suffix}.flac"
            new_path = os.path.join(new_flac_dir, new_name)
            if not os.path.exists(new_path):
                sf.write(new_path, data, sr)
            original_text.append(new_name)
            count[0] += 1
        elif os.path.exists(os.path.join(padded_path, f"AudioSet.{ytid}.wav")):
            old_path = os.path.join(padded_path, f"AudioSet.{ytid}.wav")
            data, sr = sf.read(old_path)
            if len(data) != 441000:
                with open("./bad.txt", "a") as f:
                    f.write(f"{old_path}\n")
                continue
            new_name = f"Y{ytid}{suffix}.wav"
            new_path = os.path.join(new_wav_dir, new_name)
            if not os.path.exists(new_path):
                sf.write(new_path, data, sr, subtype="PCM_16")
            new_name = f"Y{ytid}{suffix}.flac"
            new_path = os.path.join(new_flac_dir, new_name)
            if not os.path.exists(new_path):
                sf.write(new_path, data, sr)
            original_text.append(new_name)
            count[1] += 1
        print(f"Processing :: unpadded: {count[0]:8d} padded: {count[1]:8d} | Left: {count[2] - count[0] - count[1]} {((count[0] + count[1]) * 100 / count[2]):8.4f}%")
    with open("./unpadded_samples.txt", "w") as f:
        f.write("\n".join(original_text))
    with open("./unpadded_samples.txt", "w") as f:
        f.write("\n".join(padded_text))

from multiprocessing import Pool, Manager

meta_file = (
    "/server20/datasets/AudioSet/fetch-audioset/tsv/unbalanced_train_segments.csv"
)
with open(meta_file) as f:
    meta = f.readlines()[1:]
    if meta_file.endswith(".tsv"):
        meta = [(line.strip().split("\t")[0]) for line in meta]
        meta = list(set(meta))
    elif meta_file.endswith(".csv"):
        while meta[0][0] == "#":
            meta.pop(0)
        meta = [
            (line.strip().split(", ")[0], line.strip().split(", ")[1], line.strip().split(", ")[2])
            for line in meta
        ]

meta = [(item[0], f"_{item[1]}_{item[2]}") for item in meta]

manager = Manager()
count = manager.list()
count.extend([0, 0, len(meta)])

num_proc = 64
star_input = [
    (
        meta[i * len(meta) // num_proc : (i + 1) * len(meta) // num_proc],
        count
    )
    for i in range(num_proc)
]

with Pool(num_proc) as p:
    p.starmap(post_process, star_input)
    p.close()
    p.join()