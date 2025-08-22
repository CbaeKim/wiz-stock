# wiz-stock/app/pages/predict_stock.py
import streamlit as st
import requests
import pandas as pd
import traceback
from datetime import date

# FastAPI 백엔드 API URL 설정
API_BASE_URL = "http://localhost:8000/stock-predict"

# --- API 호출 함수들 ---
@st.cache_data(ttl=60)
def check_participation_status(user_id: str):
    """
    API를 통해 사용자의 주가 예측 게임 참여 가능 여부를 확인
    """
    try:
        response = requests.get(f"{API_BASE_URL}/check-participation", params={"user_id": user_id})
        response.raise_for_status()
        
        api_response = response.json()
        if not isinstance(api_response, dict):
            st.error("API 응답 형식이 올바르지 않습니다.")
            return False
            
        return api_response.get("can_participate", False)
    except requests.exceptions.RequestException as e:
        st.error(f"참여 상태 확인 중 오류 발생: {e}")
        return False
    except Exception as e:
        st.error(f"예기치 않은 오류가 발생했습니다: {e}")
        return False

@st.cache_data(ttl=3600)
def get_top10_stocks():
    """
    API를 통해 최신 시가총액 상위 10개 종목 목록을 가져옴
    """
    try:
        response = requests.get(f"{API_BASE_URL}/get-top10")
        response.raise_for_status()
        
        api_response = response.json()
        if not isinstance(api_response, list):
            st.error("종목 목록 API 응답 형식이 올바르지 않습니다.")
            return []
            
        return api_response
    except requests.exceptions.RequestException as e:
        st.error(f"종목 데이터를 불러오는 데 실패했습니다: {e}")
        return []
    except Exception as e:
        st.error(f"예기치 않은 오류가 발생했습니다: {e}")
        return []

@st.cache_data(ttl=3600)
def get_stock_info_from_api(stock_code: str):
    """
    API를 통해 특정 종목의 예측 및 감성 분석 정보를 가져옴
    """
    try:
        response = requests.get(f"{API_BASE_URL}/get-stock-info", params={"stock_code": stock_code})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"종목 정보를 불러오는 데 실패했습니다: {e}")
        return None
    except Exception as e:
        st.error(f"예기치 않은 오류가 발생했습니다: {e}")
        return None

def submit_prediction_to_api(user_id: str, stock_code: str, user_predict_trend: str):
    """
    API를 통해 사용자의 주가 예측 선택을 제출
    """
    payload = {
        "user_id": user_id,
        "stock_code": stock_code,
        "user_predict_trend": user_predict_trend
    }
    try:
        response = requests.post(f"{API_BASE_URL}/submit-prediction", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"예측 제출 중 오류가 발생했습니다: {e}")
        return None

# UI 메인 함수 
def predict_stock_page():
    st.title("📊 주가 예측 게임")
    st.markdown("매일 1회, 다음 날 종가를 예측하고 포인트를 얻어보세요!")
    st.markdown("---")
    
    # 임시 사용자 ID 설정
    if "user_id" not in st.session_state:
        st.session_state.user_id = "test_user_001"
        st.warning("사용자 ID가 없어 임시로 'test_user_001'로 설정했습니다. 실제 앱에서는 로그인 시스템을 구현해야 합니다.")
    
    user_id = st.session_state.user_id

    game_state = st.session_state.game_state

    # --- UI 분기 처리 ---

    # 참여 가능 여부 확인 단계 (최초 진입 시 또는 새로고침 시)
    if game_state["step"] == "initial":
        with st.spinner("참여 가능 여부를 확인하는 중입니다..."):
            can_participate = check_participation_status(user_id)
        
        game_state["can_participate"] = can_participate
        
        if can_participate:
            game_state["step"] = "select_stock"
            st.rerun()
        else:
            game_state["step"] = "already_participated"
            st.rerun()

    # 이미 참여한 경우
    elif game_state["step"] == "already_participated":
        st.info("오늘의 예측은 이미 완료했어요. 내일 결과를 확인해보세요!")

    # 종목 선택 및 예측 단계
    elif game_state["step"] == "select_stock":
        st.subheader("🕵️ 오늘의 예측")
        st.info("아직 오늘의 예측을 하지 않았습니다. 아래에서 종목을 선택하세요.")

        with st.spinner("종목 목록을 불러오는 중입니다..."):
            top10_stocks = get_top10_stocks()

        if not top10_stocks:
            st.warning("종목 목록을 불러올 수 없습니다. 데이터 파이프라인을 확인해주세요.")
            return

        stock_map = {item['stock_name']: item['stock_code'] for item in top10_stocks}
        selected_stock_name = st.selectbox("종목을 선택하세요", list(stock_map.keys()), key="stock_select")
        
        # 종목이 선택되면 상세 정보를 불러오도록 트리거
        if selected_stock_name:
            selected_stock_code = stock_map[selected_stock_name]
            stock_info = get_stock_info_from_api(selected_stock_code)
            
            if stock_info:
                st.markdown(f"**현재가: {stock_info['current_price']}원**")
                
                with st.expander("AI 모델 분석 결과 보기"):
                    st.markdown(f"""
                    - 다음날 예측 등락: **{stock_info['trend_predict']}**
                    - 다음날 예측 종가: **{stock_info['price_predict']}**원
                    - 가장 영향력 있는 지표: **{stock_info['top_feature']}**
                    - 감성 분석 전망: **{stock_info['sentiment_outlook']}**
                    """)
                
                user_prediction = st.radio("예측 방향 선택", ("상승", "하락"), key="user_predict_radio")

                if st.button("예측 완료", key="submit_button"):
                    submit_result = submit_prediction_to_api(
                        user_id=user_id,
                        stock_code=selected_stock_code,
                        user_predict_trend=user_prediction
                    )
                    if submit_result:
                        st.success("✅ 예측이 성공적으로 제출되었습니다! 내일 결과를 확인하세요.")
                        game_state["step"] = "prediction_submitted"
                        st.rerun()
                        
    # 예측 제출 완료 단계 (리로드 후에도 상태 유지)
    elif game_state["step"] == "prediction_submitted":
        st.success("오늘의 예측이 이미 완료되었습니다. 내일 결과를 확인하세요!")
    
    st.markdown("---")
    st.markdown("""
    ### 📝 결과 확인에 대한 참고 사항
    * **결과 확인**: 예측 결과는 다음 날 시장 마감 후 확정됩니다. 현재 포인트 및 어제 예측 결과 확인 기능은 추후 추가될 예정입니다.
    * **포인트 부여**: 정답/오답 판별 및 포인트 부여는 백엔드에서 별도의 스케줄링 작업을 통해 처리됩니다.
    """)
