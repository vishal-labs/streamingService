import { useEffect, useState } from "react";
import { getMovies } from "../api/movies";
import MovieCard from "../components/MovieCard";

function Home() {
  const [movies, setMovies] = useState([]);

  useEffect(() => {
    async function loadMovies() {
      const data = await getMovies();
      setMovies(data);
    }

    loadMovies();
  }, []);
  console.log(movies);

  return (
    <div>
      <h1>DIY Netflix</h1>

      <div style={{ display: "flex", gap: "20px" }}>
        {movies.map((movie) => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>
    </div>
  );
}

export default Home;