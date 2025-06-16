import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="즐길거리 추천기", page_icon="🎡")
st.title("🎡 여행지 즐길거리 추천")

# Kakao Local API Key
KAKAO_API_KEY = "12ef3a654aaaed8710e1f5a04454d0a2"

# Naver Search API
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# 여행지 위치 가져오기
location = st.session_state.get("location")
if not location:
    st.warning("❗ 메인 페이지에서 여행지를 먼저 입력해 주세요.")
    st.stop()

# 즐길거리 키워드
activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크", "랜드마크",
    "산책로", "시장", "유적지", "카페거리"
]

# Kakao 장소 검색
def search_places_kakao(query):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 15}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params)
    return res.json().get("documents", [])

# 블로그 리뷰 분석
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

    keyword_candidates = ["뷰", "가성비", "사진", "산책", "데이트", "가족", "체험", "이색", "감성", "전통", "역사", "문화", "힐링", "활동", "동물", "아이", "야경"]
    found_keywords = sorted(set([k for k in keyword_candidates if k in combined_text]))

    return found_keywords, links

# 주소를 좌표로 변환 (위도, 경도 순)
def address_to_coord_kakao(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address}
    res = requests.get(url, headers=headers, params=params).json()
    docs = res.get("documents", [])
    if docs:
        return float(docs[0]["y"]), float(docs[0]["x"])  # (위도, 경도)
    return None, None

# 즐길거리 수집
results = []
for kw in activity_keywords:
    places = search_places_kakao(f"{location} {kw}")
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
                "blogs": blog_links
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

# 출력
if unique_results:
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

    # 🗺️ 지도 시각화
    st.subheader("🗺️ 즐길거리 위치 지도")

    first_lat, first_lon = address_to_coord_kakao(unique_results[0]["address"])
    if not first_lat or not first_lon:
        st.warning("지도를 생성할 수 없습니다. 주소를 확인하세요.")
    else:
        folium_map = folium.Map(location=[first_lat, first_lon], zoom_start=13)
        for r in unique_results:
            lat, lon = address_to_coord_kakao(r["address"])
            if lat and lon:
                popup_html = f"<b>{r['name']}</b><br>{r['address']}<br><a href='{r['map_url']}' target='_blank'>지도 보기</a>"
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_html,
                    tooltip=r["name"],
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(folium_map)

        st_folium(folium_map, width=700, height=500)

else:
    st.info("즐길거리를 찾을 수 없습니다. 다른 지역을 입력해 보세요.")
