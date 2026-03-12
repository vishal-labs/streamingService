export async function getMovies() {
  const res = await fetch("http://100.84.236.95:8000/api/videos/");
  return res.json();
}