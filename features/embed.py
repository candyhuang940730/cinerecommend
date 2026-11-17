"""產生多模態特徵:劇情文字向量 + 海報 CLIP 向量,寫入 pgvector。"""
import io, requests
from PIL import Image
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from core.db import conn

text_model  = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")  # 384 維
image_model = SentenceTransformer("clip-ViT-B-32")                          # 512 維

def vec(v): return "[" + ",".join(f"{x:.6f}" for x in v) + "]"

def poster_img(url):
    try:
        return Image.open(io.BytesIO(requests.get(url, timeout=10).content)).convert("RGB")
    except Exception:
        return None

def main():
    with conn() as c, c.cursor() as cur:
        cur.execute("""SELECT m.movie_id, m.title, m.overview, m.poster_url FROM movies m
                       LEFT JOIN movie_features f USING(movie_id) WHERE f.movie_id IS NULL""")
        for mid, title, ov, url in tqdm(cur.fetchall()):
            t = text_model.encode(f"{title}. {ov or ''}", normalize_embeddings=True)
            img = poster_img(url) if url else None
            p = image_model.encode(img, normalize_embeddings=True) if img else None
            cur.execute("INSERT INTO movie_features VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                        (mid, vec(t), vec(p) if p is not None else None))
            c.commit()

if __name__ == "__main__":
    main()
