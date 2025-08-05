### 서브 콘텐츠 4: 보조지표 상점 페이지

import streamlit as st
import pandas as pd
import random 
from datetime import date

def indicator_page():
    st.title("📊 보조지표")

    # 지표 확인 여부 상태 관리
    if "indicator_access" not in st.session_state:
        st.session_state.indicator_access = False
    
    # 오늘의 퀘스트 포인트 업데이트
    today = date.today().isoformat()
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None, "step": "select_topic", "quiz_data": [],
            "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False
        }
    log = st.session_state.study_log[today]

    # 이미 확인했는지 여부
    if not st.session_state.indicator_access:
        st.markdown("### ⚠️ 보조지표를 확인하시겠습니까?")
        st.markdown("🔑 확인 시 포인트 2점이 차감됩니다.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes (2점 차감)"):
                if st.session_state.points >= 2 and log["point"] >= 2:
                    st.session_state.points -= 2
                    log["point"] -= 2
                    st.session_state.indicator_access = True
                    st.success("2포인트가 차감되었습니다.")
                    st.rerun()
                else:
                    st.error("포인트가 부족합니다.")
        with col2:
            if st.button("❌ No"):
                st.session_state.indicator_access = None
                st.info("보조지표 확인이 취소되었습니다.")
                st.rerun()

    elif st.session_state.indicator_access == True:
        st.success("보조지표를 확인할 수 있습니다!")

        # 여기에 원하는 보조지표 예시 표시
        st.subheader("📈 예시 보조지표: 이동평균선")
        sample_data = pd.DataFrame({
            "날짜": pd.date_range(start="2024-01-01", periods=30),
            "종가": [random.randint(90, 110) for _ in range(30)]
        })
        sample_data["5일 이동평균"] = sample_data["종가"].rolling(window=5).mean()
        st.line_chart(sample_data.set_index("날짜")[["종가", "5일 이동평균"]])

    st.markdown(f"현재 포인트: **{st.session_state.points}점")

