import streamlit as st
import time
import random
import requests

# --- 상수 정의 ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- API 호출 함수 섹션 ---
def get_user_status_api(user_id: str):
    """백엔드에 사용자의 현재 상태 정보(포인트, 참여 횟수 등)를 요청합니다."""
    try:
        response = requests.get(f"{BACKEND_URL}/point/{user_id}/status")
        # 요청이 성공하면(200 OK), JSON 데이터를 반환
        return response.json() if response.ok else None
    except requests.exceptions.RequestException:
        # 서버 연결 실패 등 네트워크 오류 발생 시 None을 반환
        return None

def attendance_check_api(user_id: str):
    """백엔드에 출석 체크를 요청하고 결과를 반환합니다."""
    response = requests.post(f"{BACKEND_URL}/point/attendance", json={"user_id": user_id})
    return response.json() if response.ok else {"error": response.json().get("detail", "오류 발생")}

def ad_points_api(user_id: str):
    """백엔드에 광고 시청에 따른 포인트 지급을 요청합니다."""
    response = requests.post(f"{BACKEND_URL}/point/gain/ad", json={"user_id": user_id})
    return response.json() if response.ok else {"error": response.json().get("detail", "오류 발생")}

def game_result_api(user_id: str, won: bool):
    """백엔드에 게임 결과를 전송하고 결과를 반환합니다."""
    response = requests.post(f"{BACKEND_URL}/point/game-result", json={"user_id": user_id, "won": won})
    return response.json() if response.ok else {"error": response.json().get("detail", "오류 발생")}


# --- UI 렌더링 함수 섹션 ---
def render_attendance_tab(user_id: str):
    """'출석 체크' 탭의 UI를 렌더링합니다."""
    st.subheader("🗓️ 출석 체크")
    already_checked = st.session_state.get('user_attendance_participate', False)
    st.write(f"현재 연속 출석: **{st.session_state.get('user_consecutive_days', 0)}일**")
    
    if st.button("출석 체크하기", disabled=already_checked):
        # 'with st.spinner(...)'는 API가 응답할 때까지 로딩 애니메이션을 보여줌
        with st.spinner("출석 정보를 확인하는 중..."):
            result = attendance_check_api(user_id)
        
        if "error" not in result:
            # 성공 시 토스트 메시지를 띄우고 세션 상태를 업데이트
            st.toast(f"✅ 출석 체크 완료! {result.get('bonus_message', '')}")
            st.session_state.update(
                user_total_point=result['total_point'],
                user_consecutive_days=result['consecutive_days'],
                user_attendance_participate=True
            )
            st.rerun()
        else:
            st.toast(f"🚨 {result['error']}", icon="🚨")
    
    # 이미 참여했다면, 버튼 대신 안내 문구를 보여줌
    if already_checked: 
        st.info("오늘은 이미 출석체크를 완료했습니다.")

def render_game_tab(user_id: str):
    """'숫자 게임' 탭의 UI를 렌더링합니다."""
    st.subheader("🎮 숫자 맞추기 게임")
    if st.session_state.get('user_dailygame_participate', False):
        st.info("오늘은 이미 게임에 참여했습니다. 내일 다시 도전해주세요!")
        return

    st.write("1부터 100 사이의 숫자를 5번 안에 맞춰보세요! 정답 시 10 포인트 획득!")
    
    # st.session_state를 사용하여 게임 상태(시작 전, 진행 중, 종료)를 관리
    if 'game' not in st.session_state:
        st.session_state.game = {'state': 'ready'}
    game = st.session_state.game

    if game['state'] == 'ready':
        if st.button("게임 시작!"):
            # 게임 시작 버튼을 누르면 랜덤 숫자를 생성하고 상태를 'playing'으로 변경
            game.update({'state': 'playing', 'secret': random.randint(1, 100), 'guesses': 0, 'message': '게임을 시작합니다.'})
            st.rerun()
    elif game['state'] == 'playing':
        st.info(game['message'])
        st.write(f"남은 기회: **{5 - game['guesses']}**")
        guess = st.number_input("숫자를 입력하세요 (1-100)", min_value=1, max_value=100, key="guess_input", value=50)
        
        if st.button("제출"):
            game['guesses'] += 1
            if guess == game['secret']: # 정답을 맞춘 경우
                with st.spinner("정답 확인 중..."):
                    result = game_result_api(user_id, won=True)
                if "error" not in result:
                    st.toast("🎉 정답! 10포인트를 획득했습니다!", icon="🎉")
                    st.session_state.update(user_total_point=result['total_point'], user_dailygame_participate=True)
                    st.balloons()
                else: 
                    st.toast(f"🚨 {result['error']}", icon="🚨")
                game['state'] = 'over'; st.rerun()
            elif game['guesses'] >= 5: # 기회를 모두 소진한 경우
                st.warning(f"아쉽네요! 정답은 {game['secret']}였습니다.")
                with st.spinner("결과 기록 중..."):
                    game_result_api(user_id, won=False) # 패배 결과 전송
                st.toast("게임 참여가 기록되었습니다.", icon="💾")
                st.session_state.user_dailygame_participate = True
                game['state'] = 'over'; st.rerun()
            else: # 오답인 경우 (기회 남음)
                game['message'] = f"'{guess}'보다 더 낮은 숫자입니다!" if guess > game['secret'] else f"'{guess}'보다 더 높은 숫자입니다!"
                st.rerun()
    elif game['state'] == 'over':
        st.info("게임이 종료되었습니다.")
        if st.button("돌아가기"): game['state'] = 'ready'; st.rerun()

