import streamlit as st
import pandas as pd
from datetime import date
from .ranking import display_ranking_sidebar, award_weekly_points 

def sidebar_menu():
    menu_options = [
        "메인", "주가 예측 게임", "커뮤니티", "수집 콘텐츠",
        "보조지표 제공", "포인트 상점", "애널리스트 페이지", "마이페이지", "로그아웃"
    ]

    with st.sidebar:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("<div style='font-size: 26px; font-weight: bold; color: #007acc;'>📈 위즈주식</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🏠"):
                st.session_state.page = "메인"
                st.rerun()

        st.title("📌 메뉴")
        choice = st.radio("이동하기", menu_options, key="radio_menu_choice")
        
        if choice != st.session_state.page:
            st.session_state.page = choice
            st.rerun()

        st.markdown("---")

        # 오늘의 퀘스트 로직
        render_daily_quest()
        st.markdown("---")
        
        # 주간 랭킹
        display_ranking_sidebar()
        award_weekly_points()

# 오늘의 퀘스트 UI를 렌더링
def render_daily_quest():
    today = date.today().isoformat()
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None, "step": "select_topic", "quiz_data": pd.DataFrame(),
            "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False
        }

    log = st.session_state.study_log[today]
    if "balloons_shown_for_quest" not in log:
        log["balloons_shown_for_quest"] = False

    today_point = log.get("point", 0)
    goal_point = 10

    with st.expander("🎯 오늘의 퀘스트"):
        st.markdown(f"오늘의 목표: **{goal_point}점**")
        st.markdown(f"현재 획득 포인트: **{today_point}점**")
        progress = min(today_point / goal_point, 1.0)
        st.progress(progress)

        if today_point >= goal_point:
            st.success("✅ 오늘의 퀘스트를 완료했어요! 🎉")
            if not log["balloons_shown_for_quest"]:
                st.balloons()
                log["balloons_shown_for_quest"] = True
        else:
            st.markdown(f"🔥 목표까지 **{goal_point - today_point}점** 남았어요! 힘내세요 💪")
            log["balloons_shown_for_quest"] = False
