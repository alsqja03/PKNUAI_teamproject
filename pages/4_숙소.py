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

# 🧠 사용자 입력에서 지역명 추출
def extract_area_name(user_input):
    prompt = f'다음 문장에서 한국의 여행 지역명을 하나만 뽑아줘. 예: "{user_input}" → "제주"'
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "넌 한국 지역명을 뽑는 도우미야. 지역명만 한 단어로 출력해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ 지역 추출 오류: {e}")
        return None

# 🧠 GPT로 숙소 추천 받기
def generate_gpt_based_recommendations(area_name, user_input):
    prompt = f"""
한국의 {area_name} 지역에서 여행하려는 사람이 있습니다.
입력 내용: \"{user_input}\"
이 사람에게 적합한 숙소를 3~4곳 추천해 주세요. 숙소명(가상 가능), 위치, 분위기, 추천 이유를 함께 써 주세요.
각 숙소는 마치 여행 블로그에서 소개하듯, 짧게 설명해 주세요.
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
def get_location_and_image(place_name):
    headers = {"Authorization": KAKAO_API_KEY}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": place_name}
    try:
        res = requests.get(url, headers=headers, params=params).json()
        documents = res.get("documents", [])
        if not documents:
            return None, None, None
        top = documents[0]
        name = top["place_name"]
        lat = float(top["y"])
        lon = float(top["x"])
        return name, lat, lon
    except:
        return None, None, None

# 🗺️ 지도에 마커 표시
def show_map_with_places(place_list):
    m = folium.Map(location=[36.5, 127.5], zoom_start=6)
    for place in place_list:
        name, lat, lon = get_location_and_image(place)
        if lat and lon:
            folium.Marker(
                location=[lat, lon],
                popup=name,
                icon=folium.Icon(color='blue')
            ).add_to(m)
    st.subheader("🗺️ 지도에서 보기")
    st_folium(m, width=700)

# ▶️ Streamlit UI
st.title("🏨 자연어 기반 숙소 추천기 + 지도")
user_input = st.text_input("어디로 여행 가고 싶으세요?", placeholder="예: 부모님과 함께 조용한 바닷가 여행")

if user_input:
    with st.spinner("🧠 여행지 파악 중..."):
        area_name = extract_area_name(user_input)

    if area_name:
        st.success(f"추출된 지역: {area_name}")

        with st.spinner("✍️ GPT가 숙소를 추천하는 중..."):
            recommendations = generate_gpt_based_recommendations(area_name, user_input)

        st.subheader("📌 GPT 추천 숙소 리스트")
        st.write(recommendations)

        # 숙소명 추출 (예외 방지형 안전 버전)
        stay_names = []
        for line in recommendations.split('\n'):
            if line.strip().startswith(tuple(str(i) + '.' for i in range(1, 10))):
                try:
                    if '숙소명:' in line:
                        name = line.split('숙소명:')[1].split('위치')[0].strip().replace(':', '')
                        stay_names.append(name)
                except:
                    continue

        # 지도에 표시
        if stay_names:
            show_map_with_places(stay_names)
        else:
            st.warning("❗ 숙소 이름을 인식할 수 없어 지도를 표시할 수 없습니다.")
    else:
        st.warning("지역명을 인식하지 못했어요. 다시 입력해 주세요.")
