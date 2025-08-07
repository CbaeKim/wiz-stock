### 서브 콘텐츠 5: 포인트 상점

import streamlit as st
from datetime import date, datetime, timedelta
import random
import time

# ---------------------------
# 숫자 맞추기 게임
def number_guessing_game():
    st.subheader("숫자 맞추기 게임")
    st.write("1부터 100 사이의 숫자를 5번 안에 맞춰보세요! 정답 시 10 포인트 획득!")

    # 게임 상태 변수 초기화
    if "game_state" not in st.session_state:
        st.session_state.game_state = "initial"
    if "secret_number" not in st.session_state:
        st.session_state.secret_number = 0
    if "guesses" not in st.session_state:
        st.session_state.guesses = 0
    if "game_message" not in st.session_state:
        st.session_state.game_message = ""
    if "game_cooldown_start_time" not in st.session_state:
        st.session_state.game_cooldown_start_time = None
    if "last_guess_value" not in st.session_state:
        st.session_state.last_guess_value = 50
    if "game_over_reason" not in st.session_state:
        st.session_state.game_over_reason = ""


    # 게임 재시작 또는 쿨다운 상태 처리
    if st.session_state.game_state == "initial":
        st.session_state.secret_number = random.randint(1, 100)
        st.session_state.guesses = 0
        st.session_state.game_message = "새로운 게임이 시작되었습니다. 숫자를 맞춰보세요!"
        st.session_state.game_state = "playing"
        st.session_state.game_cooldown_start_time = None
        st.session_state.game_over_reason = ""
        if st.session_state.game_state != "initial":
            st.rerun()

    elif st.session_state.game_state == "cooldown":
        current_time = datetime.now()
        if st.session_state.game_cooldown_start_time is None:
            st.session_state.game_state = "initial"
            st.rerun()
            return
        
        elapsed_time = (current_time - st.session_state.game_cooldown_start_time).total_seconds()
        remaining_game_cooldown_time = 60 - elapsed_time

        # 게임 결과 메시지 표시
        if st.session_state.game_over_reason == "lost":
            st.warning(f"아쉽네요! 5번의 기회를 모두 소진했습니다. 정답은 {st.session_state.secret_number}였습니다.")
        elif st.session_state.game_over_reason == "won":
            st.success(f"정답입니다! 🎉 {st.session_state.guesses}번 만에 맞췄어요! +10점")

        # 쿨다운 상태 표시
        if remaining_game_cooldown_time > 0:
            st.info(f"게임 재도전까지 **{int(remaining_game_cooldown_time)}초** 남았습니다. 다른 활동을 이용해보세요.")
            st.number_input("숫자를 입력하세요 (1-100)", min_value=1, max_value=100, value=50, key="number_guess_disabled", disabled=True)
            st.button("제출", key="submit_guess_disabled", disabled=True)
        else:
            # 쿨다운이 끝나면 게임 초기화
            st.session_state.game_state = "initial"
            st.session_state.game_cooldown_start_time = None
            st.session_state.game_message = "새로운 게임이 시작되었습니다. 숫자를 맞춰보세요!"
            st.rerun()

    elif st.session_state.game_state == "playing":
        st.info(st.session_state.game_message)
        st.write(f"시도 횟수: {st.session_state.guesses}/5")

        guess = st.number_input("숫자를 입력하세요 (1-100)", min_value=1, max_value=100, value=st.session_state.last_guess_value, key="number_guess")
        st.session_state.last_guess_value = guess

        if st.button("제출", key="submit_guess"):
            st.session_state.guesses += 1
            if guess < st.session_state.secret_number:
                st.session_state.game_message = "더 높은 숫자입니다!"
            elif guess > st.session_state.secret_number:
                st.session_state.game_message = "더 낮은 숫자입니다!"
            else:
                # 정답을 맞춘 경우
                st.session_state.game_message = f"정답입니다! 🎉 {st.session_state.guesses}번 만에 맞췄어요! +10점"
                if "points" not in st.session_state:
                    st.session_state.points = 0
                st.session_state.points += 10
                today_iso = date.today().isoformat()
                if today_iso in st.session_state.study_log:
                    st.session_state.study_log[today_iso]["point"] = st.session_state.study_log[today_iso].get("point", 0) + 10
                st.balloons()
                st.session_state.game_state = "cooldown"
                st.session_state.game_over_reason = "won"
                st.session_state.game_cooldown_start_time = datetime.now()
            
            # 5번의 기회를 모두 소진한 경우 (오답)
            if st.session_state.game_state == "playing" and st.session_state.guesses >= 5:
                st.session_state.game_message = f"아쉽네요! 5번의 기회를 모두 소진했습니다. 정답은 {st.session_state.secret_number}였습니다. 60초 후에 다시 도전해주세요."
                st.session_state.game_state = "cooldown"
                st.session_state.game_over_reason = "lost"
                st.session_state.game_cooldown_start_time = datetime.now()
            
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
            st.rerun()
    
    if not can_watch_ad:
        st.markdown(f"다음 광고 시청까지 **{int(remaining_time)}초** 남았습니다.")
    else:
        st.markdown("새로운 광고를 시청할 수 있습니다!")

