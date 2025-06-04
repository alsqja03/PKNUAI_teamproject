#숙소 예약
import streamlit as st
import requests
import xml.etree.ElementTree as ET
from streamlit.components.v1 import html
import openai  # OpenAI 연동 추가

# 🔐 API 키들
TOUR_API_KEY = "여기에_공공데이터포털_인증키"
NAVER_CLIENT_ID = "여기에_네이버_Client_ID"
NAVER_CLIENT_SECRET = "여기에_네이버_Client_Secret"
KAKAO_REST_API_KEY = "여기에_카카오_REST_API_키"
KAKAO_JS_KEY = "여기에_카카오_JS_키"
OPENAI_API_KEY = "여기에_OpenAI_API_키"

openai.api_key = OPENAI_API_KEY

AREA_CODES = {
    "서울": 1,
    "부산": 6,
    "제주": 39,
    "강원": 32,
    "경기": 31,
    "인천": 2
}

def normalize_region(user_input):
    """OpenAI를 사용하여 사용자의 입력을 지역 키워드로 정규화"""
    system_msg = "다음은 여행지 관련 사용자 입력입니다. 이를 가능한 정확한 한국의 지역명으로 정규화해서 대답하세요. 가능한 값은 " + ", ".join(AREA_CODES.keys()) + " 중 하나입니다. 오타나 대충 쓴 말도 알아서 고쳐주세요. 다른 설명은 필요 없고, 지역명만 한 단어로 대답하세요."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

def search_blog_reviews(query):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": 2, "sort": "sim"}
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        return res.json().get("items", [])
    return []

def get_coordinates(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": address}
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        documents = res.json().get("documents", [])
        if documents:
            return documents[0]["y"], documents[0]["x"]
    return None, None

def display_map(y, x):
    map_html = f"""
    <div id="map" style="width:100%;height:350px;"></div>
    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>
    <script>
      var container = document.getElementById('map');
      var options = {{
        center: new kakao.maps.LatLng({y}, {x}),
        level: 3
      }};
      var map = new kakao.maps.Map(container, options);
      var marker = new kakao.maps.Marker({{
          position: new kakao.maps.LatLng({y}, {x})
      }});
      marker.setMap(map);
    </script>
    """
    html(map_html, height=370)

# 🌍 Streamlit 인터페이스
st.title("🌐 자유 입력 기반 숙소 추천 도우미")
user_input = st.text_input("여행지를 입력해 주세요 (예: '제주 가고 싶어', '서울 근처로 여행갈래요' 등)")

if st.button("숙소 추천 보기"):
    if not user_input.strip():
        st.warning("여행지를 입력해 주세요.")
    else:
        with st.spinner("여행 지역 파악 중..."):
            region = normalize_region(user_input)
        
        if region not in AREA_CODES:
            st.error(f"'{region}' 지역은 현재 지원하지 않습니다.")
        else:
            st.success(f"🎯 인식된 여행 지역: {region}")
            area_code = AREA_CODES[region]

            # 공공데이터 API 호출
            with st.spinner("숙소 정보를 불러오는 중..."):
                url = "http://apis.data.go.kr/B551011/KorService1/searchStay1"
                params = {
                    "ServiceKey": TOUR_API_KEY,
                    "areaCode": area_code,
                    "MobileOS": "ETC",
                    "MobileApp": "TravelApp",
                    "arrange": "A",
                    "numOfRows": 3,
                    "pageNo": 1,
                    "listYN": "Y"
                }

                response = requests.get(url, params=params)
                root = ET.fromstring(response.content)
                items = root.findall(".//item")

                if not items:
                    st.warning("숙소 데이터를 찾을 수 없습니다.")
                else:
                    for item in items:
                        title = item.findtext("title", default="제목 없음")
                        addr = item.findtext("addr1", default="주소 없음")
                        image = item.findtext("firstimage", default="")

                        st.subheader(title)
                        st.write(f"📍 {addr}")
                        if image:
                            st.image(image, width=300)

                        # 지도 출력
                        y, x = get_coordinates(addr)
                        if y and x:
                            display_map(y, x)
                        else:
                            st.write("📌 지도 정보를 불러올 수 없습니다.")

                        # 블로그 리뷰
                        st.markdown("**📝 관련 블로그 리뷰:**")
                        blog_results = search_blog_reviews(title)
                        if blog_results:
                            for blog in blog_results:
                                st.markdown(f"- [{blog['title']}]({blog['link']})")
                        else:
                            st.write("리뷰가 없습니다.")
                        st.markdown("---")
