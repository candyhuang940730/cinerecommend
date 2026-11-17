CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE movies (
  movie_id    INT PRIMARY KEY,          -- MovieLens movieId
  tmdb_id     INT UNIQUE,
  title       TEXT NOT NULL,
  year        INT,
  overview    TEXT,
  poster_url  TEXT
);
CREATE TABLE genres (genre_id SERIAL PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE movie_genres (
  movie_id INT REFERENCES movies ON DELETE CASCADE,
  genre_id INT REFERENCES genres,
  PRIMARY KEY (movie_id, genre_id)
);
CREATE TABLE users (
  user_id     INT PRIMARY KEY,
  is_synthetic_spam BOOLEAN DEFAULT FALSE   -- 實驗用:注入的水軍帳號
);
CREATE TABLE reviews (
  user_id  INT REFERENCES users,
  movie_id INT REFERENCES movies,
  rating   REAL NOT NULL,
  ts       TIMESTAMP,
  PRIMARY KEY (user_id, movie_id)
);
-- 多模態特徵(向量索引)
CREATE TABLE movie_features (
  movie_id   INT PRIMARY KEY REFERENCES movies ON DELETE CASCADE,
  text_vec   vector(384),   -- 劇情簡介 embedding
  poster_vec vector(512)    -- 海報 CLIP embedding
);
-- 社群可信度
CREATE TABLE user_trust (
  user_id INT PRIMARY KEY REFERENCES users,
  consistency REAL, volume REAL, diversity REAL,
  trust REAL
);
CREATE INDEX ON reviews(movie_id);
CREATE INDEX ON movie_features USING hnsw (text_vec   vector_cosine_ops);
CREATE INDEX ON movie_features USING hnsw (poster_vec vector_cosine_ops);
