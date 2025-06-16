import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="즐길거리 추천기", page_icon="🎡")
st.title("🎡 여행지 즐길거리 추천")

# Kakao Local API Key
KAKAO_API_KEY = "cf0f3e08c8579cf39f37df048fc9802a"

# Naver Search API
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# 여행지 위치 가져오기
location = st.session_state.get("location")
if not location:
    st.warning("❗ 메인 페이지에서 여행지를 먼저 입력해 주세요.")
    st.stop()

activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크", "랜드마크", "산책로", "시장", "유적지", "카페거리"
]

# Kakao 장소 검색 (좌표 포함)
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

# 즐길거리 검색
results = []
for kw in activity_keywords:
    places = search_places_kakao(f"{location} {kw}")
    for place in places:
        name = place["place_name"]
        address = place["road_address_name"] or place["address_name"]
        map_url = place["place_url"]
        x = float(place["x"])  # 경도
        y = float(place["y"])  # 위도
        keywords, blog_links = analyze_blog_reviews(name, f"{location} {name}")
        if blog_links:
            results.append({
                "name": name,
                "address": address,
                "map_url": map_url,
                "keywords": keywords,
                "blogs": blog_links,
                "lat": y,
                "lng": x
            })

# 중복 제거 및 최대 7개 제한
unique_results = []
seen = set()
for r in results:
    if r["name"] not in seen:
        seen.add(r["name"])
        unique_results.append(r)
    if len(unique_results) >= 7:
        break

# 출력 및 지도 표시
if unique_results:
    # 지도의 초기 중심 좌표: 첫 장소 기준
    map_center = [unique_results[0]["lat"], unique_results[0]["lng"]]
    m = folium.Map(location=map_center, zoom_start=13)

    for r in unique_results:
        # 마커 추가
        popup_content = f"<b>{r['name']}</b><br>{r['address']}<br>"
        if r["keywords"]:
            popup_content += f"후기 키워드: {', '.join(r['keywords'])}<br>"
        if r["blogs"]:
            popup_content += "<a href='{}' target='_blank'>블로그 후기 보기</a>".format(r["blogs"][0][1])
        folium.Marker(
            [r["lat"], r["lng"]],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=r["name"],
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # 왼쪽에 리스트, 오른쪽에 지도 배치
    col1, col2 = st.columns([1, 2])
    with col1:
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

    with col2:
        st_folium(m, width=700, height=600)

else:
    st.info("즐길거리를 찾을 수 없습니다. 다른 지역을 입력해 보세요.")
