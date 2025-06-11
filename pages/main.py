import streamlit as st
import food
import activities
import transport
import accommodation

def main():
    st.sidebar.title("여행 정보 페이지")
    page = st.sidebar.radio("페이지 선택", ["여행지 입력", "맛집", "즐길거리", "교통편", "숙소"])
    
    if page == "여행지 입력":
        destination = st.text_input("여행지를 입력하세요")
        if destination:
            st.session_state['destination'] = destination
            st.success(f"여행지가 '{destination}' 로 설정되었습니다.")
        else:
            st.info("여행지를 입력해주세요.")

    elif page == "맛집":
        food.app()

    elif page == "즐길거리":
        activities.app()

    elif page == "교통편":
        transport.app()

    elif page == "숙소":
        accommodation.app()

if __name__ == "__main__":
    main()
