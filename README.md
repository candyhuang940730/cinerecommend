# CineRecommend 執行順序
1. `cp .env.example .env` 填入 TMDB_API_KEY
2. `docker compose up -d`# PostgreSQL + pgvector,自動建表
3. `pip install -r requirements.txt`
4. 下載 MovieLens(先用 ml-latest-small 測試,再換 20M)
5. `python -m etl.load_movielens ./ml-latest-small`
6. `python -m etl.fetch_tmdb`        # 補簡介/海報
7. `python -m features.embed`       # 產生文字+海報向量
8. `python -m etl.inject_spam`      # (實驗)注入水軍
9. `python -m core.trust`           # 計算信任分數
10. `streamlit run app.py`
11. `python -m core.evaluate`       # P@K / R@K 消融實驗
