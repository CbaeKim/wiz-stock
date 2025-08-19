# app_pages/main_page.py

import streamlit as st
from datetime import date
import pandas as pd
import requests

# --- 설정 ---
API_BASE_URL = "http://127.0.0.1:8000/quiz"

# --- API 호출 함수들 ---
@st.cache_data(ttl=600) # 10분(600초) 동안 API 응답을 캐싱합니다.
def get_quizzes_from_api(topic: str):
    """
    FastAPI 서버에 GET 요청을 보내 특정 주제의 퀴즈 데이터를 가져옵니다.
    - topic: '기초지식', '기술적 지표' 등 사용자가 선택한 주제
    - st.cache_data: 동일한 주제로 반복 요청 시, 캐시된 데이터를 사용하여 API 호출을 줄입니다.
    """
    try:
        # GET 요청을 보낼 URL과 파라미터를 지정합니다.
        response = requests.get(f"{API_BASE_URL}/get-by-topic", params={"topic": topic})
        response.raise_for_status()  # 200번대 상태 코드가 아니면 에러를 발생시킵니다.
        # 성공적으로 받아온 JSON 데이터를 Pandas DataFrame으로 변환하여 반환합니다.
        return pd.DataFrame(response.json())
    except requests.exceptions.RequestException as e:
        # API 호출 실패 시 사용자에게 에러 메시지를 보여줍니다.
        st.error(f"퀴즈 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60) # 1분마다 참여 가능 여부를 다시 확인
def check_participation_status(user_id: str):
    """
    API를 통해 사용자의 퀴즈 참여 가능 여부를 확인합니다.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/check-participation", params={"user_id": user_id})
        response.raise_for_status()
        # API 응답에서 "can_participate" 키의 값을 가져옵니다. 없으면 False를 기본값으로 사용합니다.
        return response.json().get("can_participate", False)
    except requests.exceptions.RequestException as e:
        st.error(f"참여 상태 확인 중 오류 발생: {e}")
        return False

def submit_answer_to_api(user_id: str, quiz_id: int, user_answer: str, topic: str, quiz_index: int, total_questions: int):
    """
    FastAPI 서버에 POST 요청을 보내 사용자의 답변을 제출하고 채점 결과를 받습니다.
    """
    # 서버로 보낼 데이터를 딕셔너리 형태로 정의합니다.
    payload = {
        "user_id": user_id, "quiz_id": quiz_id,
        "user_answer": user_answer, "topic": topic,
        "quiz_index": quiz_index, "total_questions": total_questions
    }
    try:
        # POST 요청을 보낼 URL과 JSON 데이터를 지정합니다.
        response = requests.post(f"{API_BASE_URL}/submit-answer", json=payload)
        response.raise_for_status()
        # 성공적으로 받아온 JSON 형태의 채점 결과를 반환합니다.
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"답변 제출 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit UI 메인 함수 ---
def main_content():
    st.title("📘 오늘의 주식 퀴즈")
    st.markdown("매일 새로운 퀴즈를 풀고 포인트를 얻어보세요!")
    st.markdown("---")

    # --- 참여 가능 여부 확인 ---
    # 로그인 시 st.session_state에 저장된 사용자 ID를 가져옵니다.
    user_id = st.session_state.get("user_id", None)
    if not user_id:
        st.warning("퀴즈를 풀려면 먼저 로그인을 해주세요.")
        return

    # API를 호출하여 오늘 퀴즈를 풀 수 있는지 확인합니다.
    can_participate = check_participation_status(user_id)

    # --- 세션 상태(Session State) 관리 ---
    today = date.today().isoformat()
    if "quiz_log" not in st.session_state:
        st.session_state.quiz_log = {}
    
    # 오늘 날짜에 대한 기록이 없으면 새로 생성하여, 하루에 한 번만 퀴즈를 풀도록 합니다.
    if today not in st.session_state.quiz_log:
        st.session_state.quiz_log[today] = {
            "step": "select_topic", "topic": None, "quiz_data": pd.DataFrame(),
            "quiz_index": 0, "total_points": 0, "last_answer_result": None
        }
    
    log = st.session_state.quiz_log[today]

    # --- UI 분기 처리 ---

    # 참여가 불가능하고, 아직 퀴즈 결과 단계가 아닐 때 메시지를 표시합니다.
    if not can_participate and log["step"] != "result":
        st.success("오늘의 퀴즈에 이미 참여하셨습니다! 🎉")
        st.info("내일 새로운 퀴즈에 다시 도전해보세요.")
        st.subheader("📚 오늘 공부할 주제를 선택하세요 (1일 1회)")
        st.radio("학습 주제 선택", ["기초지식", "기술적 지표", "재무제표"], disabled=True)
        return

    # 1. 결과 화면
    if log["step"] == "result":
        st.success("오늘의 퀴즈를 모두 완료했습니다! 🎉")
        st.balloons()
        st.subheader(f"주제: [{log['topic']}]")
        st.metric("오늘 획득한 총 포인트", f"{log['total_points']} 점")
        st.info("내일 새로운 퀴즈에 다시 도전해보세요!")
        return

    # 2. 주제 선택 화면
    if log["step"] == "select_topic":
        st.subheader("📚 오늘 공부할 주제를 선택하세요 (1일 1회)")
        topic = st.radio("학습 주제 선택", ["기초지식", "기술적 지표", "재무제표"], horizontal=True)
        if st.button("퀴즈 시작하기", type="primary"):
            with st.spinner("퀴즈를 불러오는 중입니다..."):
                quiz_df = get_quizzes_from_api(topic)
            if not quiz_df.empty:
                log.update({"topic": topic, "quiz_data": quiz_df, "step": "quiz"})
                st.rerun() # 페이지를 새로고침하여 퀴즈 단계로 넘어갑니다.

    # 3. 퀴즈 진행 화면
    elif log["step"] == "quiz":
        index = log["quiz_index"]
        if index < len(log["quiz_data"]):
            quiz_item = log["quiz_data"].iloc[index]
            st.subheader(f"퀴즈 {index + 1} / {len(log['quiz_data'])}")
            st.markdown(f"#### Q. {quiz_item['question']}")

            # 직전 문제의 결과가 있으면 정답/오답 피드백과 해설을 보여줍니다.
            if log['last_answer_result']:
                feedback = "정답입니다! 👍" if log['last_answer_result'] == "correct" else "오답입니다. 👎"
                st.success(feedback) if log['last_answer_result'] == "correct" else st.warning(feedback)
                st.info(f"**해설:** {quiz_item['explanation']}")
                if st.button("다음 문제로", key=f"next_{index}"):
                    log.update({"last_answer_result": None, "quiz_index": index + 1})
                    st.rerun()
            else:
                # O/X 선택 버튼을 표시합니다.
                cols = st.columns(2)
                user_answer = None
                if cols[0].button("O", use_container_width=True): user_answer = "O"
                if cols[1].button("X", use_container_width=True): user_answer = "X"
                
                # 사용자가 버튼을 클릭하면 API로 답변을 제출합니다.
                if user_answer:
                    with st.spinner("채점 중..."):
                        result = submit_answer_to_api(
                            user_id=user_id,
                            quiz_id=int(quiz_item['identify_code']),
                            user_answer=user_answer,
                            topic=log['topic'],
                            quiz_index=index,
                            total_questions=len(log['quiz_data'])
                        )
                    if result:
                        # 채점 결과를 세션에 저장하고 페이지를 새로고침하여 피드백을 보여줍니다.
                        log.update({
                            "last_answer_result": "correct" if result["is_correct"] else "wrong",
                            "total_points": log["total_points"] + result["points_awarded"]
                        })
                        st.rerun()
        else:
            # 모든 퀴즈를 다 풀었으면 결과 화면으로 이동합니다.
            log["step"] = "result"
            st.rerun()