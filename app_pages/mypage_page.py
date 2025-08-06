### 서브 콘텐츠 7: 마이페이지

import streamlit as st

def mypage_content():
    st.title("👤 마이페이지")
    st.subheader("내 정보")

    if "user_id" not in st.session_state:
        st.session_state.user_id = "익명 사용자"
    if "points" not in st.session_state:
        st.session_state.points = 0
    if "nickname" not in st.session_state:
        st.session_state.nickname = "익명"
    if "daily_point_bonus" not in st.session_state:
        st.session_state.daily_point_bonus = 0
    if "my_trophies" not in st.session_state:
        st.session_state.my_trophies = []
    if "purchased_indicators" not in st.session_state:
        st.session_state.purchased_indicators = []

    user_id = st.session_state.user_id
    total_points = st.session_state.points
    nickname = st.session_state.nickname
    nickname_color = st.session_state.get("nickname_color", None)
    daily_bonus = st.session_state.daily_point_bonus
    my_trophies = st.session_state.my_trophies
    purchased_indicators = st.session_state.purchased_indicators

    # nickname_color가 있을 경우에만 color 스타일을 적용
    if nickname_color:
        nickname_style_tag = f'style="color:{nickname_color};"'
    else:
        nickname_style_tag = ""

    st.markdown(f"**닉네임:** <span {nickname_style_tag}>{nickname}</span>", unsafe_allow_html=True)
    st.markdown(f"**아이디:** {user_id}")
    st.markdown(f"**총 보유 포인트:** {total_points}점")
    st.markdown(f"**일일 추가 포인트 보너스:** {daily_bonus}점")

    st.subheader("획득한 훈장")
    if my_trophies:
        trophies_meta = {
            "quiz_master_7days": {"name": "퀴즈 마스터 (7일 연속)", "rarity": "레어", "color": "#1E90FF"},
            "daily_champion": {"name": "데일리 챔피언", "rarity": "노말", "color": "#A9A9A9"},
            "unique_learner": {"name": "유니크 러너", "rarity": "유니크", "color": "#800080"},
            "legendary_investor": {"name": "레전드 투자자", "rarity": "레전드", "color": "#FFD700"}
        }
        for trophy_key in my_trophies:
            trophy = trophies_meta.get(trophy_key, {"name": "알 수 없는 훈장", "rarity": "", "color": "#000000"})
            st.markdown(f"""
                <div style="border:1px solid #ddd; padding:8px; margin-bottom:4px; border-radius:4px; background-color:#f0f8ff;">
                    <strong style="color:{trophy['color']};">{trophy['name']} ({trophy['rarity']})</strong>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("아직 획득한 훈장이 없습니다.")

    st.subheader("구매한 보조지표")
    if purchased_indicators:
        for indicator in purchased_indicators:
            st.markdown(f"- {indicator}")
    else:
        st.write("아직 구매한 보조지표가 없습니다. '보조지표 상점' 페이지에서 구매할 수 있습니다. ")
