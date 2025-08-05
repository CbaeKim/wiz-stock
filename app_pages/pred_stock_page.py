### 서브 콘텐츠 1: 주가 예측 게임

import streamlit as st
import random
from datetime import date, timedelta
from utils.ranking import update_user_points 

# 예시용 종목 리스트
kospi_stocks = ["삼성전자", "LG화학", "현대차", "카카오", "POSCO"]

# 예시용 가격 함수
def get_current_price(stock_name):
    return random.randint(50000, 150000)

def get_previous_close(stock_name):
    return random.randint(50000, 150000)

def predict_stock_page():
    st.title("📊 주가 예측 게임")
    today = date.today()

    # 세션 상태 초기화
    if "points" not in st.session_state:
        st.session_state.points = 0
    if "today_prediction_done" not in st.session_state:
        st.session_state.today_prediction_done = False
        
    # 예측 기록이 있고, 그 기록이 오늘 날짜가 아니면 (어제 기록으로 간주)
    if "predicted_stock_date" in st.session_state and st.session_state.predicted_stock_date != today:
        st.subheader("🕵️ 어제 예측 결과 확인")
        yesterday_stock = st.session_state.predicted_stock
        yesterday_direction = st.session_state.predicted_direction

        # 예측 당시 가격과 오늘 종가
        prev_price = st.session_state.get("predicted_price_at_time_of_prediction", get_previous_close(yesterday_stock))
        curr_price = get_current_price(yesterday_stock)

        actual_direction = (
            "상승" if curr_price > prev_price else
            "하락" if curr_price < prev_price else
            "유지"
        )
        
        st.markdown(f"""
        **어제 예측 결과**
        - 종목: **{yesterday_stock}**
        - 예측 방향: **{yesterday_direction}**
        - 예측 시점 가격: {prev_price}원
        - 오늘 종가: {curr_price}원
        - 실제 방향: **{actual_direction}**
        """)

        if yesterday_direction == actual_direction:
            st.success("정답입니다! 🎉 포인트 +5")
            st.session_state.points += 5
            update_user_points(st.session_state.user_id, 5)
        else:
            st.info("아쉽게 틀렸어요. 포인트 +2")
            st.session_state.points += 2
            update_user_points(st.session_state.user_id, 2)
            
        # 예측 기록 초기화 (결과 확인 후)
        if "predicted_stock" in st.session_state: del st.session_state.predicted_stock
        if "predicted_direction" in st.session_state: del st.session_state.predicted_direction
        if "predicted_stock_date" in st.session_state: del st.session_state.predicted_stock_date
        if "predicted_price_at_time_of_prediction" in st.session_state: del st.session_state.predicted_price_at_time_of_prediction
        st.session_state.today_prediction_done = False
        st.rerun()

    # 오늘 예측 진행
    elif not st.session_state.today_prediction_done:
        st.subheader("📅 오늘의 종가 예측")
        selected_stock = st.selectbox("종목을 선택하세요", kospi_stocks)
        current_price = get_current_price(selected_stock)

        st.markdown(f"**현재가: {current_price}원**")
        prediction = st.radio("예측 방향 선택", ("상승", "하락", "유지"))

        if st.button("예측 완료"):
            st.session_state.today_prediction_done = True
            st.session_state.predicted_stock = selected_stock
            st.session_state.predicted_direction = prediction
            st.session_state.predicted_price_at_time_of_prediction = current_price
            st.session_state.predicted_stock_date = today

            st.success("✅ 예측이 완료되었습니다! 내일 결과를 확인해보세요.")
            st.markdown(f"**오늘의 예측: {prediction}**")
            st.rerun()
    else:
        st.info("오늘의 예측은 이미 완료했어요. 내일 결과를 확인해보세요!")
        st.markdown(f"**오늘의 예측:** **{st.session_state.predicted_direction}**")

    st.markdown(f"---")
    st.markdown(f"🌟 현재 포인트: **{st.session_state.points}점**")
