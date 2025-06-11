import streamlit as st
import requests
import urllib.parse
from openai import OpenAI
import folium
from streamlit_folium import st_folium

# 🔐 API 키 설정
OPENAI_API_KEY = "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"  # 여기에 본인의 OpenAI API 키 입력
KAKAO_API_KEY = "KakaoAK b3759742989e0c923c37d8baf058f95c"  # 여기에 본인의 Kakao REST API 키 입력

# OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)

# 🧠 GPT로 숙소 추천 받기
def generate_gpt_based_recommendations(area_name):
    prompt = f"""
한국의 {area_name} 지역에서 실제 존재할 법한 숙소(게스트하우스, 리조트 등)를 3~4곳 추천해 주세요.
숙소명, 위치, 분위기, 추천 이유를 함께 써 주세요.
각 숙소는 마치 여행 블로그에서 소개하듯, 줄 나눠서 보기 좋게 정리해 주세요.
- 실제 한국 여행 플랫폼(네이버 지도, 야놀자, 여기어때 등)에서 검색 가능한 실제 숙소명을 추천해 주세요.
- 반드시 전체 이름을 포함하고, 지역명도 정확히 명시해 주세요.
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

# 📍 숙소명으로 좌표 검색 (카카오 API)
def get_location_and_image(place_name, region=None):
    query = f"{region} {place_name}" if region else place_name
    headers = {"Authorization": KAKAO_API_KEY}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": query}
    try:
        res = requests.get(url, headers=headers, params=params).json()
        documents = res.get("documents", [])
        if not documents:
            st.warning(f"📍 카카오 검색 실패: {query}")
            return None, None, None
        top = documents[0]
        name = top["place_name"]
        lat = float(top["y"])
        lon = float(top["x"])
        return name, lat, lon
    except Exception as e:
        st.error(f"❌ 좌표 검색 오류: {e}")
        return None, None, None

# 🗺️ 지도에 마커 표시
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
                name = line.split('.')[1].split('(')[0].strip()
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
