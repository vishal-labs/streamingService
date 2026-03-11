# should check if all the videos in the videos/ folder are of the right format, if not, use ffmpeg wrapper and format them. 
import os
import ffmpeg


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR  = os.path.join(BASE_DIR, "inputs")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")


def process_video(video_name: str) -> None:
    video_path = os.path.join(INPUTS_DIR, video_name)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    stem = os.path.splitext(video_name)[0]           # "testvideo1.mp4" → "testvideo1"

    output_dir   = os.path.join(OUTPUTS_DIR, stem)   # outputs/testvideo1/
    segments_dir = os.path.join(output_dir, "segments")
    os.makedirs(segments_dir, exist_ok=True)


    stream = ffmpeg.input(video_path)

    stream = ffmpeg.output(
        stream,
        os.path.join(output_dir, "manifest.m3u8"),
        vcodec="libx264",
        acodec="aac",
        hls_time=2,
        s="1280x720",
        aspect="16:9",
        format="hls",
        hls_list_size=0,
        g=48,
        keyint_min=48,
        sc_threshold=0,
        hls_segment_filename=f"{segments_dir}/seg_%03d.ts"
    )

    ffmpeg.run(stream)

process_video("RRR.mp4")

