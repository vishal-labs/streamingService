# Video Streaming — How It Actually Works

This document answers the questions from your notes and teaches you the fundamentals
you need to build a video streaming service from scratch.

---

## 1. How Does Video Streaming Work?

When you watch a video on YouTube or Netflix, your browser is **not** downloading the
entire file before playing it. Instead, the video is delivered in **small pieces (chunks)**
over time. The player requests a chunk, plays it, and while playing, it requests the
next chunk in the background. This is streaming.

There are three main approaches:

### a) Progressive Download (Simplest)
The server sends the video file from start to finish over HTTP. The browser starts
playing as soon as it has enough data. This is what happens when you point a `<video>`
tag at a file URL.

- **How it works**: The browser sends an HTTP request. The server responds with the
  video file. The browser's built-in video player starts playing once it has buffered
  enough.
- **Seeking**: The browser uses **HTTP Range Requests** to jump to different parts of
  the file. It sends a header like `Range: bytes=1000000-2000000` and the server
  responds with just that byte range.
- **Limitation**: No adaptive quality. If the user's network slows down, the video
  just buffers (stalls). You can't switch to a lower quality mid-stream.

### b) HTTP Live Streaming — HLS (Industry Standard)
The video is **pre-split** into small `.ts` (Transport Stream) segment files, typically
2-10 seconds each. A **playlist file** (`.m3u8`) lists all the segments in order.
The player reads the playlist, then fetches segments one by one.

```text path=null start=null
video/
├── playlist.m3u8          # Index file listing all segments
├── segment_000.ts         # First 4 seconds
├── segment_001.ts         # Next 4 seconds
├── segment_002.ts         # Next 4 seconds
└── ...
```

- **How it works**: Client fetches `playlist.m3u8` → reads the list of `.ts` files →
  fetches them sequentially → feeds them to the video player.
- **Adaptive Bitrate**: You can have multiple playlists at different qualities
  (480p, 720p, 1080p). A "master playlist" points to each quality level. The player
  monitors download speed and switches quality automatically.
- **This is what Netflix, YouTube, Twitch, etc. use** (YouTube uses DASH, which is
  similar but uses `.mpd` manifests instead of `.m3u8`).

### c) Media Source Extensions — MSE (Programmatic Control)
MSE is a browser API that lets JavaScript **manually feed video data** to a `<video>`
element. Instead of pointing `<video src="...">` at a URL, you create a
`MediaSource` object, open a `SourceBuffer`, and append chunks of video data yourself.

```javascript path=null start=null
const mediaSource = new MediaSource();
video.src = URL.createObjectURL(mediaSource);

mediaSource.addEventListener('sourceopen', () => {
  const sourceBuffer = mediaSource.addSourceBuffer('video/mp4; codecs="avc1.64001f,mp4a.40.2"');
  // Fetch chunks and append them:
  fetch('/chunk/0').then(r => r.arrayBuffer()).then(data => {
    sourceBuffer.appendBuffer(data);
  });
});
```

- **Why use it**: Full control over buffering, quality switching, and playback.
  This is how you implement custom buffering logic.
- **This is what we'll build** for the buffering feature.

---

## 2. Bottlenecks

These are the things that will slow down or break your streaming service:

