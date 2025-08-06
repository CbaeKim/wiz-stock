### 서브 콘텐츠 3: 훈장 수집 페이지

import streamlit as st
from datetime import date

def collection_page():
    st.title("📁 수집 콘텐츠 - 훈장 수집 시스템")

    if "my_trophies" not in st.session_state:
        st.session_state.my_trophies = []
    if "daily_point_bonus" not in st.session_state:
        st.session_state.daily_point_bonus = 0
        
    # 트로피 메타 정보
    # 트로피별 이름, 설명, 희귀도, 색상, 포인트 보너스 
    trophies = {
        "quiz_master_7days": {
            "name": "퀴즈 마스터 (7일 연속)",
            "description": "퀴즈를 7일 연속 달성했습니다.",
            "rarity": "레어",
            "color": "#1E90FF", 
            "unique_point_bonus": 0,
            "legend_point_bonus": 0,
        },
        "daily_champion": {
            "name": "데일리 챔피언",
            "description": "하루에 모든 퀴즈를 완료했습니다.",
            "rarity": "노말",
            "color": "#A9A9A9", 
            "unique_point_bonus": 0,
            "legend_point_bonus": 0,
        },
        "unique_learner": {
            "name": "유니크 러너",
            "description": "특별한 학습 성과 달성!",
            "rarity": "유니크",
            "color": "#800080", 
            "unique_point_bonus": 1,
            "legend_point_bonus": 0,
        },
        "legendary_investor": {
            "name": "레전드 투자자",
            "description": "전설적인 투자 지식 보유자!",
            "rarity": "레전드",
            "color": "#FFD700",
            "unique_point_bonus": 0,
            "legend_point_bonus": 2,
        }
    }


    # 트로피 획득 조건
    today = date.today().isoformat()
    points_today = st.session_state.get("study_log", {}).get(today, {}).get("point", 0)
    continuous_days = st.session_state.get("quiz_continuous_days", 0)  # 예: 연속 달성 일 수 저장 필요

    available_trophies = []

    # 조건: 하루 20점 이상 → daily_champion 가능
    if points_today >= 20 and "daily_champion" not in st.session_state.my_trophies:
        available_trophies.append("daily_champion")

    # 조건: 7일 연속 달성 → quiz_master_7days 가능
    if continuous_days >= 7 and "quiz_master_7days" not in st.session_state.my_trophies:
        available_trophies.append("quiz_master_7days")

    # 조건: 하루 50점 이상 → unique_learner 가능
    if points_today >= 50 and "unique_learner" not in st.session_state.my_trophies:
        available_trophies.append("unique_learner")
    
    # 조건: 30일 연속 달성 → unique_learner 가능
    if continuous_days >= 30 and "legendary_investor" not in st.session_state.my_trophies:
        available_trophies.append("legendary_investor")

    st.session_state.available_trophies = available_trophies

    # --- 내 트로피 리스트 출력 ---
    st.subheader("🎖️ 내 트로피 리스트")

    if st.session_state.my_trophies:
        for trophy_key in st.session_state.my_trophies:
            trophy = trophies[trophy_key]
            st.markdown(f"""
                <div style="border:1px solid #ddd; padding:10px; margin-bottom:5px; border-radius:5px; background-color:#f9f9f9;">
                    <strong style="color:{trophy['color']}; font-size:18px;">{trophy['name']} ({trophy['rarity']})</strong><br>
                    <small>{trophy['description']}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("아직 획득한 트로피가 없습니다. 퀴즈를 열심히 풀어보세요!")

    st.markdown("---")

    # --- 획득 가능한 트로피 리스트 ---
    st.subheader("🏆 획득 가능한 트로피")

    if available_trophies:
        for trophy_key in available_trophies:
            trophy = trophies[trophy_key]

            st.markdown(f"""
                <div style="border:2px dashed #007acc; padding:10px; margin-bottom:10px; border-radius:5px;">
                    <strong style="color:{trophy['color']}; font-size:18px;">{trophy['name']} ({trophy['rarity']})</strong><br>
                    <small>{trophy['description']}</small>
                </div>
            """, unsafe_allow_html=True)
            
            # 트로피 획득 버튼 생성
            if st.button(f"🏅 '{trophy['name']}' 획득하기", key=f"get_{trophy_key}"):
                st.session_state.my_trophies.append(trophy_key)
                st.success(f"'{trophy['name']}' 트로피를 획득했습니다! 🎉")

                # 획득한 훈장 등급에 따라 닉네임 색상 및 일일 포인트 보너스 설정
                if trophy["rarity"] == "유니크":
                    st.session_state.nickname_color = trophy["color"]
                    st.session_state.daily_point_bonus += trophy["unique_point_bonus"]
                    st.info("유니크 등급 획득! 닉네임 색상이 변경되고, 일 1포인트 추가 보너스를 받습니다.")
                elif trophy["rarity"] == "레전드":
                    st.session_state.nickname_color = trophy["color"]
                    st.session_state.daily_point_bonus += trophy["legend_point_bonus"]
                    st.info("레전드 등급 획득! 닉네임 색상이 변경되고, 일 2포인트 추가 보너스를 받습니다.")

                # 획득 가능한 리스트에서 제거하고 페이지를 다시 로드하여 변경사항 적용
                st.session_state.available_trophies.remove(trophy_key)
                st.rerun()
    else:
        st.write("현재 획득 가능한 트로피가 없습니다.")

    # --- 닉네임 색상 출력 ---
    st.markdown("---")
    st.subheader("👤 닉네임")

    user_name = st.session_state.get("nickname", "익명")
    color = st.session_state.get("nickname_color", None)

    # 닉네임 색상이 설정된 경우에만 스타일 적용
    if color:
        style_tag = f'style="color:{color};"'
    else:
        style_tag = ""
    
    st.markdown(f'<span {style_tag}>{user_name}</span>', unsafe_allow_html=True)

    # --- 일일 추가 포인트 보너스 표시 ---
    st.markdown("---")
    st.write(f"💡 일일 추가 포인트 보너스: **{st.session_state.daily_point_bonus}점**")
