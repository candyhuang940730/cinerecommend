import streamlit as st
from core.recommend import recommend, list_genres
from core.profile import get_profile, search_movies, create_user, add_rating

st.set_page_config(page_title="CineRecommend", page_icon="🎬", layout="wide")

st.title("🎬 CineRecommend")
st.caption("Find movies you'll like using plot similarity, poster style, "
           "and ratings from trusted people with similar taste.")

c1, c2, c3 = st.columns(3)
c1.markdown("### 👤\n**選擇使用者**", help="輸入 MovieLens 使用者 ID，或在側邊欄建立新使用者。")
c2.markdown("### ⭐\n**評分 5 部以上**", help="到「建立偏好」分頁評分，系統才能了解你的口味。")
c3.markdown("### 🎯\n**取得推薦**", help="到「推薦」分頁，按下按鈕即可。")

st.caption("🎞️ = 劇情與海報相似度　👥 = 品味相近的可信使用者　🛡️ = 信任分數")

# ---- Sidebar: User Profile ----
st.sidebar.header("User Profile")
mode = st.sidebar.radio("Account", ["Existing user", "New user"])
if mode == "Existing user":
    st.session_state["uid"] = int(st.sidebar.number_input("User ID", min_value=1, value=1))
elif st.sidebar.button("Create new user") or "uid" not in st.session_state:
    st.session_state["uid"] = create_user()
uid = st.session_state["uid"]
st.sidebar.write(f"Current user: **{uid}**")

p = get_profile(uid)
st.sidebar.metric("Ratings", p["n"])
st.sidebar.metric("Average rating", p["avg"] if p["n"] else "-")
st.sidebar.metric("🛡️ 信任分數", f"{p['trust']:.2f}" if p["trust"] is not None else "尚未計算",
                  help="這位使用者的評分看起來有多可靠（0 到 1）。")
if p["n"]:
    st.sidebar.caption("Genre preference (number of ratings)")
    st.sidebar.bar_chart(p["genre"].set_index("name").n)

# ---- Main area ----
tab1, tab2 = st.tabs(["Recommend", "Build preferences"])

with tab2:
    st.write("找一部電影並評分。 Your ratings are used to find similar movies and similar users.")
    kw = st.text_input("Search movies")
    if kw:
        for _, m in search_movies(kw).iterrows():
            c1, c2, c3 = st.columns([1, 3, 2])
            if m.poster_url: c1.image(m.poster_url, width=70)
            c2.write(f"{m.title} ({int(m.year) if m.year==m.year else ''})")
            score = c3.select_slider("Rating", [1, 2, 3, 4, 5], 4, key=f"s{m.movie_id}")
            if c3.button("Submit", key=f"b{m.movie_id}"):
                add_rating(uid, int(m.movie_id), float(score)); st.rerun()

with tab1:
    alpha = st.slider(
        "👥 社群 ←→ 🎞️ 內容",
        0.0, 1.0, 0.5,
        help="左邊：只參考品味相近且可信的使用者評分。右邊：只看劇情與海報的相似度。中間：兩者混合。")
    genres = st.multiselect("Genres (leave empty for all)", list_genres())
    if st.button("Recommend"):
        if p["n"] < 5:
            st.warning("Please rate at least 5 movies in the 'Build preferences' tab first.")
        else:
            df = recommend(uid, topk=10, alpha=alpha, genres=genres)
            if df.empty:
                st.warning("No movies match your filters.")
            for mid, r in df.iterrows():
                c1, c2 = st.columns([1, 3])
                if r.poster_url: c1.image(r.poster_url)
                c2.subheader(f"{r.title} ({int(r.year) if r.year==r.year else ''})")
                c2.write(f"內容： {r.content:.2f} | 社群： {r.social:.2f} | 總分： {r.final:.2f}")