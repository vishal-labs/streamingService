# Tasks — Build Your Video Streaming Service

Follow these tasks in order. Each task builds on the previous one.
Read `ENLIGHTEN.md` first — these tasks reference concepts explained there.

---

## Phase 1: Setup & Basic Server

### Task 1: Install prerequisites
- [ ] Install Python 3 (if not already — macOS usually has it)
- [ ] Install ffmpeg (needed later): `brew install ffmpeg`
- [ ] Create a virtual environment: `python3 -m venv venv`
- [ ] Activate it: `source venv/bin/activate`
- [ ] Install Flask: `pip install flask`
- [ ] Create the project structure:
  ```
  streaming-service/
  ├── server/
  │   └── app.py             # Server entry point
  ├── client/
  │   ├── index.html         # Video list page
  │   ├── player.html        # Video player page
  │   ├── style.css
  │   └── app.js             # Client-side JavaScript
  ├── videos/                # Your video files go here (gitignored)
  ├── requirements.txt       # Just: flask
  ├── ENLIGHTEN.md
  └── TASKS.md
  ```
- [ ] Add a `.gitignore` with `venv/`, `__pycache__/`, and `videos/`
- [ ] Create `requirements.txt` with `flask` in it
- [ ] Drop 2-3 `.mp4` test videos into the `videos/` directory

### Task 2: Fix your test videos for streaming
- [ ] Run `ffmpeg -i input.mp4 -movflags +faststart output.mp4` on each test video
      (see ENLIGHTEN.md § 2 — "The moov atom problem")
- [ ] This ensures the metadata is at the start of the file so browsers can play
      immediately without downloading the whole file

### Task 3: Build the basic Flask server
- [ ] Create `server/app.py`
- [ ] Accept a command-line argument for the video directory path:
      `python server/app.py ./videos`
      (use `sys.argv[1]` to read it)
- [ ] On startup, scan the directory with `os.listdir()` and build an in-memory
      list of video files (filter for `.mp4`, `.webm`, `.mkv`)
- [ ] Log the number of videos found
- [ ] Start the Flask server on port 3000: `app.run(port=3000)`
- [ ] Serve the `client/` directory as static files using Flask's
      `send_from_directory()` or a static folder config

### Task 4: Build the video listing API
- [ ] Create endpoint: `GET /api/videos` using `@app.route('/api/videos')`
- [ ] Return a JSON array of video objects: `[{ id, name, size }]`
      (use `os.path.getsize()` to get file size)
- [ ] Return JSON with `flask.jsonify()`
- [ ] Test it: open `http://localhost:3000/api/videos` in your browser
      and verify you see JSON

---

## Phase 2: Basic Streaming (Progressive Download + Range Requests)

### Task 5: Implement the streaming endpoint WITHOUT Range support
- [ ] Create endpoint: `GET /api/videos/<int:video_id>/stream`
- [ ] Look up the video by ID, get its file path
- [ ] Set the response header `Content-Type: video/mp4`
- [ ] Use a Python generator that reads the file in chunks and return it
      with `Response(generate(), mimetype='video/mp4')`:
      ```python
      def generate():
          with open(filepath, 'rb') as f:
              while chunk := f.read(8192):
                  yield chunk
      ```
      (see ENLIGHTEN.md § 2 — never load the whole file into memory)
- [ ] Test: open `http://localhost:3000/api/videos/0/stream` in browser —
      the video should play but **seeking will NOT work yet**

### Task 6: Add HTTP Range Request support
This is the most important server-side task. See ENLIGHTEN.md § 1a and § 5.
- [ ] Check if the request has a `Range` header: `request.headers.get('Range')`
- [ ] If **no Range header**: respond with the full file (status `200`) —
      same as Task 5
- [ ] If **Range header present**:
  - Parse the range: `range_header.replace('bytes=', '').split('-')`
  - Calculate `start`, `end`, and `chunk_size`
  - Write a generator that does `f.seek(start)` then reads in chunks up to `end`
  - Build a `Response` with status `206`
  - Set headers on the response:
    - `Content-Range: bytes start-end/total_size`
    - `Accept-Ranges: bytes`
    - `Content-Length: chunk_size`
    - `Content-Type: video/mp4`
  - Return the response
