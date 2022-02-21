from multiprocessing.sharedctypes import Value
import os
import yt_dlp as youtube_dl
from yt_dlp import DownloadError
from yt_dlp.utils import ExtractorError
import logging
from time import sleep
import soundfile as sf
import numpy as np
import random
import fcntl


logging.basicConfig(
    format=f"%(asctime)s @{os.getpid()} %(levelname)-8s %(message)s",
    level=logging.ERROR,
    datefmt="%B %d, %H:%M:%S",
)

class LoggerYtdlWarnings(object):
    """ Class needed to avoid printing warnings from youtube_dl which cause breaks in the progress bar."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def download_video(ytid, dest, name):
    logging.info(" > download_video")
    ydl_opt = {
        "outtmpl": f"{dest}/{name}.%(ext)s",
        "format": "bestaudio/best",
        "quiet": True,
        "noprogress": True,
        "abort-on-unavailable-fragment": True,
        "logger": LoggerYtdlWarnings(),
        "cookiefile": "./youtube.com_cookies.txt",
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            info = ydl.extract_info(ytid, download=True)
            filename = ydl.prepare_filename(info)
    except (ExtractorError, DownloadError, IOError) as e:
        return ytid, str(e), False

    logging.info(f" {ytid} Downloaded: \t{os.path.basename(filename)}")
    check_duration = info["duration"]

    logging.debug(f" {ytid} Duration: \tconverted audio: {check_duration}s")
    return filename, check_duration, True


def split_samplename(item):
    ytid = item[0]
    start = item[1]
    return ytid, start


def convert_to_audio(
    filename,
    codec="pcm_s16le",
    num_channels=1,
    sampelrate=44100,
    silent=True,
    clear_origin=False,
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
    logging.debug(f"Duration: \tconverted audio: {check_duration}s")

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
    logging.debug(
        f"Trimmed: \t{os.path.basename(filename)} to {os.path.basename(output_file)}"
    )

    os.system(f"rm -rf {filename}")
    logging.warning(f"Removed: \t{os.path.basename(filename)}")

    return output_file


def checking(filename, padded_dir, meta_duration, audio_duration):
    logging.debug(" > checking")
    logging.debug(f"Checking: \t{filename}")
    command = f"sox --i -- {filename}"
    info = os.popen(cmd=command).read()
    check_channel = int(info.strip().split("\n")[1].split(":")[1].strip())
    logging.debug(f"Checking: \tchannels:\t{check_channel}")
    assert (
        check_channel == 1
    ), f"Wrong ch numbers, got {check_channel}, but should be 1 (mono)."
    check_samplerate = int(info.strip().split("\n")[2].split(":")[1].strip())
    logging.debug(f"Checking: \tsamplerate:\t{check_samplerate}")
    assert (
        check_samplerate == 44100
    ), f"Wrong samplerate, got{check_samplerate}, but should be 44100."
    check_precision = info.strip().split("\n")[3].split(":")[1].strip()
    logging.debug(f"Checking: \tprecision:\t{check_precision}")
    assert (
        check_precision == "16-bit"
    ), f"Wrong precision, got{check_precision}, but should be 16-bit."
    check_duration = info.strip().split("\n")[4][16:].strip().split(" = ")
    logging.debug(f"Checking: \tduration:\t{check_duration[0]}")
    assert (
        check_duration[0] == "00:00:10.00"
    ), f"Wrong duration, got {check_duration[0]}, but should be 00:00:10.00."
    assert (
        check_duration[1] == "441000 samples"
    ), f"Wrong duration, got {check_duration[1]}, but should be 441000 samples."

    if meta_duration != audio_duration and abs(meta_duration - audio_duration) < 2:
        output_file = os.path.join(padded_dir, os.path.basename(filename))
        os.system(f"mv {filename} {output_file}")
        logging.debug(f"Different duration: {meta_duration} and {audio_duration}.")
        logging.debug(f"Moved to: \t{output_file}")
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
        info = os.popen(f"rm -fv {filename}").read().strip()
        waveform = np.concatenate((waveform, np.zeros(diff)), axis=0)
        logging.warning(f" > padding {filename} Diff: {diff} Removed: \t{info}")
        filename = os.path.join(padded_dir, os.path.basename(filename))
        with open(filename, "wb") as f:
            sf.write(f, waveform, samplerate)
        return filename


def download_sample(item, save_dir, padded_dir, count):
    ytid, start = split_samplename(item)
    video_file, ytid_duration, sucess = download_video(ytid, save_dir, item[0])
    if sucess:
        audio_file, converted_duration = convert_to_audio(video_file)
        sample_file = trim_audio(audio_file, start)
        sample_file = padding_zeros(sample_file, padded_dir)
        sample_file = checking(sample_file, padded_dir, ytid_duration, converted_duration)
        new_audio_path = os.path.join(os.path.dirname(sample_file), "audio/AudioSet." + os.path.basename(sample_file))
        new_video_path = os.path.join(os.path.dirname(video_file), "video/AudioSet." + os.path.basename(video_file))
        os.system(f"mv '{sample_file}' '{new_audio_path}'")
        os.system(f"mv '{video_file}' '{new_video_path}'")
        logging.info(f"Finished: \t{item[0]}")
        count[0] += 1
        print(f"OK: {count[0]:6d} | NG: {count[1]:6d} | ALL: {count[2]} ({int(((count[0] + count[1]) * 100) / count[2]):-3d}%)", end="\r")
    else:
        logging.info(f"Downloading {ytid} NG. Ometting...")
        count[1] += 1
        print(f"OK: {count[0]:6d} | NG: {count[1]:6d} | ALL: {count[2]} ({int(((count[0] + count[1]) * 100) / count[2]):-3d}%) with {ytid_duration[:80]}", end="\n")
        with open("missing_videos.txt", "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(f"{ytid}\n")


def download_tsv(meta, save_dir, padded_dir, count, sleep_time=0.1):
    if not padded_dir:
        logging.info(
            "Not setting path to save padded files, using the same as save_dir."
        )
        padded_dir = save_dir

    while len(meta):
        item = meta.pop(0)
        logging.info("{:=^72s}".format(item[0]))
        if os.path.exists(os.path.join(save_dir, f"{item[0]}.wav")):
            logging.warning(f"Skipping: \t{item[0]}")
            continue
        if os.path.exists(os.path.join(padded_dir, f"{item[0]}.wav")):
            logging.warning(f"Skipping: \t{item[0]}")
            continue
        try:
            download_sample(item, save_dir=save_dir, padded_dir=padded_dir, count=count)
        except Exception as e:
            sleep(0.3)
            info = os.popen(f"rm -vf -- {save_dir}/{item[0]}*").read()
            info = info.replace("\n", " ")
            logging.warning(f"Temp files removed: {info}")
            # logging.error(f"{e}")
            logging.info(f"Left: \t{len(meta)}")
        # sleep(sleep_time)


if __name__ == "__main__":
    meta_file = (
        "/server20/datasets/AudioSet/fetch-audioset/tsv/unbalanced_train_segments.csv"
    )
    save_dir = "/server20/datasets/AudioSet/fetch-audioset/audiosetdata/original"
    padded_dir = "/server20/datasets/AudioSet/fetch-audioset/audiosetdata/padded"

    save_dir = os.path.join(
        save_dir, os.path.basename(meta_file).replace(".tsv", "").replace(".csv", "")
    )
    padded_dir = os.path.join(
        padded_dir, os.path.basename(meta_file).replace(".tsv", "").replace(".csv", "")
    )
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(save_dir + "/audio", exist_ok=True)
    os.makedirs(save_dir + "/video", exist_ok=True)
    os.makedirs(padded_dir, exist_ok=True)

    with open(meta_file) as f:
        meta = f.readlines()[1:]
        if meta_file.endswith(".tsv"):
            meta = [(line.strip().split("\t")[0]) for line in meta]
            meta = list(set(meta))
        elif meta_file.endswith(".csv"):
            while meta[0][0] == "#":
                meta.pop(0)
            meta = [
                (line.strip().split(", ")[0], int(float(line.strip().split(", ")[1])))
                for line in meta
            ]

    print("AudioSet Script by km4sh")

    with open("missing_videos.txt", "r") as f:
        missing = f.read()
        missing = missing.split("\n")

    temp = set(meta)
    print(f"Original list length: {len(meta)}")
    ytid_dict = {item[0]: item[1] for item in temp}
    missing = set([(item, ytid_dict[item]) for item in missing if len(item) == 11])
    temp = temp - missing
    temp = list(temp)
    print(f"Remove missing videos' id, left {len(temp)}")
    sleep(3)
    meta = []
    for item in temp:
        if os.path.exists(os.path.join(save_dir, "audio", f"AudioSet.{item[0]}.wav")):
            print(f"Skipping: \t{item} | audio", end="\r")
        elif os.path.exists(os.path.join(padded_dir, f"{item[0]}.wav")):
            print(f"Skipping: \t{item} | padded", end="\n")
        else:
            meta.append(item)
    logging.info(f"Downloading meta length: {len(meta)}")
    random.shuffle(meta)
    sleep(1)

    from multiprocessing import Pool, Manager
    manager = Manager()
    count = manager.list()
    count.extend([0, 0, len(meta)])

    num_proc = 32
    star_input = [
        (
            meta[i * len(meta) // num_proc : (i + 1) * len(meta) // num_proc],
            save_dir,
            padded_dir,
            count
        )
        for i in range(num_proc)
    ]

    with Pool(num_proc) as p:
        p.starmap(
            download_tsv, star_input,
        )
        p.close()
        p.join()
    logging.info("ALL FINISHED.")
