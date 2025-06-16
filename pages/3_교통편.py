import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

st.set_page_config(page_title="즐길거리 추천기", page_icon="🎡")
st.title("🎡 여행지 즐길거리 추천")

# Kakao & Naver API 키
KAKAO_API_KEY = "12ef3a654aaaed8710e1f5a04454d0a2"
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# 여행지 입력 (메인 페이지에서 전달)
location = st.session_state.get("location")
if not location:
    st.warning("❗ 메인 페이지에서 여행지를 먼저 입력해 주세요.")
    st.stop()

# 반경 제한
RADIUS_KM = 5.0

# 즐길거리 키워드
activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크", "랜드마크", "산책로", "시장", "유적지", "카페거리"
]

# 위치를 좌표로 변환 (키워드 검색)
def get_coordinates(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params).json()
    documents = res.get("documents", [])
    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        return x, y
    return None, None

# 두 좌표 간 거리 계산 (단위: km)
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

# Kakao 장소 검색
def search_places_kakao(query):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 15}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params)
    return res.json().get("documents", [])

# Naver 블로그 후기 분석
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
        "뷰", "가성비", "사진", "산책", "데이트", "가족", "체험", "이색", "감성", "전통", "역사", "문화", "힐링", "활동", "동물", "아이", "야경"
    ]
    found_keywords = sorted(set([k for k in keyword_candidates if k in combined_text]))

    return found_keywords, links

# 여행지 기준 좌표 구하기
center_x, center_y = get_coordinates(location)
if center_x is None:
    st.error("여행지 좌표를 찾을 수 없습니다.")
    st.stop()

# 즐길거리 탐색 및 결과 수집
results = []
for kw in activity_keywords:
    places = search_places_kakao(f"{location} {kw}")
    for place in places:
        name = place["place_name"]
        address = place["road_address_name"] or place["address_name"]
        map_url = place["place_url"]
        x = float(place["x"])
        y = float(place["y"])
        distance = haversine(center_x, center_y, x, y)

        if distance <= RADIUS_KM:
            keywords, blog_links = analyze_blog_reviews(name, f"{location} {name}")
            if blog_links:
                results.append({
                    "name": name,
                    "address": address,
                    "map_url": map_url,
                    "keywords": keywords,
                    "blogs": blog_links,
                    "lat": y,
                    "lon": x
                })

# 중복 제거 및 최대 8개
unique_results = []
seen = set()
for r in results:
    if r["name"] not in seen:
        seen.add(r["name"])
        unique_results.append(r)
    if len(unique_results) >= 8:
        break

# 출력
if unique_results:
    st.subheader("📍 추천 즐길거리 목록")
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

    # 지도 시각화
    st.subheader("🗺️ 지도에서 보기")
    map_center = [unique_results[0]["lat"], unique_results[0]["lon"]]
    m = folium.Map(location=map_center, zoom_start=13)

    for r in unique_results:
        blog_html = "<br>".join([f'<a href="{url}" target="_blank">{title}</a>' for title, url in r["blogs"]])
        popup_html = f"<b>{r['name']}</b><br>{r['address']}<br><br>{blog_html}"
        folium.Marker(
            location=[r["lat"], r["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=r["name"],
            icon=folium.Icon(color="blue")
        ).add_to(m)

    st_folium(m, width=700, height=500)

else:
    st.info("반경 5km 이내에서 즐길거리를 찾을 수 없습니다. 다른 지역을 시도해 보세요.")
💡 추가 안내
