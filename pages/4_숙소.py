import streamlit as st
import requests
import urllib.parse
from openai import OpenAI

# 🔐 API 키 설정
OPENAI_API_KEY = "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"
NAVER_CLIENT_ID = "wxZvR_Hx1sBwjb1rnxBZ"
NAVER_CLIENT_SECRET = "Hhznyt4xzf"

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_gpt_based_recommendations(area_name):
    prompt = f"""
한국의 {area_name} 지역에서 실제 검색 가능한 숙소(게스트하우스, 호텔, 리조트 등)를 3~4곳 추천해 주세요.
숙소명은 반드시 네이버 지도에 등록된 실제 이름만 사용해 주세요.
검색 가능한 이름이 아니면 포함하지 마세요.
다음 형식을 유지하여 출력해 주세요 (줄바꿈 포함):

숙소명: 팔레드 시즈 리조트
위치: 부산광역시 해운대구 송정동 147-8
분위기: 바다가 한 눈에 보이는 리조트로, 로맨틱하고 프라이빗한 분위기를 즐길 수 있습니다.
추천 이유: 부산의 아름다운 해변을 전망하면서 휴식을 취할 수 있는 곳입니다. 또한, 조식이 포함되어 있어 편리하게 이용할 수 있습니다.
네이버 블로그 후기: 넓은 테라스에서 바라보는 부산의 야경이 아름답다는 후기가 많습니다. 또한, 깨끗하고 세련된 인테리어에 만족하는 손님들이 많습니다.
평점: 4.5/5

이 포맷을 그대로 사용해 주세요.
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

st.set_page_config(page_title="숙소 추천기", page_icon="🏨")
st.title("🏨 GPT 기반 숙소 추천기")
st.markdown("좌측 메뉴 또는 메인 화면에서 입력한 여행지를 기반으로 숙소를 추천해 드립니다.")

if "location" in st.session_state:
    area_name = st.session_state["location"]
    st.success(f"입력된 여행지: {area_name}")

    with st.spinner("✍️ GPT가 숙소를 추천하는 중..."):
        recommendations = generate_gpt_based_recommendations(area_name)

    st.subheader("📌 GPT 추천 숙소 리스트")

    # 카드 단위로 파싱하여 출력
    blocks = recommendations.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        data = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        if "숙소명" in data:
            blog_search_url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(data['숙소명'] + ' 후기')}"
            rating_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(data['숙소명'])}"
            card_html = f"""
            <div style="border:1px solid #ccc; border-radius:10px; padding:16px; margin-bottom:20px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom:10px;">🏨 {data.get('숙소명')}</h4>
                <p>📍 <strong>위치:</strong> {data.get('위치', '정보 없음')}</p>
                <p>🌅 <strong>분위기:</strong> {data.get('분위기', '정보 없음')}</p>
                <p>✅ <strong>추천 이유:</strong> {data.get('추천 이유', '정보 없음')}</p>
                <p>✍️ <strong>네이버 블로그 후기:</strong> {data.get('네이버 블로그 후기', '정보 없음')}</p>
                <p>⭐ <strong>평점:</strong> {data.get('평점', '정보 없음')}</p>
                <a href="{blog_search_url}" target="_blank" style="
                    display:inline-block;
                    margin-top:8px;
                    padding:8px 16px;
                    background-color:#4CAF50;
                    color:white;
                    text-decoration:none;
                    border-radius:5px;
                    font-weight:bold;
                ">🔗 네이버 블로그 후기 보기</a>
                <br>
                <a href="{rating_url}" target="_blank" style="
                    display:inline-block;
                    margin-top:8px;
                    padding:8px 16px;
                    background-color:#2196F3;
                    color:white;
                    text-decoration:none;
                    border-radius:5px;
                    font-weight:bold;
                ">⭐ 지도에서 평점 확인</a>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("여행지를 먼저 입력해주세요. 메인 화면에서 입력하면 여기에 자동으로 연결됩니다.")
