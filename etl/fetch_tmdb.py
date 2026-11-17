"""用 TMDB API 補劇情簡介與海報 URL。"""
import os, time, requests
from tqdm import tqdm
from core.db import conn

KEY = os.environ.get("TMDB_API_KEY")
IMG = "https://image.tmdb.org/t/p/w342"

def main():
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT movie_id, tmdb_id FROM movies WHERE overview IS NULL")
        for mid, tid in tqdm(cur.fetchall()):
            r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}",
                             params={"api_key": KEY, "language": "zh-TW"}, timeout=10)
            if r.status_code != 200:
                continue
            j = r.json()
            cur.execute("UPDATE movies SET overview=%s, poster_url=%s WHERE movie_id=%s",
                        (j.get("overview") or "", IMG + j["poster_path"] if j.get("poster_path") else None, mid))
            c.commit(); time.sleep(0.03)

if __name__ == "__main__":
    main()
