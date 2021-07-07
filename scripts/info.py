import os

os.makedirs("./info", exist_ok=True)

tsv_file = "../tsv/audioset_train_strong.tsv"
save_dir = "../wavs/strong_label_train"
padded_dir = "../wavs/strong_label_train_padded"
with open(tsv_file) as f:
    meta = f.readlines()[1:]
    meta = [line.strip().split("\t")[0] for line in meta]
    meta = list(set(meta))

temp = meta
content_normal = []
content_padded = []
content_failed = []
for item in temp:
    if os.path.exists(os.path.join(save_dir, f"{item}.wav")):
        content_normal.append(f"{item}\n")
    elif os.path.exists(os.path.join(padded_dir, f"{item}.wav")):
        content_padded.append(f"{item}\n")
    else:
        content_failed.append(f"{item}\n")

with open("../info/train_normal.txt", "w") as f:
    f.writelines(content_normal)
with open("./info/train_padded.txt", "w") as f:
    f.writelines(content_padded)
with open("./info/train_failed.txt", "w") as f:
    f.writelines(content_failed)

tsv_file = "../tsv/audioset_eval_strong.tsv"
save_dir = "../wavs/strong_label_eval"
padded_dir = "../wavs/strong_label_eval_padded"
with open(tsv_file) as f:
    meta = f.readlines()[1:]
    meta = [line.strip().split("\t")[0] for line in meta]
    meta = list(set(meta))

temp = meta
content_normal = []
content_padded = []
content_failed = []
for item in temp:
    if os.path.exists(os.path.join(save_dir, f"{item}.wav")):
        content_normal.append(f"{item}\n")
    elif os.path.exists(os.path.join(padded_dir, f"{item}.wav")):
        content_padded.append(f"{item}\n")
    else:
        content_failed.append(f"{item}\n")

with open("../info/eval_normal.txt", "w") as f:
    f.writelines(content_normal)
with open("../info/eval_padded.txt", "w") as f:
    f.writelines(content_padded)
with open("../info/eval_failed.txt", "w") as f:
    f.writelines(content_failed)

