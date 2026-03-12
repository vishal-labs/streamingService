import os
import time
import queue
import threading
import shutil
import ffmpeg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR  = os.path.join(BASE_DIR, "inputs")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(INPUTS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

job_queue = queue.Queue()


def output_exists(video_name):
    """Check if processing already finished"""
    stem = os.path.splitext(video_name)[0]
    manifest = os.path.join(OUTPUTS_DIR, stem, "manifest.m3u8")
    return os.path.exists(manifest)


def wait_for_copy_complete(path):
    """Wait until file size stops changing"""
    last_size = -1

    while True:
        size = os.path.getsize(path)

        if size == last_size:
            return

        last_size = size
        time.sleep(2)


def process_video(video_name):

    if output_exists(video_name):
        print("Skipping (already processed):", video_name)
        return

    video_path = os.path.join(INPUTS_DIR, video_name)

    if not os.path.exists(video_path):
        return

    wait_for_copy_complete(video_path)

    stem = os.path.splitext(video_name)[0]

    output_dir   = os.path.join(OUTPUTS_DIR, stem)
    segments_dir = os.path.join(output_dir, "segments")

    os.makedirs(segments_dir, exist_ok=True)

    print("Processing:", video_name)

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
        hls_segment_filename=f"{segments_dir}/seg_%06d.ts"
    )

    ffmpeg.run(stream)

    print("Finished:", video_name)


def worker():
    """Sequential processing worker"""
    while True:

        video = job_queue.get()

        try:
            process_video(video)
        except Exception as e:
            print("Error processing", video, ":", e)

        job_queue.task_done()


class InputHandler(FileSystemEventHandler):

    def on_created(self, event):

        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)

        if file_name.lower().endswith((".mp4", ".mkv", ".mov")):

            if output_exists(file_name):
                print("Skipping (already processed):", file_name)
                return

            print("New video detected:", file_name)
            job_queue.put(file_name)


    def on_moved(self, event):
        """Handle rename of video files"""

        if event.is_directory:
            return

        old_name = os.path.basename(event.src_path)
        new_name = os.path.basename(event.dest_path)

        if not new_name.lower().endswith((".mp4", ".mkv", ".mov")):
            return

        old_stem = os.path.splitext(old_name)[0]
        new_stem = os.path.splitext(new_name)[0]

        old_output = os.path.join(OUTPUTS_DIR, old_stem)
        new_output = os.path.join(OUTPUTS_DIR, new_stem)

        if os.path.exists(old_output):

            print(f"Renaming output folder: {old_stem} → {new_stem}")
            os.rename(old_output, new_output)

        else:
            print("Renamed file detected:", new_name)
            job_queue.put(new_name)


    def on_deleted(self, event):
        """Delete output if input video is deleted"""

        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)
        stem = os.path.splitext(file_name)[0]

        output_dir = os.path.join(OUTPUTS_DIR, stem)

        if os.path.exists(output_dir):
            print(f"Deleting output folder for removed video: {stem}")
            shutil.rmtree(output_dir)


def scan_existing_files():
    """Process files already in inputs folder"""

    for file in os.listdir(INPUTS_DIR):

        if file.lower().endswith((".mp4", ".mkv", ".mov")):

            if output_exists(file):
                print("Skipping (already processed):", file)
                continue

            print("Existing video found:", file)
            job_queue.put(file)


observer = None


def start_watcher():
    """Start the watchdog observer and worker thread (non-blocking)."""
    global observer

    threading.Thread(target=worker, daemon=True).start()
    scan_existing_files()

    observer = Observer()
    observer.schedule(InputHandler(), INPUTS_DIR, recursive=False)
    observer.start()

    print("Watching folder:", INPUTS_DIR)


def stop_watcher():
    """Stop the watchdog observer."""
    global observer

    if observer:
        observer.stop()
        observer.join()
        print("Watcher stopped.")


if __name__ == "__main__":
    start_watcher()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watcher()