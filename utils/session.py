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
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "step": "initial",
            "can_participate": None,
            "selected_stock_code": None,
            "selected_stock_name": None,
            "prediction_submitted": False
        }
    if "secret_number" not in st.session_state:
        st.session_state.secret_number = 0
    if "guesses" not in st.session_state:
        st.session_state.guesses = 0
    if "game_message" not in st.session_state:
        st.session_state.game_message = ""
    if "game_cooldown_start_time" not in st.session_state:
        st.session_state.game_cooldown_start_time = None
    if "last_guess_value" not in st.session_state:
        st.session_state.last_guess_value = 50
    if "game_over_reason" not in st.session_state:
        st.session_state.game_over_reason = ""
    if "last_attendance_date" not in st.session_state:
        st.session_state.last_attendance_date = None
    if "consecutive_days" not in st.session_state:
        st.session_state.consecutive_days = 0
    if "attendance_points_today_given" not in st.session_state:
        st.session_state.attendance_points_today_given = False
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if "users" not in st.session_state:
        st.session_state.users = {"test_user": {"password": "test_password", "nickname": "테스트 유저"}}
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
