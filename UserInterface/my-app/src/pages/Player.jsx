import { useParams } from "react-router-dom";
import VideoPlayer from "../components/VideoPlayer";

function Player() {
  const { movieId } = useParams();

  const streamUrl = `http://100.84.236.95:8000/api/videos/stream/${movieId}/manifest.m3u8`;

  return (
    <div>
      <VideoPlayer src={streamUrl} />
    </div>
  );
}

export default Player;