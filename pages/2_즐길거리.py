import openai
import langchain
import ast
import os
import requests
import folium
from streamlit_folium import st_folium
from langchain_openai import ChatOpenAI
import streamlit as st
import streamlit.components.v1 as components

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_community.tools import DuckDuckGoSearchResults
from langgraph.prebuilt import create_react_agent

# ✅ Kakao API Key
KAKAO_API_KEY = "83c0445f5fc4a2ee846f09e47fb00187"

# ✅ 장소 키워드로 좌표 얻기
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

# ✅ 좌표 기준으로 업종별 장소 검색
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

# ✅ 장소이름 → 결과 목록 + 좌표 반환
def search_nearby_places_list(place_name, category_codes):
    coords = get_coordinates_by_keyword(place_name)
    if not coords:
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

    return output_list, (x, y)

# ✅ Streamlit UI 시작
st.title("📍 주변 장소 탐색")

# ✅ Main 페이지에서 입력된 장소 사용
if "location" in st.session_state and st.session_state["location"]:
    where = st.session_state["location"]
    st.info(f"사용자가 입력한 장소: **{where}** 기준으로 검색합니다.")
else:
    st.warning("⚠️ 메인 페이지에서 여행지를 먼저 입력해주세요.")
    st.stop()

# ✅ 장소 검색 실행
data, coords = search_nearby_places_list(where, ["CT1", "AT4"])  # 문화시설, 관광명소 등

if coords:
    st.write(f"🔍 검색 장소: {where}")
    st.write(f"📍 좌표: 경도 {coords[0]}, 위도 {coords[1]}")
    
    m = folium.Map(location=[coords[1], coords[0]], zoom_start=15)
    folium.Marker(location=[coords[1], coords[0]], popup=where, tooltip="검색 장소").add_to(m)

    for place in data[:10]:
        folium.Marker(location=[place[2], place[3]], popup=place[0], tooltip=place[1]).add_to(m)

    st_folium(m, width=700, height=500)

    st.write("▶️ 주변 장소:")
    for i, item in enumerate(data[:5]):
        st.write(f"{i+1}. 위치: {item[0]} , 주소: {item[1]}")
else:
    st.error("❌ 입력한 장소의 좌표를 찾을 수 없습니다.")
