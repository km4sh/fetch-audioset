import os
import sys
import soundfile as sf
from tqdm import tqdm

if len(sys.argv) != 2:
    raise 'Please specify one path to clean.'
clean_list = []
for root, _, files in os.walk(sys.argv[1]):
    if len(files):
        for f in tqdm(files):
            if f.endswith(".wav"):
                try:
                    command = f"sox --i -- {os.path.join(root, f)}"
                    info = os.popen(cmd=command).read()
                    assert len(info.strip().split("\n")) == 8, "EMPTY FILE."
                    check_duration = info.strip().split("\n")[4][16:].strip().split(" = ")
                    assert (
                        check_duration[0] == "00:00:10.00"
                    ), f"Wrong duration, got {check_duration[0]}, but should be 00:00:10.00."

                    assert (
                        check_duration[1] == "441000 samples"
                    ), f"Wrong duration, got {check_duration[1]}, but should be 441000 samples."

                except Exception as e:
                    clean_list.append(os.path.join(root, f))
                    tqdm.write(f"{root}/{f:30s}:{e}")
            else:
                clean_list.append(os.path.join(root, f))
                tqdm.write(f"{root}/{f:30s}:NOT A WAVE FILE.")

t = input(f"Find {len(clean_list)} to clean, are you sure? [y/n] ").strip()
if t == "y" or t == "Y":
    for f in tqdm(clean_list):
        os.system(f'rm -f {f}')
print("FINISHED.")
