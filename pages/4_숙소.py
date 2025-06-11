import streamlit as st
import requests
import urllib.parse
from openai import OpenAI
import folium
from streamlit_folium import st_folium

# 🔐 API 키 설정
OPENAI_API_KEY = "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"
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

# OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)

# TM128 → WGS84 임시 변환 함수 (근사값)
def tm128_to_wgs84(mapx, mapy):
    lon = mapx * 1e-5 - 126.0
    lat = mapy * 1e-5 - 34.0
    return lat, lon

# GPT 숙소 추천

def generate_gpt_based_recommendations(area_name):
    prompt = f"""
한국의 {area_name} 지역에서 실제 검색 가능한 숙소(게스트하우스, 호텔, 리조트 등)를 3~4곳 추천해 주세요.
숙소명은 반드시 한국의 여행 플랫폼(네이버 지도, 야놀자, 여기어때 등)에 실제로 등록된 이름만 사용해 주세요.
숙소명, 위치, 분위기, 추천 이유를 함께 써 주세요.
각 숙소는 마치 여행 블로그에서 소개하듯, 보기 좋게 줄 나눠서 정리해 주세요.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 여행 숙소 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ 추천 생성 오류: {e}")
        return "추천 결과를 생성할 수 없습니다."

# 네이버 장소 검색 API → 위도/경도 변환 포함
def get_location_and_image(place_name, region=None):
    query = f"{region} {place_name}" if region else place_name
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    url = "https://openapi.naver.com/v1/search/local.json"
    params = {"query": query, "display": 1}
    try:
        res = requests.get(url, headers=headers, params=params).json()
        items = res.get("items", [])
        if not items:
            st.warning(f"📍 네이버 장소 검색 실패: {query}")
            return None, None, None
        top = items[0]
        name = top["title"].replace("<b>", "").replace("</b>", "")
        mapx = float(top["mapx"])
        mapy = float(top["mapy"])
        lat, lon = tm128_to_wgs84(mapx, mapy)
        return name, lat, lon
    except Exception as e:
        st.error(f"❌ 네이버 장소 검색 오류: {e}")
        return None, None, None

# 지도 마커 표시 함수
def show_map_with_places(place_list, region):
    m = folium.Map(location=[36.5, 127.5], zoom_start=6)
    added = False
    for place in place_list:
        name, lat, lon = get_location_and_image(place, region=region)
        if lat and lon:
            folium.Marker(
                location=[lat, lon],
                popup=name,
                icon=folium.Icon(color='blue')
            ).add_to(m)
            added = True
        else:
            st.info(f"❌ 마커를 표시할 수 없습니다: {place}")
    if added:
        st.subheader("🗺️ 지도에서 보기")
        st_folium(m, width=700)
    else:
        st.warning("지도에 표시할 숙소가 없습니다.")

# ▶️ Streamlit UI 시작
st.set_page_config(page_title="숙소 추천기", page_icon="🏨")
st.title("🏨 GPT 기반 숙소 추천기 + 지도")
st.markdown("좌측 메뉴 또는 메인 화면에서 입력한 여행지를 기반으로 숙소를 추천해 드립니다.")

# 📥 메인 페이지에서 전달된 지역명 받기
if "location" in st.session_state:
    area_name = st.session_state["location"]
    st.success(f"입력된 여행지: {area_name}")

    with st.spinner("✍️ GPT가 숙소를 추천하는 중..."):
        recommendations = generate_gpt_based_recommendations(area_name)

    st.subheader("📌 GPT 추천 숙소 리스트")
    st.markdown(recommendations, unsafe_allow_html=True)

    # 숙소명 추출
    stay_names = []
    for line in recommendations.split('\n'):
        if line.strip().startswith(tuple(str(i) + '.' for i in range(1, 10))):
            try:
                name = line.split('.', 1)[1].strip()
                stay_names.append(name)
            except:
                continue

    st.write("🎯 추출된 숙소명 리스트:", stay_names)

    if stay_names:
        st.subheader("🏨 숙소 카드 보기 + 검색 링크")
        for stay in stay_names:
            query = urllib.parse.quote(stay)
            search_url = f"https://search.naver.com/search.naver?query={query}"
            image_url = f"https://via.placeholder.com/300x200?text={urllib.parse.quote(stay)}"

            card_html = f"""
            <div style="border:1px solid #ccc; border-radius:10px; padding:16px; margin-bottom:20px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom:10px;">🏨 {stay}</h4>
                <img src="{image_url}" style="width:100%; border-radius:8px; margin-bottom:10px;">
                <a href="{search_url}" target="_blank" style="
                    display:inline-block;
                    padding:8px 16px;
                    background-color:#4CAF50;
                    color:white;
                    text-decoration:none;
                    border-radius:5px;
                    font-weight:bold;
                ">🔎 네이버에서 검색하기</a>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        show_map_with_places(stay_names, region=area_name)
    else:
        st.warning("❗ 숙소 이름을 인식할 수 없어 지도를 표시할 수 없습니다.")
else:
    st.info("여행지를 먼저 입력해주세요. 메인 화면에서 입력하면 여기에 자동으로 연결됩니다.")
