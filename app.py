import streamlit as st
from core.recommend import recommend, list_genres
from core.profile import get_profile, search_movies, create_user, add_rating

st.title("🎬 CineRecommend")

# ---- 側邊欄:User Profile ----
st.sidebar.header("User Profile")
mode = st.sidebar.radio("身分", ["現有使用者", "新使用者"])
if mode == "現有使用者":
    st.session_state["uid"] = int(st.sidebar.number_input("User ID", min_value=1, value=1))
elif st.sidebar.button("建立新使用者") or "uid" not in st.session_state:
    st.session_state["uid"] = create_user()
uid = st.session_state["uid"]
st.sidebar.write(f"目前使用者:**{uid}**")

p = get_profile(uid)
st.sidebar.metric("評分數", p["n"])
st.sidebar.metric("平均評分", p["avg"] if p["n"] else "-")
st.sidebar.metric("可信度", f"{p['trust']:.2f}" if p["trust"] is not None else "未計算")
if p["n"]:
    st.sidebar.caption("類型偏好(評分次數)")
    st.sidebar.bar_chart(p["genre"].set_index("name").n)

# ---- 主畫面 ----
tab1, tab2 = st.tabs(["推薦", "建立偏好"])

with tab2:
    kw = st.text_input("搜尋電影")
    if kw:
        for _, m in search_movies(kw).iterrows():
            c1, c2, c3 = st.columns([1, 3, 2])
            if m.poster_url: c1.image(m.poster_url, width=70)
            c2.write(f"{m.title} ({int(m.year) if m.year==m.year else ''})")
            score = c3.select_slider("評分", [1, 2, 3, 4, 5], 4, key=f"s{m.movie_id}")
            if c3.button("送出", key=f"b{m.movie_id}"):
                add_rating(uid, int(m.movie_id), float(score)); st.rerun()

with tab1:
    alpha = st.slider("內容(多模態) ↔ 社群信任 權重", 0.0, 1.0, 0.5)
    genres = st.multiselect("電影類型(不選=全部)", list_genres())
    if st.button("推薦"):
        if p["n"] < 5:
            st.warning("請先到「建立偏好」評分至少 5 部電影")
        else:
            df = recommend(uid, topk=10, alpha=alpha, genres=genres)
            for mid, r in df.iterrows():
                c1, c2 = st.columns([1, 3])
                if r.poster_url: c1.image(r.poster_url)
                c2.subheader(f"{r.title} ({int(r.year) if r.year==r.year else ''})")
                c2.write(f"內容分 {r.content:.2f}｜社群分 {r.social:.2f}｜總分 {r.final:.2f}")