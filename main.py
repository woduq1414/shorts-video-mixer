import random

import librosa
from moviepy import VideoFileClip, clips_array, concatenate_videoclips, CompositeVideoClip, vfx, TextClip, afx
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean

from fft import get_time_diff_list, get_beat_times

# project_name = "patisiel"
project_name = "discord"

# video 리스트 가져오기

import os

video_file_list = os.listdir(f"project/{project_name}/video")
video_list = [
    VideoFileClip(f"project/{project_name}/video/{video}").resized(width=720, height=1280)
    for video in video_file_list
]
video_list = sorted(video_list, key=lambda x: -x.duration)
sub_list = video_list[1:]
random.seed(1101)
random.shuffle(sub_list)
video_list = [video_list[0]] + sub_list

time_diff_list, beat_times = get_time_diff_list(video_list)

is_using_first_audio = True


def make_parallel_video(video_list, time_diff_list):
    for idx, video in enumerate(video_list):

        new_video = video.with_start(time_diff_list[idx])
        if idx != 0:
            new_video = new_video.without_audio()
        video_list[idx] = new_video

    combined = clips_array(
        [video_list]
    )

    combined.write_videofile(f"project/{project_name}/output/parallel.mp4", threads=10, fps=24, preset='ultrafast')


def make_crossed_video(video_list: list[VideoFileClip], time_diff_list, beat_times):
    concated = []

    longest_video_duration = max([video.duration for video in video_list])

    # longest_video_duration = 6

    clip_start, clip_end = 0, 0
    origin_t = beat_times[0]
    # interval = (beat_times[1] - beat_times[0]) * 4

    # def get average interval

    interval = 0
    for i in range(1, len(beat_times)):
        interval += beat_times[i] - beat_times[i - 1]
    interval /= len(beat_times) - 1

    interval *= 4
    print(interval, "interval")

    f = True
    prev_info = {}
    while f and clip_end < longest_video_duration:
        for idx, video in enumerate(video_list):
            clip_start = origin_t - time_diff_list[idx]
            clip_end = min(origin_t + interval - time_diff_list[idx] + 0.6, video.duration)
            if clip_start >= video.duration or clip_start < 0:

                continue

            if prev_info.get("idx") == idx and prev_info.get("clip_start") == clip_start and prev_info.get(
                    "clip_end") == clip_end:
                f = False
                break
            prev_info = {"clip_start": clip_start, "clip_end": clip_end, "idx": idx}
            if clip_end - clip_start < 0.4:
                continue
            print(f"clip_start: {clip_start}, clip_end: {clip_end}, idx: {idx}")


            video_clip = video.subclipped(clip_start, clip_end).with_start(origin_t - beat_times[0]).with_effects(
                [vfx.CrossFadeIn(0.4), vfx.CrossFadeOut(0.4)])
            video_file_name = video.filename.split("/")[-1]
            video_author = "__".join(video_file_name.split("@")[1].split("__")[:-1])

            #
            txt_clip = TextClip(
                text="@" + video_author, font=r"NanumYeBbeunMinGyeongCe.ttf",
                color='#FFFFFF88',
                font_size=80, method='caption', text_align='center', size=(720, 400),
            )
            txt_clip = txt_clip.with_position('center').with_duration(clip_end - clip_start).with_start(
                origin_t - beat_times[0]).with_effects([vfx.CrossFadeIn(0.4), vfx.CrossFadeOut(0.4)])

            # Overlay the text clip on the first video clip

            concated.append(video_clip)
            concated.append(txt_clip)

            origin_t += clip_end - clip_start - 0.6

            if clip_end >= longest_video_duration:
                f = False
                break

    if is_using_first_audio:
        final_video = CompositeVideoClip(concated)
        final_audio = video_list[0].audio
        final = final_video.with_audio(final_audio)

    else:
        final = CompositeVideoClip(concated)

    final = final.with_effects([vfx.FadeIn(1), vfx.FadeOut(2), afx.AudioFadeOut("00:00:02")])

    final.write_videofile(f"project/{project_name}/output/mixed.mp4", threads=10, fps=30, preset='ultrafast',
                          ffmpeg_params=["-loglevel", "quiet"])


make_crossed_video(video_list, time_diff_list, beat_times)
exit()
