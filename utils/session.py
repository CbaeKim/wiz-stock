### 세션 상태 초기화

import streamlit as st

def initialize_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = "로그인"
    if "user_id" not in st.session_state:
        st.session_state.user_id = "test_user"
    if "nickname" not in st.session_state:
        st.session_state.nickname = "테스트 유저"
    if "points" not in st.session_state:
        st.session_state.points = 0
    if "my_trophies" not in st.session_state:
        st.session_state.my_trophies = []
    if "daily_point_bonus" not in st.session_state:
        st.session_state.daily_point_bonus = 0
    if "last_ad_watch_time" not in st.session_state:
        st.session_state.last_ad_watch_time = None
    if "ad_cooldown_active" not in st.session_state:
        st.session_state.ad_cooldown_active = False
    if "game_reset" not in st.session_state:
        st.session_state.game_reset = True
    if "users" not in st.session_state:
        st.session_state.users = {"test_user": {"password": "test_password", "nickname": "테스트 유저"}}
    if "game_cooldown_start_time" not in st.session_state:
        st.session_state.game_cooldown_start_time = None
    if "game_over" not in st.session_state:
        st.session_state.game_over = False
    if "weekly_rankings" not in st.session_state:
        st.session_state.weekly_rankings = {}
    if "last_payout_week" not in st.session_state:
        st.session_state.last_payout_week = None
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if "selected_sub_category" not in st.session_state:
        st.session_state.selected_sub_category = None
    if "indicator_access" not in st.session_state:
        st.session_state.indicator_access = False
    if "last_answer_result" not in st.session_state:
        st.session_state.last_answer_result = None
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = "메인"
    if "analysis_requests" not in st.session_state:
        st.session_state.analysis_requests = {}