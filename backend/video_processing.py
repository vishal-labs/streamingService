# should check if all the videos in the videos/ folder are of the right format, if not, use ffmpeg wrapper and format them. 
import os
from  ffmpeg import FFmpeg, Progress
from dotenv import load_dotenv


def processVideo(
    video_name: str,
    chunk_size: int = 10,
    videos_dir: str = "videos",
    crf: int = 24,
    preset: str = "veryslow",
    scale: str = "1280:-1",
    on_progress=None,
) -> str:
    stem = os.path.splitext(video_name)[0]

    input_path      = os.path.join(videos_dir, video_name)
    output_dir      = os.path.join(videos_dir, stem)
    m3u8_path       = os.path.join(output_dir, "index.m3u8")
    segment_pattern = os.path.join(output_dir, f"{stem}_%03d.ts")

    os.makedirs(output_dir, exist_ok=True)

    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(input_path)
        .output(
            m3u8_path,
            {"codec:v": "libx264", "codec:a": "aac"}, 
            vf=f"scale={scale}",
            preset=preset,
            crf=crf,
            f="hls",
            hls_time=chunk_size,
            hls_list_size=0,
            hls_segment_filename=segment_pattern,
            hls_playlist_type="vod",
            start_number=0,
        )
    )

    if on_progress:
        @ffmpeg.on("progress")
        def _on_progress(progress: Progress):
            on_progress(progress)

    ffmpeg.execute()
    return os.path.abspath(m3u8_path)
processVideo("testvideo1.mp4")
