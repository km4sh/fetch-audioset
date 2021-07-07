import os
from random import sample
from numpy.lib.npyio import save
import youtube_dl
import logging
from time import sleep
import soundfile as sf
import numpy as np
from multiprocessing import active_children

logging.basicConfig(
    format=f"%(asctime)s @{os.getpid()} %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%B %d, %H:%M:%S",
)


def download_video(ytid, dest, name):
    logging.info(" > download_video")
    ydl_opt = {
        "outtmpl": f"{dest}/{name}.%(ext)s",
        "format": "bestaudio/best",
        "quiet": True,
        "abort-on-unavailable-fragment": True,
        "cookiefile": "/Users/er1yaaruma/Downloads/youtube.com_cookies.txt",
    }
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        info = ydl.extract_info(ytid, download=True)
        filename = ydl.prepare_filename(info)

    logging.info(f"Downloaded: \t{os.path.basename(filename)}")
    check_duration = info["duration"]

    logging.info(f"Duration: \tconverted audio: {check_duration}s")
    return filename, check_duration


def split_samplename(item):
    ytid = item[:11]
    start = item[12:]
    return ytid, start


def convert_to_audio(
    filename,
    codec="pcm_s16le",
    num_channels=1,
    sampelrate=44100,
    silent=True,
    clear_origin=True,
):
    logging.info(" > convert_to_audio")
    output_pre, _ = os.path.splitext(filename)
    output_file = output_pre + "_temp.wav"

    ffmpeg_command = f"ffmpeg -i {filename} -hide_banner"
    ffmpeg_command += f" -acodec {codec}"
    ffmpeg_command += f" -ac {num_channels}"
    ffmpeg_command += f" -ar {sampelrate}"
    ffmpeg_command += f" {output_file}"
    if silent:
        ffmpeg_command += " 2> /dev/null"
    os.system(ffmpeg_command)

    logging.info(
        f"Converted: \t{os.path.basename(filename)} to {os.path.basename(output_file)}"
    )

    if clear_origin:
        os.system(f"rm -rf {filename}")
        logging.warning(f"Removed: \t{os.path.basename(filename)}")

    command = f"sox --i -- {output_file}"
    info = os.popen(cmd=command).read()

    check_duration = info.strip().split("\n")[4][16:].strip().split(" = ")
    check_duration = round(int(check_duration[1].strip().split(" ")[0]) / sampelrate)
    logging.info(f"Duration: \tconverted audio: {check_duration}s")

    return output_file, check_duration


def trim_audio(filename, start, silent=True):
    logging.info(" > trim_audio")
    seek_head = int(start) // 1000
    start_time = f"{seek_head // 3600}:{(seek_head % 3600) // 60}:{seek_head % 60}"
    output_file = filename.replace("_temp", "")
    sox_command = f"sox {filename} {output_file}"
    sox_command += f" trim {start_time} 10"
    if silent:
        sox_command += " 2> /dev/null"
    os.system(sox_command)
    logging.info(
        f"Trimmed: \t{os.path.basename(filename)} to {os.path.basename(output_file)}"
    )

    os.system(f"rm -rf {filename}")
    logging.warning(f"Removed: \t{os.path.basename(filename)}")

    return output_file


def checking(filename, padded_dir, meta_duration, audio_duration):
    logging.info(" > checking")
    logging.info(f"Checking: \t{filename}")
    command = f"sox --i -- {filename}"
    info = os.popen(cmd=command).read()
    check_channel = int(info.strip().split("\n")[1].split(":")[1].strip())
    logging.info(f"Checking: \tchannels:\t{check_channel}")
    assert (
        check_channel == 1
    ), f"Wrong ch numbers, got {check_channel}, but should be 1 (mono)."
    check_samplerate = int(info.strip().split("\n")[2].split(":")[1].strip())
    logging.info(f"Checking: \tsamplerate:\t{check_samplerate}")
    assert (
        check_samplerate == 44100
    ), f"Wrong samplerate, got{check_samplerate}, but should be 44100."
    check_precision = info.strip().split("\n")[3].split(":")[1].strip()
    logging.info(f"Checking: \tprecision:\t{check_precision}")
    assert (
        check_precision == "16-bit"
    ), f"Wrong precision, got{check_precision}, but should be 16-bit."
    check_duration = info.strip().split("\n")[4][16:].strip().split(" = ")
    logging.info(f"Checking: \tduration:\t{check_duration[0]}")
    assert (
        check_duration[0] == "00:00:10.00"
    ), f"Wrong duration, got {check_duration[0]}, but should be 00:00:10.00."
    assert (
        check_duration[1] == "441000 samples"
    ), f"Wrong duration, got {check_duration[1]}, but should be 441000 samples."

    if meta_duration != audio_duration and abs(meta_duration - audio_duration) < 2:
        output_file = os.path.join(padded_dir, os.path.basename(filename))
        os.system(f"mv {filename} {output_file}")
        logging.warning(f"Different duration: {meta_duration} and {audio_duration}.")
        logging.warning(f"Moved to: \t{output_file}")
    elif meta_duration != audio_duration:
        raise AssertionError
    else:
        output_file = filename
    return output_file