| Bottleneck | What Happens | Solution |
|---|---|---|
| **Network bandwidth** | Video bitrate > user's download speed → buffering/stalling | Adaptive bitrate (multiple qualities) |
| **Server I/O** | Reading large video files from disk is slow if done naively | Stream the file (don't load entire file into memory). Read in chunks with `open()` + generator functions |
| **Blocking server** | One slow client blocks others | Use a WSGI server with threading (Flask's dev server handles this; for production use gunicorn with workers) |
| **No chunking** | Client must download from the start; seeking is slow | Support HTTP Range Requests so client can jump to any byte offset |
| **Large file in memory** | Loading a 2GB video into RAM to serve it | Never do this. Stream directly from disk to the HTTP response |
| **Video format** | Not all formats support streaming (e.g., some `.avi` files) | Use `.mp4` (with moov atom at the start) or `.webm` |

### The moov atom problem (important!)
MP4 files have a metadata section called the **moov atom** that contains the index
(timestamps, byte offsets for each frame, etc.). If the moov atom is at the **end** of
the file (which is the default when encoding), the browser must download the entire
file before it can play anything.

**Fix**: Use `ffmpeg` to move the moov atom to the beginning:
```bash path=null start=null
ffmpeg -i input.mp4 -movflags +faststart output.mp4
```

This is called **faststart** and is essential for streaming MP4 files.

---

## 3. UDP vs TCP — And Why You'll Use TCP (HTTP)

### UDP (User Datagram Protocol)
- **No connection setup** — just fire packets
- **No guaranteed delivery** — packets can be lost, arrive out of order, or duplicated
- **No congestion control** — sends as fast as it wants
- **Low latency** — great for live video calls (Zoom, WebRTC) where a dropped frame
  is better than a delayed one

### TCP (Transmission Control Protocol)
- **Reliable delivery** — every packet is acknowledged; lost packets are retransmitted
- **Ordered** — data arrives in the order it was sent
- **Congestion control** — adapts to network conditions
- **Higher latency** — the reliability guarantees add overhead

### So which one for streaming?

**For browser-based video streaming: TCP (via HTTP).**

Here's why:
- Browsers **don't support raw UDP sockets**. There's no `UDPSocket` API in JavaScript.
- HTTP is built on TCP, and browsers are extremely good at HTTP.
- Modern streaming (HLS, DASH) all run over HTTP/TCP.
- For **pre-recorded video** (VOD), reliability matters more than latency. You don't
  want corrupted frames — you'd rather buffer for a moment.

**UDP is used in**:
- Live video conferencing (WebRTC — which uses UDP under the hood)
- RTSP/RTP — used in security cameras, some live broadcast setups
- Game streaming (low-latency requirements)

**For your project**: Use HTTP (TCP). It's the right tool for serving video files
to a browser.

---

## 4. API vs RPC — Which One?

### REST API
- Resources are URLs: `GET /videos`, `GET /videos/1/stream`
- Uses standard HTTP methods: GET, POST, PUT, DELETE
- Stateless — each request contains all the info needed
- Easy to use from a browser (just `fetch()`)

### RPC (Remote Procedure Call)
- Call functions on the server: `listVideos()`, `streamVideo(id)`
- Protocols: gRPC (uses HTTP/2 + Protocol Buffers), JSON-RPC, XML-RPC
- More efficient for complex operations, but harder to use from browsers
- gRPC requires special client libraries

### For your project: REST API.

Your client is a browser. Browsers speak HTTP natively. A simple REST API is perfect:

```text path=null start=null
GET /api/videos              → List all available videos (JSON)
GET /api/videos/:id/stream   → Stream the video file (supports Range requests)
GET /api/videos/:id/info     → Get metadata (duration, size, name)
```

This is simple, debuggable (you can test endpoints in the browser URL bar), and
aligns with how real streaming services work.

---

## 5. Splitting of Video (Chunking)

Splitting is the process of dividing a video file into smaller segments. This is
fundamental to modern streaming.

### Why split?
1. **Seeking**: Instead of downloading from byte 0, jump to segment 45 which starts
   at the 3-minute mark
2. **Buffering control**: Download only the next 3-4 segments ahead of playback
3. **Adaptive quality**: Switch quality at segment boundaries
4. **Parallel downloads**: Fetch multiple segments simultaneously (if needed)

### How to split with ffmpeg:
```bash path=null start=null
# Split into 4-second HLS segments
ffmpeg -i input.mp4 -c copy -hls_time 4 -hls_list_size 0 \
  -hls_segment_filename 'segment_%03d.ts' playlist.m3u8

# Split into numbered MP4 chunks (for custom MSE player)
ffmpeg -i input.mp4 -c copy -f segment -segment_time 4 \
  -reset_timestamps 1 chunk_%03d.mp4
```

### Two approaches for your project:

**Approach A — On-the-fly Range Requests (simpler)**:
Don't pre-split anything. Serve the original MP4 file and let the browser use HTTP
Range Requests to fetch byte ranges as needed. The browser's built-in player handles
buffering automatically.

**Approach B — Pre-split into segments (more control)**:
Use ffmpeg to split videos into chunks. Serve chunks via your API. Build a custom
player using MSE that fetches and plays chunks in order, with manual buffering logic.

We'll implement **both** — Approach A first (to get something working fast), then
Approach B (to learn how real streaming works and implement custom buffering).

---

## 6. Buffering — How It Works

Buffering means **downloading video data ahead of the current playback position** so
that playback doesn't stall when the network hiccups.

### How buffering works conceptually:

```text path=null start=null
Timeline:     [====PLAYED====|==BUFFERED==|...NOT YET FETCHED...]
                              ^ playhead

- PLAYED:     Already watched. Data can be discarded.
- BUFFERED:   Downloaded but not yet played. This is your safety net.
- NOT FETCHED: Server has this data but client hasn't requested it yet.
```

### Buffering strategy:
1. **Buffer ahead**: Always try to stay N seconds ahead of the playhead.
   For example, if the user is at 00:30, try to have data up to 00:45 buffered.
2. **Buffer check loop**: Periodically check how much is buffered ahead. If it drops
   below a threshold (e.g., 5 seconds), fetch the next chunk.
3. **Stall detection**: If the buffer runs empty, show a loading spinner. Resume
   playback when enough data is re-buffered.

### Implementation with MSE:

```javascript path=null start=null
// Pseudocode for buffer management
const BUFFER_AHEAD = 15; // seconds to keep buffered ahead of playhead

function checkBuffer() {
  const currentTime = video.currentTime;
  const bufferedEnd = getBufferedEnd(); // how far ahead we've buffered

  if (bufferedEnd - currentTime < BUFFER_AHEAD) {
    fetchNextChunk(); // get the next segment from the server
  }
}

// Run every 500ms
setInterval(checkBuffer, 500);
```

### What "buffering" looks like from server's perspective:
The server doesn't know or care about buffering. It just responds to HTTP requests
for byte ranges or chunk files. **All buffering logic lives in the client.** The
client decides when to fetch more data.

---

## 7. The Complete Flow (Your End Outcome)

Here's how everything connects:

```text path=null start=null
┌─────────────────────────────────────────────────────────────┐
│                         SERVER                               │
│                                                              │
│  1. Starts up, scans the video directory you provide         │
│  2. Exposes REST API:                                        │
│     GET /api/videos         → returns list of videos         │
│     GET /api/videos/:id/stream → streams video with Range    │
│  3. Serves the client HTML/JS/CSS                            │
│                                                              │
│  Videos are read from disk using streams (not loaded fully   │
│  into memory). Server supports HTTP Range Requests.          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (TCP)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                         CLIENT (Browser)                     │
│                                                              │
│  1. User opens http://localhost:3000                          │
│  2. Browser loads HTML page                                  │
│  3. JS calls GET /api/videos → displays video list           │
│  4. User clicks a video                                      │
│  5. Browser starts streaming:                                │
│     - Basic: <video src="/api/videos/1/stream">              │
│     - Advanced: MSE fetches chunks, manages buffer           │
│  6. Buffering logic keeps N seconds ahead of playhead        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tech stack for this project:
- **Server**: Python (Flask) — simple, readable, you already know Python
- **Client**: HTML + vanilla JavaScript — no frameworks needed
- **Video processing**: ffmpeg — for splitting videos and fixing faststart
- **Protocol**: HTTP with Range Requests, then HLS/chunked for advanced buffering

---

## 8. Key Concepts Summary

- **Streaming** = sending data progressively so playback starts before the full
  download completes
- **HTTP Range Requests** = the mechanism that lets clients request specific byte
  ranges of a file (essential for seeking and resuming)
- **Chunking/Splitting** = dividing a video into small segments for better control
  over delivery and buffering
- **Buffering** = client-side logic that downloads data ahead of the playhead to
  ensure smooth playback
- **HLS** = the industry-standard protocol for HTTP-based streaming, built on
  chunking + playlists
- **MSE** = browser API that gives JavaScript direct control over feeding video
  data to the player
- **faststart** = moving MP4 metadata to the front of the file so playback can
  begin immediately
- **TCP/HTTP** = the right transport for browser-based VOD streaming (not UDP)
- **REST API** = the right interface style for browser clients (not RPC)
