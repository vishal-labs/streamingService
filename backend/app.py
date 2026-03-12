from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
from backend.video_processing import start_watcher, stop_watcher


@asynccontextmanager
async def lifespan(app):
    start_watcher()
    yield
    stop_watcher()

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = Path(__file__).parent / "outputs"


@app.get("/")
def welcome():
    payload = {
        "Welcome to" : "My streaming service"
    }
    return payload


@app.get("/api/videos")
def get_videos():
    videos = []
    if not OUTPUTS_DIR.exists():
        raise HTTPException(status_code=404, detail="Folder Not found")
    for folder in sorted(OUTPUTS_DIR.iterdir()):
        videos.append({
            "id": folder.name.lower(),
            "title": folder.name,
        })
    return videos


@app.get("/api/videos/stream/{name}/{chunkId}")
def send_video(name: str, chunkId : str):
    if ".ts" in chunkId:
        folder_path = Path(f"backend/outputs/{name}/")
        segment = "segments"
        file_path = folder_path / segment / chunkId
        print(file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File Not found")
        return FileResponse(
            path=file_path,
            filename=name,
            media_type="video/mp2t"
        )
    elif ".m3u8" in chunkId:
        folder_path = Path(f"backend/outputs/{name}/")
        file_path = folder_path / "manifest.m3u8"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File Not found")
        return FileResponse(
            path=file_path,
            filename=chunkId,
            media_type="application/vnd.apple.mpegurl"
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported file request")


# required endpoints
# 1. GET /api/videos : returns a JSON payload with all the available videos. 
# 2. GET /api/videos/stream/{name}/{chunkId} : Should start the stream with the requested movie name, and the chunk/manifest. 