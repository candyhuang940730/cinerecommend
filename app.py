import streamlit as st
from core.recommend import recommend, list_genres
from core.profile import get_profile, search_movies, create_user, add_rating
import pandas as pd
from core.db import conn

st.set_page_config(page_title="CineRecommend", page_icon="🎬", layout="wide")

# ---------- Text ----------
TEXT = {
    "en": {
        "caption": "Find movies you'll like using plot similarity, poster style, and ratings from trusted people with similar taste.",
        "s1": "**Pick a user**", "s1h": "Existing MovieLens ID, or create a new user in the sidebar.",
        "s2": "**Rate 5+ movies**", "s2h": "Use the 'Build preferences' tab. Needed to learn your taste.",
        "s3": "**Get picks**", "s3h": "Use the 'Recommend' tab and press the button.",
        "legend": "🎞️ = plot + poster similarity　👥 = trusted users with similar taste　🛡️ = trust score",
        "profile": "User Profile", "account": "Account",
        "existing": "Existing user", "new": "New user",
        "uid": "User ID", "create": "Create new user", "current": "Current user",
        "ratings": "Ratings", "avg": "Average rating", "trust": "🛡️ Trust", "na": "n/a",
        "trust_h": "How reliable this user's ratings look (0 to 1).",
        "genre_pref": "Genre preference (number of ratings)",
        "tab_rec": "Recommend", "tab_pref": "Build preferences",
        "pref_intro": "Search for a movie and rate it. Your ratings are used to find similar movies and similar users.",
        "search": "Search movies", "rating": "Rating", "submit": "Submit",
        "slider": "👥 Social  ←→  🎞️ Content",
        "slider_h": "Left: ratings from trusted, similar users. Right: plot and poster similarity. Middle: a mix.",
        "genres": "Genres (leave empty for all)", "go": "Recommend",
        "need5": "Please rate at least 5 movies in the 'Build preferences' tab first.",
        "empty": "No movies match your filters.",
        "no_result": "No movies found for “{kw}”.",
        "no_result_hint": "Tips: search by the English title (e.g. “Matrix”), try a shorter keyword, or check the spelling. Only the most-rated movies are in the database, so very obscure titles may be missing.",
        "years": "🗓️ Movies released {lo} – {hi}",
    },
    "zh": {
        "caption": "結合劇情相似度、海報風格，以及品味相近的可信使用者評分，幫你找到想看的電影。",
        "s1": "**選擇使用者**", "s1h": "輸入 MovieLens 使用者 ID，或在側邊欄建立新使用者。",
        "s2": "**評分 5 部以上**", "s2h": "到「建立偏好」分頁評分，系統才能了解你的口味。",
        "s3": "**取得推薦**", "s3h": "到「推薦」分頁，按下按鈕即可。",
        "legend": "🎞️ = 劇情與海報相似度　👥 = 品味相近的可信使用者　🛡️ = 信任分數",
        "profile": "使用者資料", "account": "帳號",
        "existing": "現有使用者", "new": "新使用者",
        "uid": "使用者 ID", "create": "建立新使用者", "current": "目前使用者",
        "ratings": "評分數", "avg": "平均評分", "trust": "🛡️ 信任分數", "na": "尚未計算",
        "trust_h": "這位使用者的評分看起來有多可靠（0 到 1）。",
        "genre_pref": "類型偏好（評分次數）",
        "tab_rec": "推薦", "tab_pref": "建立偏好",
        "pref_intro": "搜尋電影並評分。你的評分會用來尋找相似的電影與相似的使用者。",
        "search": "搜尋電影", "rating": "評分", "submit": "送出",
        "slider": "👥 社群 ←→ 🎞️ 內容",
        "slider_h": "左邊：只參考品味相近且可信的使用者評分。右邊：只看劇情與海報的相似度。中間：兩者混合。",
        "genres": "電影類型（不選＝全部）", "go": "推薦",
        "need5": "請先到「建立偏好」分頁評分至少 5 部電影。",
        "empty": "沒有符合條件的電影。",
        "no_result": "找不到「{kw}」相關的電影。",
        "no_result_hint": "小提示：請用英文片名搜尋（例如 “Matrix”）、試試較短的關鍵字，或檢查拼字。資料庫只收錄評分數較多的電影，太冷門的片可能不在其中。",
        "years": "🗓️ 收錄電影上映時間：{lo} – {hi}",
    },
}
GENRE_ZH = {
    "Action": "動作", "Adventure": "冒險", "Animation": "動畫", "Children": "兒童",
    "Comedy": "喜劇", "Crime": "犯罪", "Documentary": "紀錄片", "Drama": "劇情",
    "Fantasy": "奇幻", "Film-Noir": "黑色電影", "Horror": "恐怖", "IMAX": "IMAX",
    "Musical": "音樂劇", "Mystery": "懸疑", "Romance": "愛情", "Sci-Fi": "科幻",
    "Thriller": "驚悚", "War": "戰爭", "Western": "西部",
}

