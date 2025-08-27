# wiz-stock/app/pages/predict_stock.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 설정
API_BASE_URL = "http://localhost:8000/stock-predict"

# API 호출 함수
def api_request(method, endpoint, params=None, json=None, ttl=60):
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method.upper() == 'GET':
            # GET 요청에 대해서만 캐싱 적용
            @st.cache_data(ttl=ttl)
            def cached_get_request(url, params):
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response.json()
            return cached_get_request(url, params)
        
        elif method.upper() == 'POST':
            response = requests.post(url, json=json)
            response.raise_for_status()
            return response.json()
            
    except requests.exceptions.HTTPError as e:
        st.error(f"오류: {e.response.status_code} - {e.response.json().get('detail', '내용 없음')}")
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {e}")
    except Exception as e:
        st.error(f"예기치 않은 오류가 발생했습니다: {e}")
    return None

# 페이지 상태 초기화
def initialize_session_state():
    """세션 상태 변수들을 초기화"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = "test_user_001"
    if "page_view" not in st.session_state:
        st.session_state.page_view = "main"
    if "can_participate" not in st.session_state:
        st.session_state.can_participate = None

# UI 컴포넌트
def show_main_menu():
    """메인 메뉴 UI를 표시"""
    st.subheader("무엇을 하시겠어요?")
    
    if st.session_state.can_participate is None:
        with st.spinner("참여 가능 여부를 확인 중입니다..."):
            res = api_request("GET", "check-participation", params={"user_id": st.session_state.user_id})
            if res:
                st.session_state.can_participate = res.get("can_participate", False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("오늘의 예측 참여하기", key="go_to_predict", disabled=not st.session_state.can_participate):
            st.session_state.page_view = "predict"
            st.rerun()
        if not st.session_state.can_participate:
            st.info("오늘은 이미 예측에 참여했습니다.")

    with col2:
        if st.button("지난 예측 결과 확인", key="go_to_history"):
            st.session_state.page_view = "history"
            st.rerun()

def show_prediction_game():
    """주가 예측 게임 UI를 표시"""
    st.subheader("🕵️ 오늘의 예측")
    if st.button("메인 메뉴로 돌아가기", key="back_from_predict"):
        st.session_state.page_view = "main"
        st.rerun()

    with st.spinner("종목 목록을 불러오는 중입니다..."):
        top10_stocks = api_request("GET", "get-top10", ttl=3600)

    if not top10_stocks:
        st.warning("종목 목록을 불러올 수 없습니다. 데이터 파이프라인을 확인해주세요.")
        return

    stock_map = {item['stock_name']: item['stock_code'] for item in top10_stocks}
    selected_stock_name = st.selectbox("종목을 선택하세요", list(stock_map.keys()), key="stock_select")
    
    if selected_stock_name:
        selected_stock_code = stock_map[selected_stock_name]
        stock_info = api_request("GET", "get-stock-info", params={"stock_code": selected_stock_code}, ttl=3600)
        
        if stock_info:
            st.markdown(f"**현재가: {stock_info['current_price']:,}원**")
            
            with st.expander("AI 모델 분석 결과 보기"):
                st.markdown(f"""
                - **다음날 예측 등락**: {stock_info['trend_predict']}
                - **다음날 예측 종가**: {stock_info['price_predict']:,}원
                - **가장 영향력 있는 지표**: {stock_info['top_feature']}
                - **감성 분석 전망**: {stock_info['sentiment_outlook']}
                """)
            
            user_prediction = st.radio("예측 방향 선택", ("상승", "하락"), key="user_predict_radio", horizontal=True)

            if st.button("예측 완료", key="submit_button", type="primary"):
                submit_result = api_request("POST", "submit-prediction", json={
                    "user_id": st.session_state.user_id,
                    "stock_code": selected_stock_code,
                    "user_predict_trend": user_prediction
                })
                if submit_result:
                    st.success("✅ 예측이 성공적으로 제출되었습니다! 내일 결과를 확인하세요.")
                    st.session_state.can_participate = False
                    st.session_state.page_view = "main"
                    st.balloons()
                    st.rerun()

def show_history_page():
    """지난 예측 결과 및 전체 기록 UI를 표시"""
    st.subheader("📈 전체 예측 기록")
    if st.button("메인 메뉴로 돌아가기", key="back_from_history"):
        st.session_state.page_view = "main"
        st.rerun()

    st.info("결과는 매일 다음날 오후 4시 30분 이후 자동으로 채점 및 업데이트됩니다.")
    st.markdown("---")
    
    with st.spinner("전체 예측 기록을 불러오는 중입니다..."):
        # 페이지 방문 시 항상 최신 데이터를 가져오도록 ttl을 짧게 설정
        history_data = api_request("GET", "get-history", params={"user_id": st.session_state.user_id}, ttl=10)

    if history_data:
        df = pd.DataFrame(history_data)
        df['prediction_date'] = pd.to_datetime(df['prediction_date']).dt.strftime('%Y-%m-%d')
        
        def format_result(row):
            if not row['is_checked']: return "채점 대기"
            return "✅ 정답" if row['actual_trend'] == row['predicted_trend'] else "❌ 오답"
        
        df['채점 결과'] = df.apply(format_result, axis=1)

        display_df = df[[
            'prediction_date', 'stock_name', 'predicted_trend', 
            'actual_trend', '채점 결과', 'points_awarded'
        ]].rename(columns={
            'prediction_date': '예측일', 'stock_name': '종목명',
            'predicted_trend': '나의 예측', 'actual_trend': '실제 등락',
            'points_awarded': '획득 포인트'
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("아직 참여한 예측 기록이 없습니다.")

# 메인 실행 함수
def predict_stock_page():
    st.title("📊 주가 예측 게임")
    st.markdown("매일 1회, 다음 날 종가를 예측하고 포인트를 얻어보세요!")
    st.markdown("---")
    
    initialize_session_state()

    if st.session_state.page_view == "main":
        show_main_menu()
    elif st.session_state.page_view == "predict":
        show_prediction_game()
    elif st.session_state.page_view == "history":
        show_history_page()