def padding_zeros(filename, padded_dir, samplerate=44100, duration=10):
    waveform, samplerate = sf.read(filename)
    diff = samplerate * duration - waveform.shape[0]
    if diff == 0:
        return filename
    else:
        logging.warning(" > padding")
        logging.warning(f"Diff: {diff}")
        info = os.popen(f"rm -fv {filename}").read().strip()
        logging.warning(f"Removed: \t{info}")
        waveform = np.concatenate((waveform, np.zeros(diff)), axis=0)
        filename = os.path.join(padded_dir, os.path.basename(filename))
        with open(filename, "wb") as f:
            sf.write(f, waveform, samplerate)
        return filename


def download_sample(item, save_dir, padded_dir):
    ytid, start = split_samplename(item)
    video_file, ytid_duration = download_video(ytid, save_dir, item)
    audio_file, converted_duration = convert_to_audio(video_file)
    sample_file = trim_audio(audio_file, start)
    sample_file = padding_zeros(sample_file, padded_dir)
    sample_file = checking(sample_file, padded_dir, ytid_duration, converted_duration)
    logging.info(f"Finished: \t{item}")


def download_tsv(meta, save_dir, padded_dir=None, sleep_time=0.1):
    if not padded_dir:
        logging.info("Not setting path to save padded files, using the same as save_dir.")
        padded_dir = save_dir

    while len(meta):
        item = meta.pop(0)
        logging.info("{:=^72s}".format(item))
        if os.path.exists(os.path.join(save_dir, f"{item}.wav")):
            logging.warning(f"Skipping: \t{item}")
            continue
        if os.path.exists(os.path.join(padded_dir, f"{item}.wav")):
            logging.warning(f"Skipping: \t{item}")
            continue
        try:
            download_sample(item, save_dir=save_dir, padded_dir=padded_dir)
        except Exception as e:
            sleep(1)
            info = os.popen(f"rm -vf -- {save_dir}/{item[:11]}*").read()
            info = info.replace("\n", " ")
            logging.warning(f"Temp files removed: {info}")
            logging.error(f"{e}")
            logging.info(f"Left: \t{len(meta)}")
        sleep(sleep_time)


if __name__ == "__main__":
    tsv_file = "/Volumes/Blue500a/AudioSet/audioset_eval_strong.tsv"
    save_dir = "/Volumes/Blue500a/AudioSet/strong_label_eval"
    padded_dir = "/Volumes/Blue500a/AudioSet/strong_label_eval_padded"

    os.makedirs(padded_dir, exist_ok=True)

    with open(tsv_file) as f:
        meta = f.readlines()[1:]
        meta = [line.strip().split("\t")[0] for line in meta]
        meta = list(set(meta))

    print("AudioSet Script by km4sh")

    temp = meta
    meta = []
    for item in temp:
        if os.path.exists(os.path.join(save_dir, f"{item}.wav")):
            print(f"Skipping: \t{item}", end="\r")
        elif os.path.exists(os.path.join(padded_dir, f"{item}.wav")):
            print(f"Skipping: \t{item}", end="\r")
        else:
            meta.append(item)

    logging.info(f"Downloading meta length: {len(meta)}")

    sleep(3)

    from multiprocessing import Pool

    num_proc = 8
    star_input = [
        (
            meta[i * len(meta) // num_proc : (i + 1) * len(meta) // num_proc],
            save_dir,
            padded_dir,
        )
        for i in range(num_proc)
    ]
    with Pool(num_proc) as p:
        p.starmap(
            download_tsv,
            star_input,
        )
        p.close()
        p.join()
    logging.info("ALL FINISHED.")
