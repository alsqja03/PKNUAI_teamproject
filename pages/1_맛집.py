#맛집추천 페이지
import streamlit as st
import requests

st.title("🍜 여행지 맛집 추천")

# 여행지 확인
location = st.session_state.get("location")
if not location:
    st.warning("여행지를 먼저 입력해 주세요 (메인 페이지에서)")
    st.stop()

# Kakao API 함수 (직접 포함)
def search_places(query):
    headers = {
        "Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"
    }
    params = {"query": query, "size": 10}
    res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params)
    return res.json().get("documents", [])

# 검색 실행
query = f"{location} 맛집"
results = search_places(query)

# 결과 표시
if results:
    for place in results:
        st.markdown(f"### 📍 {place['place_name']}")
        st.write(f"📌 주소: {place['road_address_name'] or place['address_name']}")
        st.write(f"🔗 [카카오맵 보기]({place['place_url']})")
        st.markdown("---")
else:
    st.info("검색 결과가 없습니다.")
