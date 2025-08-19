# streamlit run index.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

# 페이지 함수 임폴트
from app_pages.auth_page import login_page, signup_page
from app_pages.main_page import main_content
from app_pages.pred_stock_page import predict_stock_page
from app_pages.community_page import community_page
from app_pages.collection_page import collection_page
from app_pages.indicator_page import indicator_page
from app_pages.shop_page import shop_page
from app_pages.analyst_page import analyst_page
from app_pages.mypage_page import mypage_content

# 모듈화된 함수 임폴트
from utils.session import initialize_session_state
from utils.sidebar import sidebar_menu

# 기본 설정
st.set_page_config(page_title="위즈주식", layout="wide", page_icon="📈")

# 세션 상태 초기화 함수 호출
initialize_session_state()

# 공통 스타일
st.markdown("""
    <style>
    /* 라이트 모드일 때의 배경색 */
    .main { 
        background-color: #e6f2ff;
    }
    
    /* 다크 모드일 때의 배경색 */
    @media (prefers-color-scheme: dark) {
        .main {
            background-color: #1a1a1a;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 페이지 라우팅
if st.session_state.authenticated:
    sidebar_menu()
    
    if st.session_state.page == "메인":
        main_content()
    elif st.session_state.page == "주가 예측 게임":
        predict_stock_page()
    elif st.session_state.page == "커뮤니티":
        community_page()
    elif st.session_state.page == "수집 콘텐츠":
        collection_page()
    elif st.session_state.page == "보조지표 제공":
        indicator_page()
    elif st.session_state.page == "포인트 상점":
        shop_page()
    elif st.session_state.page == "애널리스트 페이지":
        analyst_page()
    elif st.session_state.page == "마이페이지":
        mypage_content()
else:
    # 인증되지 않은 경우 로그인 또는 회원가입 페이지 표시
    if st.session_state.page == "로그인":
        login_page()
    elif st.session_state.page == "회원가입":
        signup_page()