def render_ad_tab(user_id: str):
    """'광고 보기' 탭의 UI를 렌더링합니다."""
    st.subheader("📺 광고 보고 포인트 적립")
    participation_count = st.session_state.get('user_ad_participation', 0)
    already_participated_fully = (participation_count >= 3)
    st.write(f"오늘 광고 참여 횟수: **{participation_count}/3**")

    if st.button("📺 광고 시청하기 (5점)", disabled=already_participated_fully):
        with st.spinner("광고를 시청하는 중..."):
            time.sleep(2) # 실제 광고 대신 2초 대기
            result = ad_points_api(user_id)
        if "error" not in result:
            st.toast("✅ 광고 시청 완료! 5포인트를 획득했습니다!")
            st.session_state.update(
                user_total_point=result['total_point'], 
                user_ad_participation=result['new_ad_count']
            )
            st.balloons(); st.rerun()
        else: 
            st.toast(f"🚨 {result['error']}", icon="🚨")
    
    if already_participated_fully: 
        st.info("오늘은 광고 시청 기회를 모두 사용했습니다.")

# --- 메인 페이지 함수 ---
def shop_page():
    """포인트 획득 페이지 전체를 렌더링하는 메인 함수입니다."""
    st.title("🎁 포인트 획득")
    
    # 로그인 상태가 아니면 경고 메시지를 보여주고 함수를 종료
    if not st.session_state.get("authenticated"):
        st.warning("로그인이 필요한 서비스입니다."); return

    # st.session_state에서 현재 로그인한 사용자 ID를 가져옴
    user_id = st.session_state.get("user_id")
    
    # 세션이 시작된 후 처음 페이지에 방문했을 때만 사용자 정보를 불러옴
    # 'user_status_loaded' 플래그를 사용하여 API 중복 호출을 방지
    if 'user_status_loaded' not in st.session_state:
        with st.spinner("사용자 정보를 불러오는 중..."):
            status_data = get_user_status_api(user_id)
        if status_data:
            # API 호출에 성공하면, 가져온 데이터로 st.session_state를 업데이트
            st.session_state.update(
                user_total_point=status_data.get('total_point', 0),
                user_attendance_participate=status_data.get('attendance_participate', False),
                user_ad_participation=status_data.get('ad_participation', 0),
                user_dailygame_participate=status_data.get('dailygame_participate', False),
                user_consecutive_days=status_data.get('consecutive_days', 0),
                user_status_loaded=True # 데이터 로드 완료 플래그를 True로 설정
            )
        else:
            st.error("사용자 정보를 불러오는 데 실패했습니다. 페이지를 새로고침 해주세요.")
            return

    tab1, tab2, tab3 = st.tabs(["🗓️ 출석 체크", "🎮 숫자 게임", "📺 광고 보기"])
    with tab1: render_attendance_tab(user_id)
    with tab2: render_game_tab(user_id)
    with tab3: render_ad_tab(user_id)