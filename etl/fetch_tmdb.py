"""用 TMDB API 補劇情簡介與海報 URL(並行 + 重試版)。"""
import os, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from core.db import conn

KEY = os.environ.get("TMDB_API_KEY")
IMG = "https://image.tmdb.org/t/p/w342"
session = requests.Session()

def fetch(mid, tid):
    for attempt in range(4):                       # 最多重試 4 次
        try:
            r = session.get(f"https://api.themoviedb.org/3/movie/{tid}",
                            params={"api_key": KEY, "language": "zh-TW"}, timeout=20)
            if r.status_code == 200:
                j = r.json()
                return mid, (j.get("overview") or ""), (IMG + j["poster_path"] if j.get("poster_path") else None)
            if r.status_code == 404:
                return mid, "", None               # 查無此片,標記為已處理
            if r.status_code == 429:               # 被限流,多等一下
                time.sleep(2 + attempt * 2)
        except requests.RequestException:
            time.sleep(1 + attempt)                # 逾時或斷線,等一下再試
    return None                                    # 放棄這筆,下次重跑會再處理

def main(workers=4):
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT movie_id, tmdb_id FROM movies WHERE overview IS NULL")
        todo = cur.fetchall()
        done = 0
        with ThreadPoolExecutor(workers) as ex:
            futs = [ex.submit(fetch, m, t) for m, t in todo]
            for f in tqdm(as_completed(futs), total=len(futs)):
                res = f.result()
                if res:
                    mid, ov, url = res
                    cur.execute("UPDATE movies SET overview=%s, poster_url=%s WHERE movie_id=%s", (ov, url, mid))
                    done += 1
                    if done % 100 == 0:
                        c.commit()
        c.commit()
        print(f"完成 {done}/{len(todo)},剩下 {len(todo)-done} 筆可重跑")

if __name__ == "__main__":
    main()