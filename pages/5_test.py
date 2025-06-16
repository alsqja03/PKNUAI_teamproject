import streamlit as st
import requests
import re
import pydeck as pdk

st.set_page_config(page_title="즐길거리 추천기", page_icon="🎡")
st.title("🎡 여행지 즐길거리 추천")

# API 키
KAKAO_API_KEY = "12ef3a654aaaed8710e1f5a04454d0a2"
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# 여행지 위치 입력
location = st.session_state.get("location")
if not location:
    st.warning("❗ 메인 페이지에서 여행지를 먼저 입력해 주세요.")
    st.stop()

# Kakao 주소 → 좌표 변환
def get_coordinates(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    res = requests.get("https://dapi.kakao.com/v2/local/search/address.json", headers=headers, params={"query": address})
    documents = res.json().get("documents", [])
    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        return x, y
    return None, None

x, y = get_coordinates(location)
if x is None:
    st.error("위치 좌표를 찾을 수 없습니다.")
    st.stop()

# Kakao 장소 검색 (반경 5km)
def search_places_kakao(query, x, y, radius=5000):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "x": x, "y": y, "radius": radius, "size": 15}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params)
    return res.json().get("documents", [])

# Naver 블로그 후기 분석
def analyze_blog_reviews(place_name, full_query):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": full_query, "display": 5, "sort": "sim"}
    res = requests.get("https://openapi.naver.com/v1/search/blog.json", headers=headers, params=params)
    items = res.json().get("items", [])
    combined_text = ""
    links = []
    for item in items:
        title = re.sub(r"<.*?>", "", item["title"])
        desc = re.sub(r"<.*?>", "", item["description"])
        link = item["link"]
        if place_name in title or place_name in desc:
            combined_text += f"{title} {desc} "
            links.append((title.strip(), link))
        if len(links) >= 3:
            break

    keyword_candidates = [
        "뷰", "가성비", "사진", "산책", "데이트", "가족", "체험", "이색",
        "감성", "전통", "역사", "문화", "힐링", "활동", "동물", "아이", "야경"
    ]
    found_keywords = sorted(set([k for k in keyword_candidates if k in combined_text]))
    return found_keywords, links

# 즐길거리 키워드
activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크",
    "랜드마크", "산책로", "시장", "유적지", "카페거리"
]

# 즐길거리 검색
results = []
for kw in activity_keywords:
    places = search_places_kakao(f"{location} {kw}", x, y)
    for place in places:
        name = place["place_name"]
        address = place["road_address_name"] or place["address_name"]
        map_url = place["place_url"]
        keywords, blog_links = analyze_blog_reviews(name, f"{location} {name}")
        if blog_links:
            results.append({
                "name": name,
                "address": address,
                "map_url": map_url,
                "keywords": keywords,
                "blogs": blog_links,
                "lat": float(place["y"]),
                "lon": float(place["x"])
            })

# 중복 제거 및 최대 8개 제한
unique_results = []
seen = set()
for r in results:
    if r["name"] not in seen:
        seen.add(r["name"])
        unique_results.append(r)
    if len(unique_results) >= 8:
        break

# 출력 및 지도
if unique_results:
    st.subheader("🗺️ 지도에서 즐길거리 보기")
    map_data = [{
        "name": r["name"],
        "lat": r["lat"],
        "lon": r["lon"]
    } for r in unique_results]

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v11",
        initial_view_state=pdk.ViewState(
            latitude=y,
            longitude=x,
            zoom=12,
            pitch=0
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[lon, lat]",
                get_color="[255, 0, 0, 160]",
                get_radius=100,
                pickable=True
            )
        ],
        tooltip={"text": "{name}"}
    ))

    st.subheader("📍 즐길거리 리스트")
    for r in unique_results:
        st.markdown(f"### 🏛️ {r['name']}")
        st.write(f"📌 주소: {r['address']}")
        st.markdown(f"🗺️ [지도 보기]({r['map_url']})")
        if r["keywords"]:
            st.write("💡 후기 키워드:", ", ".join(r["keywords"]))
        if r["blogs"]:
            st.write("📰 관련 블로그 후기:")
            for title, link in r["blogs"]:
                st.markdown(f"- [{title}]({link})")
        st.markdown("---")
else:
    st.info("즐길거리를 찾을 수 없습니다. 다른 지역을 입력해 보세요.")
