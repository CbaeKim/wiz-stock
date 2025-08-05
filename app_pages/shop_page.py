### 서브 콘텐츠 5: 포인트 상점

import streamlit as st
from datetime import date, datetime
import random
import time


# ---------------------------
# 숫자 맞추기 게임
def number_guessing_game():
    st.subheader("숫자 맞추기 게임")
    st.write("1부터 100 사이의 숫자를 5번 안에 맞춰보세요! 정답 시 10 포인트 획득!")

    if st.session_state.get("game_reset", True):
        st.session_state.secret_number = random.randint(1, 100)
        st.session_state.guesses = 0
        st.session_state.game_message = "새로운 게임이 시작되었습니다. 숫자를 맞춰보세요!"
        st.session_state.game_reset = False
        st.session_state.game_over = False
        st.session_state.game_cooldown_start_time = None

    # 쿨다운 확인
    game_cooldown_active = False
    remaining_game_cooldown_time = 0
    if st.session_state.get("game_cooldown_start_time"):
        current_time = datetime.now()
        elapsed_time = (current_time - st.session_state.game_cooldown_start_time).total_seconds()
        if elapsed_time < 60: # 60초 쿨다운
            game_cooldown_active = True
            remaining_game_cooldown_time = 60 - elapsed_time

    if game_cooldown_active:
        st.warning(f"게임 재도전까지 **{int(remaining_game_cooldown_time)}초** 남았습니다.")
        st.number_input("숫자를 입력하세요 (1-100)", min_value=1, max_value=100, value=50, key="number_guess_disabled", disabled=True)
        st.button("제출", key="submit_guess_disabled", disabled=True)
    elif st.session_state.game_over:
        st.error("이번 게임은 실패했어요. 60초 후에 다시 도전할 수 있습니다.")
        if st.button("새 게임 시작", key="new_game_button_after_fail"):
            st.session_state.game_reset = True
            st.rerun()
    else:
        guess = st.number_input("숫자를 입력하세요 (1-100)", min_value=1, max_value=100, value=50, key="number_guess")
        
        if st.button("제출", key="submit_guess"):
            st.session_state.guesses += 1
            if guess < st.session_state.secret_number:
                st.session_state.game_message = "더 높은 숫자입니다!"
            elif guess > st.session_state.secret_number:
                st.session_state.game_message = "더 낮은 숫자입니다!"
            else:
                st.session_state.game_message = f"정답입니다! 🎉 {st.session_state.guesses}번 만에 맞췄어요! +10점"
                st.session_state.points += 10
                # 오늘의 퀘스트 포인트 업데이트
                today = date.today().isoformat()
                if today in st.session_state.study_log:
                    st.session_state.study_log[today]["point"] = st.session_state.study_log[today].get("point", 0) + 10
                st.balloons()
                st.session_state.game_reset = True
                st.session_state.game_over = True
            
            if st.session_state.guesses >= 5 and guess != st.session_state.secret_number:
                st.session_state.game_message = f"아쉽네요! 5번의 기회를 모두 소진했습니다. 정답은 {st.session_state.secret_number}였습니다. 60초 후에 다시 도전해주세요."
                st.session_state.game_over = True
                st.session_state.game_cooldown_start_time = datetime.now()
            st.rerun()

        st.info(st.session_state.game_message)
        st.write(f"시도 횟수: {st.session_state.guesses}/5")
        
        if st.session_state.get("game_reset", False) and not st.session_state.game_over and st.button("새 게임 시작", key="new_game_button_after_win"):
            st.session_state.game_reset = True
            st.rerun()

# ---------------------------
# 광고 보고 포인트 적립
def ad_watching_reward():
    st.subheader("30초 광고 보고 포인트 적립")
    st.write("30초 광고를 시청하고 5포인트를 획득하세요.")

    COOLDOWN_SECONDS = 60
    can_watch_ad = True
    remaining_time = 0
    if st.session_state.get("last_ad_watch_time"):
        current_time = datetime.now()
        elapsed_time = (current_time - st.session_state.last_ad_watch_time).total_seconds()
        if elapsed_time < COOLDOWN_SECONDS:
            can_watch_ad = False
            remaining_time = COOLDOWN_SECONDS - elapsed_time

    if st.button("📺 광고 시청하기 (5점)", key="watch_ad_button", disabled=not can_watch_ad):
        if can_watch_ad:
            st.session_state.ad_cooldown_active = True
            st.info("광고를 시청 중입니다. 잠시만 기다려 주세요. (30초 동안 화면이 멈춥니다)")
            progress_bar = st.progress(0)
            for i in range(30):
                time.sleep(1)
                progress_bar.progress((i + 1) * 100 // 30)
            
            st.session_state.points += 5
            # 오늘의 퀘스트 포인트 업데이트
            today = date.today().isoformat()
            if today in st.session_state.study_log:
                st.session_state.study_log[today]["point"] = st.session_state.study_log[today].get("point", 0) + 5
            st.session_state.last_ad_watch_time = datetime.now()
            st.session_state.ad_cooldown_active = False
            st.success("광고 시청 완료! 5포인트를 획득했습니다! 🎉")
            st.rerun()
    
    if not can_watch_ad:
        st.markdown(f"다음 광고 시청까지 **{int(remaining_time)}초** 남았습니다.")
    else:
        st.markdown("새로운 광고를 시청할 수 있습니다!")


# ---------------------------
# 포인트 상점(total)
def shop_page():
    st.title("🛍 포인트 상점")
    st.write("포인트로 다양한 활동을 즐기고 상품을 교환하세요.")

    today = date.today().isoformat()
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None, "step": "select_topic", "quiz_data": [],
            "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False
        }

    tab1, tab2 = st.tabs(["🎮 게임하고 포인트 적립", "📺 광고 보고 포인트 적립"])

    with tab1:
        number_guessing_game()
    
    with tab2:
        ad_watching_reward()
