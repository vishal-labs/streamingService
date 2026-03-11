from fastapi import FastAPI
from backend.video_processing import processVideo

app = FastAPI()


@app.get("/")
def welcome():
    payload = {
        "Welcome to" : "My streaming service"
    }
    return payload

# required endpoints
# 1. GET /api/videos : returns a JSON payload with all the available videos. 
# 2. GET /api/videos/{id}/stream/{chunkId} : Should start the stream
# 3. GET /api/videos/{id}/info : Should return the info of the video ID specified, like the total video duration, quality. 