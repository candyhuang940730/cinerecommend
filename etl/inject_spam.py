"""實驗用:注入水軍帳號(對指定片全給 5 星),驗證信任機制能壓低其影響。"""
from core.db import conn

def main(n_spam=100, n_target=20, base_id=9_000_000):
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT movie_id FROM movies ORDER BY random() LIMIT %s", (n_target,))
        targets = [r[0] for r in cur.fetchall()]
        for i in range(n_spam):
            u = base_id + i
            cur.execute("INSERT INTO users(user_id,is_synthetic_spam) VALUES (%s,TRUE) ON CONFLICT DO NOTHING", (u,))
            for m in targets:
                cur.execute("INSERT INTO reviews VALUES (%s,%s,5.0,now()) ON CONFLICT DO NOTHING", (u, m))
        c.commit()

if __name__ == "__main__":
    main()
