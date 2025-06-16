import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium

# --- 설정 ---
st.set_page_config(page_title="즐길거리 추천기", page_icon="🎡")
st.title("🎡 여행지 즐길거리 추천")

# --- API 키 ---
KAKAO_API_KEY = "12ef3a654aaaed8710e1f5a04454d0a2"
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# --- 여행지 입력 확인 ---
location = st.session_state.get("location")
if not location:
    st.warning("❗ 메인 페이지에서 여행지를 먼저 입력해 주세요.")
    st.stop()

# --- 즐길거리 키워드 ---
activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크",
    "랜드마크", "산책로", "시장", "유적지", "카페거리"
]

# --- Kakao 장소 검색 ---
def search_places_kakao(query):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 15}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params)
    return res.json().get("documents", [])

# --- Kakao 주소 → 좌표 변환 ---
def address_to_coord_kakao(address_or_name):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address_or_name}
    res = requests.get(url, headers=headers, params=params).json()
    docs = res.get("documents", [])
    if docs:
        return float(docs[0]["y"]), float(docs[0]["x"])
    return None, None

# --- 블로그 후기 분석 ---
def analyze_blog_reviews(place_name, full_query):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": full_query,
        "display": 5,
        "sort": "sim"
    }
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

# --- 즐길거리 수집 ---
results = []
for kw in activity_keywords:
    places = search_places_kakao(f"{location} {kw}")
    for place in places:
        name = place["place_name"]
        address = place["road_address_name"] or place["address_name"] or f"{location} {name}"
        map_url = place["place_url"]
        keywords, blog_links = analyze_blog_reviews(name, f"{location} {name}")
        if blog_links:
            results.append({
                "name": name,
                "address": address,
                "map_url": map_url,
                "keywords": keywords,
                "blogs": blog_links
            })

# --- 중복 제거 및 제한 ---
unique_results = []
seen = set()
for r in results:
    if r["name"] not in seen:
        seen.add(r["name"])
        unique_results.append(r)
    if len(unique_results) >= 8:
        break

# --- 결과 출력 ---
if unique_results:
    st.subheader("🔍 추천 즐길거리 목록")
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

    # --- 지도 출력 ---
    st.subheader("📍 지도에서 위치 보기")
    map_center = None
    folium_map = folium.Map(location=[37.5665, 126.9780], zoom_start=12)  # 기본 서울 중심
    marker_count = 0

    for r in unique_results:
        search_query = r["address"] or f"{location} {r['name']}"
        lat, lon = address_to_coord_kakao(search_query)
        if lat and lon:
            if not map_center:
                map_center = [lat, lon]
            popup_html = f"<b>{r['name']}</b><br>{r['address']}<br><a href='{r['map_url']}' target='_blank'>지도 보기</a>"
            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                tooltip=r["name"],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(folium_map)
            marker_count += 1
        else:
            st.warning(f"❌ 위치 좌표를 찾을 수 없습니다: '{r['name']}' / '{search_query}'")

    if marker_count > 0:
        st_folium(folium_map, width=700, height=500)
    else:
        st.info("지도를 표시할 수 있는 위치 정보가 없습니다.")
else:
    st.info("즐길거리를 찾을 수 없습니다. 다른 지역을 입력해 보세요.")
