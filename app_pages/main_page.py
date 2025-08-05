### 주식 기초 학습 페이지(메인)

import streamlit as st
from datetime import date
import pandas as pd
import random
from utils.ranking import update_user_points 

def main_content():
    st.title("📘 주식 기초 학습")

    if "last_answer_result" not in st.session_state:
        st.session_state.last_answer_result = None

    today = date.today().isoformat()

    if "study_log" not in st.session_state:
        st.session_state.study_log = {}

    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None,
            "step": "select_topic",
            "quiz_data": pd.DataFrame(),
            "quiz_index": 0,
            "point": 0,
            "balloons_shown_for_quest": False
        }

    log = st.session_state.study_log[today]

    # --- CSV 파일에서 퀴즈 데이터 로드 ---
    try:
        total_quiz_data = pd.read_csv('C:\\Users\\jah96\\AppData\\Local\\project\\KDT\\total_data.csv')
    except FileNotFoundError:
        st.error("퀴즈 데이터 파일을 찾을 수 없습니다. 'total_data.csv' 파일이 올바른 경로에 있는지 확인해주세요.")
        return

    # --- 오늘의 퀴즈 완료 여부 확인 및 처리 ---
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
        
        # 퀴즈 완료 시 라디오 버튼을 비활성화 상태로 표시
        st.radio("학습 주제 선택", topic_options, disabled=True, index=selected_index)
        
        # 최종 결과 안내 메시지 표시
        st.markdown("---")
        if st.session_state.selected_sub_category:
            st.info(f"오늘은 주식 퀴즈 중 **[{log['topic']}]**의 세부 개념인 **[{st.session_state.selected_sub_category}]**에 대해 학습해보았습니다. 내일은 또 다른 주제로 도전해 보세요!")
        else:
            st.info(f"오늘은 주식 퀴즈 중 **[{log['topic']}]**에 대해 학습해보았습니다. 내일은 또 다른 주제로 도전해 보세요!")

        # 메인으로 돌아가기 버튼
        if st.button("메인으로 돌아가기"):
            st.session_state.page = "메인"
            st.session_state.last_answer_result = None
            st.rerun()
            
        return

    # --------------------------
    # 1단계: 주제 선택 (퀴즈 완료되지 않았을 때만 실행)
    if log["step"] == "select_topic":
        st.subheader("📚 오늘 공부할 주제를 선택하세요 (1일 1회)")
        topic_options = ["기초지식", "기술적 지표", "재무제표"]

        if log["topic"] is not None:
            st.radio("학습 주제 선택", topic_options, disabled=True, index=topic_options.index(log["topic"]))
            st.warning(f"이미 오늘의 주제: **[{log['topic']}]**를 선택했습니다. 퀴즈를 계속 진행해주세요.")
            if st.button("계속 진행하기"):
                if log["quiz_index"] < len(log["quiz_data"]):
                    log["step"] = "quiz"
                else:
                    log["step"] = "result"
                st.rerun()
        else:
            topic = st.radio("학습 주제 선택", topic_options, key="topic_choice")
            if st.button("선택 완료"):
                log["topic"] = topic

                category_map = {
                    "기초지식": "basic",
                    "기술적 지표": "technical",
                    "재무제표": "financial"
                }

                selected_category = category_map.get(topic)
                if selected_category:
                    # 1. 선택된 카테고리에 해당하는 모든 데이터 필터링
                    filtered_by_category = total_quiz_data[total_quiz_data['category'] == selected_category]

                    if not filtered_by_category.empty:
                        # 2. 필터링된 데이터에서 랜덤으로 sub_category 선택
                        random_sub_category = random.choice(filtered_by_category['sub_category'].unique())

                        # 3. 선택된 sub_category에 해당하는 문제들만 다시 필터링
                        filtered_by_subcategory = filtered_by_category[filtered_by_category['sub_category'] == random_sub_category]

                        if not filtered_by_subcategory.empty:
                            # 4. 필터링된 문제들 중 3개를 무작위로 선택
                            num_questions = min(3, len(filtered_by_subcategory))
                            log["quiz_data"] = filtered_by_subcategory.sample(num_questions)

                            # 지식 설명에 사용할 sub_category 저장
                            st.session_state.selected_sub_category = random_sub_category
                        else:
                             st.error("선택된 주제의 세부 카테고리에 해당하는 퀴즈 데이터가 충분하지 않습니다.")
                             log["topic"] = None # 재선택 가능하게 초기화
                             return
                    else:
                        st.error("선택된 주제에 해당하는 퀴즈 데이터가 없습니다.")
                        log["topic"] = None # 재선택 가능하게 초기화
                        return

                log["step"] = "show_knowledge"
                st.rerun()

    # --------------------------
    # 2단계: 지식 설명 (퀴즈 완료되지 않았을 때만 실행)
    elif log["step"] == "show_knowledge":
        st.subheader(f"📖 [{st.session_state.selected_sub_category}] 기본 개념")
        if not log["quiz_data"].empty:
            st.info(log["quiz_data"].iloc[0]["explanation"])
        else:
            st.info("선택된 주제에 대한 개념 설명이 없습니다.")

        if st.button("다음 → OX 퀴즈"):
            log["step"] = "quiz"
            st.rerun()

    # --------------------------
    # 3단계: OX 퀴즈 진행 (퀴즈 완료되지 않았을 때만 실행)
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
                    if user_answer == correct_answer:
                        st.session_state.last_answer_result = "correct"
                        update_user_points(st.session_state.user_id, 5)
                        log["point"] += 5
                    else:
                        st.session_state.last_answer_result = "wrong"
                        update_user_points(st.session_state.user_id, 2)
                        log["point"] += 2
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
