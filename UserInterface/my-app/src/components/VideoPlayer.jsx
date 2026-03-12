import { useEffect, useRef } from "react";
import Hls from "hls.js";

function VideoPlayer({ src }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(src);
      hls.attachMedia(video);
    } else {
      video.src = src;
    }
  }, [src]);

  return <video ref={videoRef} controls width="900" />;
}

export default VideoPlayer;