def ad_active_state():
    st.title("광고를 시청 중입니다.")
    st.info("광고가 끝날 때까지 잠시만 기다려주세요.")
    progress_bar = st.progress(0)
    
    # 30초 동안 진행되는 광고 시뮬레이션
    for i in range(30):
        time.sleep(1)
        progress_bar.progress((i + 1) / 30)
    
    st.session_state.points += 5
    today = date.today().isoformat()
    if today in st.session_state.study_log:
        st.session_state.study_log[today]["point"] = st.session_state.study_log[today].get("point", 0) + 5
    
    st.session_state.last_ad_watch_time = datetime.now()
    st.success("광고 시청 완료! 5포인트를 획득했습니다! 🎉")
    st.balloons()
    st.session_state.ad_cooldown_active = False
    st.rerun()

# ---------------------------
# 출석 체크
def attendance_check():
    st.subheader("🗓️ 출석 체크")
    st.write("매일 출석하고 포인트를 적립하세요! 7일 연속 출석 시 보너스 10포인트!")

    # 출석 관련 세션 상태 초기화
    if "last_attendance_date" not in st.session_state:
        st.session_state.last_attendance_date = None
    if "consecutive_days" not in st.session_state:
        st.session_state.consecutive_days = 0
    if "attendance_points_today_given" not in st.session_state:
        st.session_state.attendance_points_today_given = False

    today = date.today()
    can_check_in = True
    message = ""

    if st.session_state.last_attendance_date:
        last_date_obj = datetime.fromisoformat(st.session_state.last_attendance_date).date()
        if last_date_obj == today:
            can_check_in = False
            message = "오늘은 이미 출석체크를 완료했습니다! 내일 다시 방문해주세요."
            st.session_state.attendance_points_today_given = True
        elif last_date_obj == today - timedelta(days=1):
            can_check_in = True
            message = "오늘 출석체크를 해주세요!"
            st.session_state.attendance_points_today_given = False
        else:
            st.session_state.consecutive_days = 0
            can_check_in = True
            message = "연속 출석 기록이 초기화되었습니다. 다시 시작하세요!"
            st.session_state.attendance_points_today_given = False
    else:
        st.session_state.consecutive_days = 0
        can_check_in = True
        message = "오늘 출석체크를 해주세요!"
        st.session_state.attendance_points_today_given = False

    st.write(f"현재 연속 출석: **{st.session_state.consecutive_days}일차**")

    num_cols = 7
    cols = st.columns(num_cols)
    for i in range(7):
        with cols[i]:
            day_number = i + 1
            is_checked_today = st.session_state.attendance_points_today_given
            current_consecutive_days = st.session_state.consecutive_days
            if is_checked_today:
                if day_number <= current_consecutive_days:
                    st.markdown(f"<div style='text-align: center; background-color: #d4edda; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: auto; border: 2px solid #28a745; color: #28a745; font-weight: bold;'>✅</div><div style='text-align: center; font-size: 0.8em;'>{day_number}일차</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center; background-color: #f8f9fa; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: auto; border: 2px solid #6c757d; color: #6c757d; font-weight: bold;'>{day_number}</div><div style='text-align: center; font-size: 0.8em;'>{day_number}일차</div>", unsafe_allow_html=True)
            else:
                if day_number < current_consecutive_days + 1:
                    st.markdown(f"<div style='text-align: center; background-color: #d4edda; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: auto; border: 2px solid #28a745; color: #28a745; font-weight: bold;'>✅</div><div style='text-align: center; font-size: 0.8em;'>{day_number}일차</div>", unsafe_allow_html=True)
                elif day_number == current_consecutive_days + 1 and can_check_in:
                    st.markdown(f"<div style='text-align: center; background-color: #e0f2f7; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: auto; border: 2px solid #007bff; color: #007bff; font-weight: bold;'>{day_number}</div><div style='text-align: center; font-size: 0.8em;'>{day_number}일차</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center; background-color: #f8f9fa; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: auto; border: 2px solid #6c757d; color: #6c757d; font-weight: bold;'>{day_number}</div><div style='text-align: center; font-size: 0.8em;'>{day_number}일차</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("출석 체크하기 (1P)", key="check_attendance_button", disabled=not can_check_in or st.session_state.attendance_points_today_given):
        if can_check_in and not st.session_state.attendance_points_today_given:
            st.session_state.points += 1
            today_iso = today.isoformat()
            if today_iso not in st.session_state.study_log:
                st.session_state.study_log[today_iso] = {"topic": None, "step": "select_topic", "quiz_data": [], "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False}
            st.session_state.study_log[today_iso]["point"] = st.session_state.study_log[today_iso].get("point", 0) + 1

            if st.session_state.last_attendance_date == (today - timedelta(days=1)).isoformat():
                st.session_state.consecutive_days += 1
            else:
                st.session_state.consecutive_days = 1

            st.session_state.last_attendance_date = today_iso
            st.session_state.attendance_points_today_given = True

            st.success("출석체크 완료! 1포인트를 획득했습니다! 🎉")
            st.balloons()

            current_consecutive = st.session_state.consecutive_days

            if current_consecutive == 7:
                st.session_state.points += 10
                st.session_state.study_log[today_iso]["point"] = st.session_state.study_log[today_iso].get("point", 0) + 10
                st.success("7일 연속 출석! 보너스 10포인트를 획득했습니다! 🥳")
                st.session_state.consecutive_days = 0
                st.balloons()
            
            st.rerun()
        else:
            st.warning(message)
    else:
        if not can_check_in or st.session_state.attendance_points_today_given:
            st.info(message)
        else:
            st.info(message)

# ---------------------------
# 포인트 상점 (전체)
def shop_page():
    st.title("🛍 포인트 상점")
    st.write("포인트로 다양한 활동을 즐기고 상품을 교환하세요.")

    if "points" not in st.session_state:
        st.session_state.points = 0
    if "study_log" not in st.session_state:
        st.session_state.study_log = {}
    if "ad_cooldown_active" not in st.session_state:
        st.session_state.ad_cooldown_active = False
    
    today = date.today().isoformat()
    if today not in st.session_state.study_log:
        st.session_state.study_log[today] = {
            "topic": None, "step": "select_topic", "quiz_data": [],
            "quiz_index": 0, "point": 0, "balloons_shown_for_quest": False
        }

    # 광고 시청 중인 경우 다른 탭 접근을 막음
    if st.session_state.ad_cooldown_active:
        ad_active_state()
    else:
        # 탭 구성: 게임, 광고, 출석체크
        tab1, tab2, tab3 = st.tabs(["🎮 게임하고 포인트 적립", "📺 광고 보고 포인트 적립", "🗓️ 출석 체크"])

        with tab1:
            number_guessing_game()
        
        with tab2:
            ad_watching_reward()
            
        with tab3:
            attendance_check()