# ---------- Language switch ----------
lang_label = st.sidebar.radio("🌐", ["English", "中文"], horizontal=True, key="lang_label")
lang = "en" if lang_label == "English" else "zh"
t = lambda k: TEXT[lang][k]
genre_name = (lambda g: GENRE_ZH.get(g, g)) if lang == "zh" else (lambda g: g)
@st.cache_data
def year_range():
    with conn() as c:
        r = pd.read_sql("SELECT min(year) lo, max(year) hi FROM movies", c).iloc[0]
    return int(r.lo), int(r.hi)

# ---------- Header ----------
st.title("🎬 CineRecommend")
st.caption(t("caption"))
lo, hi = year_range()
st.caption(t("years").format(lo=lo, hi=hi))

c1, c2, c3 = st.columns(3)
c1.markdown(f"### 1.👤\n{t('s1')}", help=t("s1h"))
c2.markdown(f"### 2.⭐\n{t('s2')}", help=t("s2h"))
c3.markdown(f"### 3.🎯\n{t('s3')}", help=t("s3h"))
st.caption(t("legend"))

# ---------- Sidebar: User Profile ----------
st.sidebar.header(t("profile"))
mode = st.sidebar.radio(t("account"), ["existing", "new"],
                        format_func=lambda m: t(m), key="mode")
if mode == "existing":
    st.session_state["uid"] = int(st.sidebar.number_input(t("uid"), min_value=1, value=1, key="uid_input"))
elif st.sidebar.button(t("create"), key="create_btn") or "uid" not in st.session_state:
    st.session_state["uid"] = create_user()
uid = st.session_state["uid"]
st.sidebar.write(f"{t('current')}: **{uid}**")

p = get_profile(uid)
st.sidebar.metric(t("ratings"), p["n"])
st.sidebar.metric(t("avg"), p["avg"] if p["n"] else "-")
st.sidebar.metric(t("trust"), f"{p['trust']:.2f}" if p["trust"] is not None else t("na"), help=t("trust_h"))
if p["n"]:
    st.sidebar.caption(t("genre_pref"))
    gp = p["genre"].copy()
    gp["name"] = gp["name"].map(genre_name)
    st.sidebar.bar_chart(gp.set_index("name").n)

# ---------- Main ----------
tab1, tab2 = st.tabs([t("tab_rec"), t("tab_pref")])

with tab2:
    st.write(t("pref_intro"))
    kw = st.text_input(t("search"), key="kw").strip()
    if kw:
        results = search_movies(kw)
        if results.empty:
            st.info(f"🔍 {t('no_result').format(kw=kw)}\n\n{t('no_result_hint')}")
        else:
            for _, m in results.iterrows():
                a, b, c = st.columns([1, 3, 2])
                if m.poster_url: a.image(m.poster_url, width=70)
                b.write(f"{m.title} ({int(m.year) if m.year==m.year else ''})")
                score = c.select_slider(t("rating"), [1, 2, 3, 4, 5], 4, key=f"s{m.movie_id}")
                if c.button(t("submit"), key=f"b{m.movie_id}"):
                    add_rating(uid, int(m.movie_id), float(score)); st.rerun()

with tab1:
    alpha = st.slider(t("slider"), 0.0, 1.0, 0.5, help=t("slider_h"), key="alpha")
    genres = st.multiselect(t("genres"), list_genres(), format_func=genre_name, key="genres")
    if st.button(t("go"), key="go_btn"):
        if p["n"] < 5:
            st.warning(t("need5"))
        else:
            df = recommend(uid, topk=10, alpha=alpha, genres=genres)
            if df.empty:
                st.warning(t("empty"))
            for mid, r in df.iterrows():
                a, b = st.columns([1, 3])
                if r.poster_url: a.image(r.poster_url)
                b.subheader(f"{r.title} ({int(r.year) if r.year==r.year else ''})")
                b.write(f"🎞️ {r.content:.2f}　👥 {r.social:.2f}　⭐ {r.final:.2f}")