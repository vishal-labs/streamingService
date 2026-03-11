from fastapi import FastAPI
from backend.video_processing import

app = FastAPI()

@app.get("/")
def welcome():
    payload = {
        "Welcome to" : "My streaming service"
    }
    return payload

# required endpoints
# 1. /api/videos : returns a JSON payload with all the available videos. 
# 2. /api/videos/{id}/stream : Should start the stream
# 3. /api/videos/{id}/info : Should return the info of the video ID specified, like the total video duration, quality. 