- [ ] Test: open the video in browser — you should now be able to **seek**
      (click anywhere on the progress bar and it jumps there)

### Task 7: Build the client — video list page
- [ ] In `client/index.html`, create a simple page with a heading and
      an empty container `<div id="video-list"></div>`
- [ ] In `client/app.js`:
  - Fetch `GET /api/videos`
  - For each video, create a clickable card/link showing the video name and size
  - Clicking a video navigates to `player.html?id=VIDEO_ID`
- [ ] Style it minimally in `style.css`

### Task 8: Build the client — basic video player page
- [ ] In `client/player.html`, create a page with:
  - A `<video>` element with `controls` attribute
  - A back button to return to the list
- [ ] In the page's JS (inline or separate file):
  - Read the `id` from the URL query params
  - Set `video.src = /api/videos/${id}/stream`
- [ ] Test the full flow: open `http://localhost:3000` → see video list →
      click a video → it plays with seeking support

**Checkpoint: At this point you have a working video streaming service.**
Everything below adds the custom buffering feature.

---

## Phase 3: Video Chunking (Preparation for Custom Buffering)

### Task 9: Create a video preparation script
See ENLIGHTEN.md § 5 for why we split videos.
- [ ] Create `scripts/prepare_video.py`
- [ ] The script should:
  1. Take an input video path as argument (`sys.argv[1]`)
  2. Create an output directory for that video
  3. Use `subprocess.run()` to call ffmpeg to split into 4-second `.mp4` segments:
     ```
     ffmpeg -i input.mp4 -c copy -f segment -segment_time 4 \
       -reset_timestamps 1 output_dir/chunk_%03d.mp4
     ```
  4. Scan the output directory and generate a `manifest.json` file listing
     all chunks with their duration and byte sizes (use `os.path.getsize()`
     and optionally `ffprobe` via `subprocess` for duration)
- [ ] Run the script on your test videos: `python scripts/prepare_video.py videos/myvideo.mp4`

### Task 10: Add chunk-serving API endpoints
- [ ] Create endpoint: `GET /api/videos/:id/manifest`
  - Returns the `manifest.json` for a video (list of chunks with metadata)
- [ ] Create endpoint: `GET /api/videos/:id/chunks/:chunkIndex`
  - Serves the specific chunk file
  - Set proper `Content-Type` header
- [ ] Test: fetch the manifest in browser, then fetch a chunk URL and
      verify it downloads

---

## Phase 4: Custom Buffering with Media Source Extensions (MSE)

### Task 11: Create the MSE-based player page
See ENLIGHTEN.md § 1c and § 6.
- [ ] Create `client/player-advanced.html` (keep the basic player working)
- [ ] Add a `<video>` element (no `src` attribute this time)
- [ ] In JavaScript:
  1. Create a `MediaSource` object
  2. Set `video.src = URL.createObjectURL(mediaSource)`
  3. Listen for `sourceopen` event on the MediaSource
  4. In the handler, create a `SourceBuffer`:
     ```
     sourceBuffer = mediaSource.addSourceBuffer(
       'video/mp4; codecs="avc1.64001f,mp4a.40.2"'
     );
     ```
     (You may need to adjust the codec string based on your video.
      Use `ffprobe -v error -show_streams input.mp4` to find the codec.)

### Task 12: Implement sequential chunk loading
- [ ] Fetch the manifest from `GET /api/videos/:id/manifest`
- [ ] Create a `loadChunk(index)` function that:
  1. Fetches the chunk as an `ArrayBuffer`
  2. Waits for the SourceBuffer to be ready (`updateend` event)
  3. Appends the buffer: `sourceBuffer.appendBuffer(data)`
- [ ] On `sourceopen`, load chunk 0, then on `updateend`, load chunk 1, etc.
- [ ] Verify: the video should play from start to finish using chunks

