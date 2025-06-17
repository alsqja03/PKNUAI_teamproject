import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium
from openai import OpenAI
import openai

pq = "sk-proj-VniTgLPw2NvHFRnnZ-6A6ygka9U-3uCPIfbYLFXXLcBoFIpopYa2eJVXGhXc06Yw"
qp = "yo3E50xRoST3BlbkFJvcMzdaG5JpXLgAWPixiYLd8DIvKePuz0jv0vJP71ubW2_3_loKnA1t2srxe-7E3_5tjt4VNtUA"


#apikey = pq+qp
#client = OpenAI(api_key=apikey)


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
#원래쓰던거 못버려서 갖고옴
def what(place):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"검색기능을 활용해 다음 장소를 한줄로 간략하게 요약해줘. 말투는 ~입니다 체여야하고 장소이름을 굳이 안말해도돼. 장소의특성만 알려주면돼.  {place}"}
        ]
    )
    return response.choices[0].message.content

activity_keywords = [
    "관광지", "핫플레이스", "체험", "명소", "박물관", "전시", "테마파크", "랜드마크", "산책로", "시장", "유적지", "카페거리"
]

def address_to_coord(address, kakao_api_key):
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address}

    response = requests.get(url_keyword, headers=headers, params=params).json()
    documents = response.get("documents", [])

    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        return x, y

    st.error(f"❌ '{address}'에 대한 장소를 찾을 수 없습니다.")
    return None, None
    
# Kakao 장소 검색 (좌표 포함)
def search_places_kakao(query):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 7}
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

# 중복 제거 및 최대 7개까지 채우기
unique_results = []
seen = set()

for r in results:
    if r["name"] not in seen:
        seen.add(r["name"])
        unique_results.append(r)
    if len(unique_results) >= 7:
        break

# 7개 못 채웠으면 블로그 후기 없는 장소도 추가해서 7개 채우기 - 이거 아래는 블로그 없는거임. 블로그 잇는걸 위에 띄우고 7개못차면 없는것도가져옴
if len(unique_results) < 7:
    for kw in activity_keywords:
        places = search_places_kakao(f"{location} {kw}")
        for place in places:
            name = place["place_name"]
            if name in seen:
                continue
            address = place["road_address_name"] or place["address_name"]
            map_url = place["place_url"]
            x = float(place["x"])
            y = float(place["y"])
            unique_results.append({
                "name": name,
                "address": address,
                "map_url": map_url,
                "keywords": [],
                "blogs": [],
                "lat": y,
                "lng": x
            })
            seen.add(name)
            if len(unique_results) >= 7:
                break
        if len(unique_results) >= 7:
            break

# 출력 및 지도 표시
if unique_results:
    avg_lat = sum(r["lat"] for r in unique_results) / len(unique_results)
    avg_lng = sum(r["lng"] for r in unique_results) / len(unique_results)

    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=13)
    for r in unique_results:
        folium.Marker(
            location=[r["lat"], r["lng"]],
            popup=f"{r['name']}\n{r['address']}",
            tooltip=r['name'],
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    st_folium(m, width=700, height=450)

    for r in unique_results:
        if r["name"]:
            st.markdown(f"### 🏛️ {r['name']}")
        else:
            st.markdown("### 🏛️ 이름 없음")

        st.write(f"📌 주소: {r['address']}")
       # st.write(f"설명 : {what(r["name"])}")
        st.markdown(f"🗺️ [지도 보기]({r['map_url']})")
        if r["keywords"]:
            st.write("키워드:", ", ".join(r["keywords"]))
        if r["blogs"]:
            st.write("📰 관련 블로그 후기:")
            for title, link in r["blogs"]:
                st.markdown(f"- [{title}]({link})")
        st.markdown("---")
else:
    st.info("즐길거리를 찾을 수 없습니다. 다른 지역을 입력해 보세요.")
