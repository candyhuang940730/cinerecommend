import streamlit as st
from core.recommend import recommend

st.title("🎬 CineRecommend")
uid = st.number_input("User ID", min_value=1, value=1)
alpha = st.slider("內容(多模態) ↔ 社群信任 權重", 0.0, 1.0, 0.5)
if st.button("推薦"):
    df = recommend(int(uid), topk=10, alpha=alpha)
    for mid, r in df.iterrows():
        c1, c2 = st.columns([1, 3])
        if r.poster_url: c1.image(r.poster_url)
        c2.subheader(f"{r.title} ({int(r.year) if r.year==r.year else ''})")
        c2.write(f"內容分 {r.content:.2f}｜社群分 {r.social:.2f}｜總分 {r.final:.2f}")
