import streamlit as st
from datetime import date, datetime # 💡 datetime 추가
import pandas as pd
import random
from supabase import create_client, Client
import os
from postgrest import APIError
from utils.ranking import update_user_points # 이 함수는 이제 사용되지 않으므로 나중에 삭제해도 됩니다.

os.environ['PYTHONUTF8'] = '1'

# Supabase 연결 정보
SUPABASE_URL = 'https://yhayrbotkkuuvoxzhqct.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InloYXlyYm90a2t1dXZveHpocWN0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzkyMjg4MiwiZXhwIjoyMDY5NDk4ODgyfQ.qCr4MtbP3Ztgz75McZ7onQnr1D3cMm-CdkmwJ722ieY'

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase 클라이언트 생성 중 치명적인 오류가 발생했습니다: {e}")
    st.stop()

# 포인트 업데이트와 로그 기록을 한 번에 처리하는 함수 
def update_points_and_log(user_id: str, points_to_add: int, topic: str):
    """
    사용자의 총 포인트를 업데이트하고, 포인트 획득 기록을 point_log 테이블에 추가합니다.
    """
    try:
        # user_info 테이블의 total_point 업데이트
        # 현재 사용자의 total_point 가져오기
        response = supabase.table('user_info').select('total_point').eq('id', user_id).single().execute()
        current_points = response.data['total_point'] if response.data and response.data.get('total_point') is not None else 0
        
        # 새로운 total_point 계산 및 업데이트
        new_total_points = current_points + points_to_add
        supabase.table('user_info').update({'total_point': new_total_points}).eq('id', user_id).execute()

        # point_log 테이블에 기록 추가
        log_data = {
            "category": topic,
            "point_value": points_to_add,
            "path": "주식 퀴즈",
            "timestamp": datetime.now().isoformat(),
            "ip_address": "not_available" # Streamlit에서 IP 주소를 직접 얻기는 어렵습니다.
        }
        supabase.table('point_log').insert(log_data).execute()
        
        # user_id도 로그에 남기려면 point_log 테이블에 user_id 컬럼을 추가하고 아래 주석을 해제하세요.
        # log_data['user_id'] = user_id 

        print(f"✅ 포인트 업데이트 및 로그 기록 성공: User {user_id}, +{points_to_add}점")

    except Exception as e:
        st.error(f"포인트 처리 중 오류가 발생했습니다: {e}")
        print(f"❌ 포인트 처리 중 오류 발생: {e}")


@st.cache_data(ttl=600)
def fetch_all_quiz_data():
    """'quiz' 테이블에서 모든 데이터를 가져와 Pandas DataFrame으로 변환합니다."""
    try:
        response = supabase.table('quiz').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            st.warning("데이터베이스의 'quiz' 테이블이 비어있습니다.")
            return pd.DataFrame()
    except APIError as e:
        st.error(f"데이터베이스 조회 오류: {e.message}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터를 처리하는 중 예상치 못한 오류가 발생했습니다: {e}")
        return pd.DataFrame()

