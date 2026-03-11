# should check if all the videos in the videos/ folder are of the right format, if not, use ffmpeg wrapper and format them. 
import os
import ffmpeg



def processVideo(videoName: str) -> None:
    stream = ffmpeg.input(videoName)

    stream = ffmpeg.output(
        stream,
        '720_out.m3u8',
        vcodec='libx264',
        acodec='aac',
        s='720x1280',
        aspect='16:9',
        format='hls',
        hls_list_size=1000000,
        hls_time=2,
        strict='experimental'
    )

    ffmpeg.run(stream)