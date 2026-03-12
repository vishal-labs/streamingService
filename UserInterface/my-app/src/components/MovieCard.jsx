import { useNavigate } from "react-router-dom";

function MovieCard({ movie }) {
  const navigate = useNavigate();

  function openMovie() {
    navigate(`/watch/${movie.id}`);
  }

  return (
    <div onClick={openMovie} style={{ cursor: "pointer" }}>
      <img src={movie.thumbnail} width="200" />
      <h3>{movie.title}</h3>
    </div>
  );
}

export default MovieCard;