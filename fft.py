import librosa
from moviepy import VideoFileClip, clips_array
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean
import os



sr = 22050
hop_length = 512
n_fft = 2048  # frame 하나당 sample 수
frequencies = np.fft.rfftfreq(n_fft, 1 / sr)




def get_magnitude(sig, sr):

    stft = librosa.stft(sig, n_fft=n_fft, hop_length=hop_length)


    magnitude = np.abs(stft)

    return magnitude


def magnitude_to_peak_frequency(magnitude):
    peak_freqs = []

    for mag in magnitude.T:
        peak_idx = np.argmax(mag)
        peak_freqs.append(frequencies[peak_idx])

    return peak_freqs

def get_best_offset(main_peak_freqs, sub_peak_freqs):


    min_distance = float('inf')
    best_offset = -1

    for offset in range(0, len(main_peak_freqs) - len(sub_peak_freqs)):

        sliced_origin_peak_freqs = main_peak_freqs[offset: offset + len(sub_peak_freqs)]

        dist = euclidean(sliced_origin_peak_freqs, sub_peak_freqs)
        if dist < min_distance:
            min_distance = dist
            best_offset = offset


    return best_offset

def get_time_diff_list(video_list):
    main_magnitude = None
    main_peak_freqs = None
    time_diff_list = []

    project_name = video_list[0].filename.split("/")[-3]

    main_sig = None
    for idx, video in enumerate(video_list):

        pre_audio_file_list = os.listdir(f"project/{project_name}/audio")
        video_file_name = video.filename.split("/")[-1]
        audio_file_name = video_file_name.replace("mp4", "mp3")
        if audio_file_name not in pre_audio_file_list:
            video.audio.write_audiofile(f"project/{project_name}/audio/{audio_file_name}")

        sig, _ = librosa.load(
            rf"project/{project_name}/audio/{audio_file_name}",
            sr=sr)

        if idx == 0:
            main_sig = sig
            main_magnitude = get_magnitude(sig, sr)
            main_peak_freqs = magnitude_to_peak_frequency(main_magnitude)
            time_diff_list.append(0)
            continue
        else:
            sub_sig_len = sig.shape[0]
            sub_part_sig = sig[int(sub_sig_len * 0.4): int(sub_sig_len * 0.4) + sr * 3]

            sub_magnitude = get_magnitude(sub_part_sig, sr)
            sub_peak_freqs = magnitude_to_peak_frequency(sub_magnitude)

            best_offset = get_best_offset(main_peak_freqs, sub_peak_freqs)
            sig_cnt_diff = best_offset * hop_length - int(sub_sig_len * 0.4)
            duration_diff = sig_cnt_diff / sr

            print(f"video: {video_file_name}, best_offset: {best_offset}, duration_diff: {duration_diff}")
            time_diff_list.append(duration_diff)

    return time_diff_list, get_beat_times(main_sig)


def get_beat_times(sig):
    tempo, beat_frames = librosa.beat.beat_track(y=sig, sr=sr)

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return beat_times