import openai
import ast
import os
import requests
import folium
from streamlit_folium import st_folium
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

KAKAO_API_KEY = "83c0445f5fc4a2ee846f09e47fb00187"

apikey = st.text_input("openai api key를 입력하세요 :", type = "password")
st.session_state.api_key = apikey
client = OpenAI(api_key=apikey)



# 1. 장소 키워드로 좌표 얻기
def get_coordinates_by_keyword(query):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        documents = response.json()['documents']
        if documents:
            first = documents[0]
            return float(first['x']), float(first['y'])  # (longitude, latitude)
    return None

# 2. 좌표 기준으로 업종별 장소 검색
def find_places_by_categories(x, y, category_codes, radius=1000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    all_results = []

    for code in category_codes:
        params = {
            "category_group_code": code,
            "x": x,
            "y": y,
            "radius": radius,
            "sort": "distance"
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            all_results += response.json()['documents']

    return all_results

# 3. 장소이름 → 결과 목록 + 좌표 반환
def search_nearby_places_list(place_name, category_codes):
    coords = get_coordinates_by_keyword(place_name)
    if not coords:
        print("❌ 장소 좌표를 찾을 수 없습니다.")
        return [], None

    x, y = coords
    results = find_places_by_categories(x, y, category_codes)
    output_list = []

    for place in results:
        name = place['place_name']
        address = place.get('road_address_name') or place.get('address_name')
        lat = float(place['y'])
        lon = float(place['x'])
        output_list.append([name, address, lat, lon])  # 장소명, 주소, 위도, 경도

    return output_list, (x, y)  # 장소 목록과 좌표 함께 반환

# 📍 검색 대상
where = st.session_state["location"]
data, coords = search_nearby_places_list(where, ["CT1", "AT4"])

# 📋 정보 출력
if coords:
    st.write(f"🔍 검색 장소: {where}")
    st.write(f"📍 좌표: 경도 {coords[0]}, 위도 {coords[1]}")
    # 지도 생성
    m = folium.Map(location=[coords[1], coords[0]], zoom_start=15)

    # 기준 장소 마커
    folium.Marker(location=[coords[1], coords[0]], popup=where, tooltip="검색 장소").add_to(m)

    # 주변 장소 10개 마커
    for place in data[:10]:
        coords_place = get_coordinates_by_keyword(place[0])
        if coords_place:
            folium.Marker(location=[coords_place[1], coords_place[0]], popup=place[0], tooltip=place[1]).add_to(m)

    # 지도 스트림릿에 띄우기
    st_folium(m, width=700, height=500)
else:
    st.error("❌ 장소 좌표를 불러올 수 없습니다.")

if len(data) >= 1:
    st.write("▶️ 주변 장소:")
    for i, item in enumerate(data[:5]):  # 최대 5개 표시
        st.write(f"{i+1}. 위치: {item[0]} , 주소: {item[1]}")

def what(place):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"검색기능을 활용해 다음 장소를 한줄로 간략하게 요약해줘. {place}"}
        ]
    )
    return response.choices[0].message.content

for i in [0,1,2,3,4]:
    w = data[i][0]
    contents = what(w)
    st.write(contents)