def main_content():
    st.title("📘 주식 기초 학습")

    if "last_answer_result" not in st.session_state:
        st.session_state.last_answer_result = None
    today = date.today().isoformat()
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None, "step": "select_topic", "quiz_data": pd.DataFrame(),
            "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False
        }
    log = st.session_state.study_log[today]

    total_quiz_data = fetch_all_quiz_data()

    if total_quiz_data is None or total_quiz_data.empty:
        return

    # 결과 표시 부분
    if log["step"] == "result":
        st.subheader("📚 오늘 공부할 주제를 선택하세요 (1일 1회)")
        st.success(f"오늘의 퀴즈는 이미 완료되었습니다! ✅")
        st.markdown(f"**선택한 주제:** **[{log['topic']}]**")
        st.markdown(f"**오늘 획득한 점수:** {log['point']}점")
        
        topic_options = ["기초지식", "기술적 지표", "재무제표"]
        try:
            selected_index = topic_options.index(log["topic"])
        except ValueError:
            selected_index = 0
        
        st.radio("학습 주제 선택", topic_options, disabled=True, index=selected_index)
        
        st.markdown("---")
        st.info(f"오늘은 주식 퀴즈 중 **[{log['topic']}]**에 대해 학습해보았습니다. 내일은 또 다른 주제로 도전해 보세요!")

        if st.button("메인으로 돌아가기"):
            st.session_state.page = "메인"
            st.session_state.last_answer_result = None
            st.rerun()
        return

    # 1단계: 주제 선택 (기존과 동일)
    if log["step"] == "select_topic":
        st.subheader("📚 오늘 공부할 주제를 선택하세요 (1일 1회)")
        
        topic_options = ["기초지식", "기술적 지표", "재무제표"]

        if log["topic"] is not None:
            st.radio("학습 주제 선택", topic_options, disabled=True, index=topic_options.index(log["topic"]))
            st.warning(f"이미 오늘의 주제: **[{log['topic']}]**를 선택했습니다. 퀴즈를 계속 진행해주세요.")
            if st.button("계속 진행하기"):
                log["step"] = "quiz" if log["quiz_index"] < len(log["quiz_data"]) else "result"
                st.rerun()
        else:
            topic = st.radio("학습 주제 선택", topic_options, key="topic_choice")
            if st.button("선택 완료"):
                log["topic"] = topic
                
                filtered_quizzes = total_quiz_data[total_quiz_data['sub_category'] == topic]

                if not filtered_quizzes.empty:
                    num_questions = min(3, len(filtered_quizzes))
                    log["quiz_data"] = filtered_quizzes.sample(num_questions)
                else:
                    st.error(f"선택된 주제 '{topic}'에 해당하는 퀴즈 데이터가 없습니다. Supabase의 'sub_category' 컬럼을 확인해주세요.")
                    log["topic"] = None 
                    return

                log["step"] = "quiz"
                st.rerun()

    # 2단계: OX 퀴즈 진행
    elif log["step"] == "quiz":
        index = log["quiz_index"]
        if index < len(log["quiz_data"]):
            question = log["quiz_data"].iloc[index]["question"]
            correct_answer = log["quiz_data"].iloc[index]["answer"]
            explanation = log["quiz_data"].iloc[index]["explanation"]

            st.subheader(f"문제 {index+1}/{len(log['quiz_data'])}")
            st.write(f"Q. {question}")
            user_answer = st.radio("당신의 선택은?", ["O", "X"], key=f"q_{index}")

            if st.session_state.last_answer_result is None:
                if st.button("제출", key=f"submit_{index}"):
                    
                    # --- 💡 2. 새로 만든 함수를 호출하여 포인트 처리 ---
                    points_to_add = 0
                    if user_answer == correct_answer:
                        st.session_state.last_answer_result = "correct"
                        points_to_add = 5
                    else:
                        st.session_state.last_answer_result = "wrong"
                        points_to_add = 2
                    
                    # 포인트 업데이트 및 로그 기록 함수 호출
                    update_points_and_log(
                        user_id=st.session_state.user_id, 
                        points_to_add=points_to_add, 
                        topic=log['topic']
                    )
                    
                    # 오늘의 획득 점수(세션) 업데이트
                    log["point"] += points_to_add
                    st.rerun()
            else:
                if st.session_state.last_answer_result == "correct":
                    st.success("정답입니다! 🎉 +5점")
                else:
                    st.warning("오답입니다. 😅 +2점")
                st.markdown(f"**해설:** {explanation}")

                if st.button("다음 문제"):
                    st.session_state.last_answer_result = None
                    log["quiz_index"] += 1
                    if log["quiz_index"] >= len(log["quiz_data"]):
                        log["step"] = "result"
                    st.rerun()
        else:
            log["step"] = "result"
            st.rerun()
