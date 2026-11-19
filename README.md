# CineRecommend

A movie recommender that combines **multimodal content features** (plot text and poster images) with a **trust-aware social signal** from community ratings.

Built as a database course final project.

## Features

- **Multimodal similarity**: plot text (multilingual MiniLM) and poster images (CLIP), stored as vectors in PostgreSQL with pgvector
- **User trust score**: based on rating consistency, volume and diversity, to reduce the influence of spam or promotional accounts
- **Social referral**: neighbors found by Pearson similarity, weighted by `similarity x trust`
- **Hybrid ranking**: `score = alpha x content + (1 - alpha) x social`, adjustable in the UI
- **Streamlit app** with user profiles, new-user rating, and genre filter
- **Evaluation** with Precision@K / Recall@K, a popularity baseline and ablations

## Tech Stack

Python 3.10-3.12, PostgreSQL + pgvector (Docker), sentence-transformers, pandas, Streamlit

## Project Structure

```
schema.sql              tables and vector indexes
etl/                    MovieLens import, TMDB fetch, spam injection
features/embed.py       text and poster embeddings
core/trust.py           user trust scores
core/recommend.py       hybrid recommender
core/evaluate.py        P@K / R@K and ablations
app.py                  Streamlit demo
```

## Setup

1. Get a free API key from [TMDB](https://www.themoviedb.org) and a copy of [MovieLens](https://grouplens.org/datasets/movielens/) (start with `ml-latest-small`).
2. Copy `.env.example` to `.env` and fill in `TMDB_API_KEY`.
3. Run:

```bash
docker compose up -d
pip install -r requirements.txt
python -m etl.load_movielens ./ml-latest-small
python -m etl.fetch_tmdb
python -m features.embed
python -m etl.inject_spam      # optional: spam accounts for experiments
python -m core.trust
streamlit run app.py
python -m core.evaluate        # optional: evaluation
```

## Results (initial, 283 users)

| Method | P@10 | R@10 |
|---|---|---|
| Popularity baseline | 0.1339 | 0.1114 |
| Content only | 0.0148 | 0.0165 |
| Social only | 0.0799 | 0.0681 |
| Hybrid (alpha = 0.5) | 0.0802 | 0.0696 |

Trust ablation and spam-resistance experiments are in progress.

## Acknowledgements

This product uses the TMDB API but is not endorsed or certified by TMDB. Rating data from [MovieLens](https://grouplens.org/datasets/movielens/) (GroupLens Research).