### Task 13: Implement the buffer-ahead logic
This is the core buffering feature. See ENLIGHTEN.md § 6.
- [ ] Define constants:
  - `BUFFER_AHEAD_SECONDS = 15` — how far ahead to buffer
  - `MIN_BUFFER_SECONDS = 5` — minimum buffer before fetching more
- [ ] Create a `checkBuffer()` function that:
  1. Gets the current playback time: `video.currentTime`
  2. Gets the buffered end time from the SourceBuffer's `buffered` ranges
  3. If `(bufferedEnd - currentTime) < MIN_BUFFER_SECONDS` → fetch next chunk
  4. If `(bufferedEnd - currentTime) >= BUFFER_AHEAD_SECONDS` → do nothing (enough buffered)
- [ ] Run `checkBuffer()` on an interval (every 500ms) and also on `timeupdate`
- [ ] Track which chunk index to fetch next with a simple counter
- [ ] When all chunks are loaded, call `mediaSource.endOfStream()`

### Task 14: Add a buffering UI indicator
- [ ] Show a loading spinner/text when the buffer is empty and video is waiting
- [ ] Listen for the video's `waiting` event (fires when playback stalls)
- [ ] Listen for the `playing` event (fires when playback resumes)
- [ ] Display a visual buffer bar below the video showing how much is buffered
      vs. how much is played (read from `video.buffered` TimeRanges)

### Task 15: Handle seeking with chunks
- [ ] Listen for the video's `seeking` event
- [ ] When the user seeks:
  1. Determine which chunk corresponds to the new `video.currentTime`
     (use the manifest's duration info)
  2. Clear the existing SourceBuffer if needed: `sourceBuffer.remove(0, Infinity)`
  3. Reset the chunk counter to the new position
  4. Start loading from the new chunk
- [ ] This lets users click anywhere on the progress bar and buffering
      restarts from that point

---

## Phase 5: Polish & Learn More (Optional)

### Task 16: Add error handling
- [ ] Server: return 404 with `abort(404)` if video ID doesn't exist
- [ ] Server: wrap file reads in try/except and return 500 on errors
- [ ] Client: show user-friendly error messages if the server is down or
      video fails to load
- [ ] Handle MSE errors (`sourceBuffer` error events)

### Task 17: Add video metadata endpoint
- [ ] Create endpoint: `GET /api/videos/<int:video_id>/info`
- [ ] Return: name, file size, duration, resolution, codec info
- [ ] Use `subprocess.run()` to call ffprobe and parse its JSON output:
      `ffprobe -v quiet -print_format json -show_format -show_streams file.mp4`
- [ ] Parse the output with `json.loads()` and return relevant fields
- [ ] Display this info on the player page

### Task 18: Support multiple video formats
- [ ] Detect the video format from the file extension
- [ ] Set the correct `Content-Type` (`video/mp4`, `video/webm`, etc.)
- [ ] Set the correct MSE codec string based on the format
- [ ] Handle unsupported formats gracefully (show error to user)

### Task 19: Experiment with HLS (bonus learning)
See ENLIGHTEN.md § 1b.
- [ ] Use ffmpeg to generate HLS output:
      ```
      ffmpeg -i input.mp4 -c copy -hls_time 4 -hls_list_size 0 \
        -hls_segment_filename 'segment_%03d.ts' playlist.m3u8
      ```
- [ ] Serve the `.m3u8` and `.ts` files from your server
- [ ] Use `hls.js` library on the client to play HLS streams
- [ ] Compare this approach with your custom MSE implementation

---

## Quick Reference: What to Read When

- Before **Task 5-6**: Read ENLIGHTEN.md § 1a (Progressive Download) and § 2 (Bottlenecks)
- Before **Task 9**: Read ENLIGHTEN.md § 5 (Splitting of Video)
- Before **Task 11-13**: Read ENLIGHTEN.md § 1c (MSE) and § 6 (Buffering)
- Before **Task 19**: Read ENLIGHTEN.md § 1b (HLS)
- Anytime confused about protocol choice: Read ENLIGHTEN.md § 3 (UDP vs TCP)
- Anytime confused about API design: Read ENLIGHTEN.md § 4 (API vs RPC)
