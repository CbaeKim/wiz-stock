### 로그인과 회원가입 관련 함수
import streamlit as st
import time, re, requests, json

# 백엔드 서버 주소 정의
FASTAPI_ENDPOINT = "http://localhost:8000"

# ---------------------------
# 로그인 페이지 함수
def login_page():
    st.title("🔐 위즈주식 로그인")
    with st.form(key="login_form"):
        username = st.text_input("아이디", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")
        st.markdown("---")
        col1, col2 = st.columns([1,1])
        with col1:
            login_clicked = st.form_submit_button("로그인")
        with col2:
            signup_clicked = st.form_submit_button("회원가입")
        
        if signup_clicked:
            st.session_state.page = "회원가입"
            st.rerun()

        if login_clicked:
            # 빈 값 유효성 검사 추가
            if not username or not password:
                st.error("아이디와 비밀번호를 모두 입력해주세요.")

            else:
                try:
                    # 백엔드 서버에 입력값 검증 요청
                    response = requests.post(
                        FASTAPI_ENDPOINT + '/login/validation',
                        json = {"username": username, "password": password}
                    )

                    # 정상적으로 서버와 통신이 완료되었을 경우
                    if response.status_code == 200:
                        
                        # response body -> json 형태로 파싱
                        data = response.json()

                        if 'message' in data and data['message'] == 'LoginSuccess':
                            response = requests.post(
                                FASTAPI_ENDPOINT + '/login/get_name',
                                json = {"username": username, "password": password}
                            )

                            if response.status_code == 200:
                                data = response.json()
                                if 'user_name' in data:
                                    st.session_state.nickname = data['user_name']
                                    st.session_state.authenticated = True
                                    st.session_state.page = "메인"
                                    st.session_state.user_id = username
                                    st.success("로그인 성공! 환영합니다, " + st.session_state.nickname + "님!")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                    else:
                        print("서버와 통신에 실패했습니다.")
                except requests.exceptions.ConnectionError:
                    st.error("서버에 연결할 수 없습니다.")
                except Exception as e:
                    st.error(f"오류 발생 : {e}")

# ---------------------------
# 회원가입 페이지 함수
def signup_page():
    st.title("📝 위즈주식 회원가입")
    with st.form(key="signup_form"):
        new_username = st.text_input("새 아이디", key="signup_username")
        new_password = st.text_input("새 비밀번호", type="password", key="signup_password")
        st.info("비밀번호는 최소 8자 이상이며, 숫자, 영어(대소문자), 특수문자를 포함해야 합니다.")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_confirm_password")
        new_nickname = st.text_input("닉네임", key="signup_nickname")

        st.markdown("---")
        col1, col2 = st.columns([1,1])
        with col1:
            signup_button = st.form_submit_button("회원가입 완료")
        with col2:
            if st.form_submit_button("로그인 페이지로"):
                st.session_state.page = "로그인"
                st.rerun()

    if signup_button:
        # 회원가입 로직
        # 1. 모든 필드 입력 확인
        if not new_username or not new_password or not confirm_password or not new_nickname:
            st.error("모든 필드를 입력해주세요.")
        # 2. 아이디 중복 확인
        elif new_username in st.session_state.users:
            st.error("이미 존재하는 아이디입니다. 다른 아이디를 사용해주세요.")
        # 3. 닉네임 중복 확인
        elif any(user["nickname"] == new_nickname for user in st.session_state.users.values()):
            st.error("이미 존재하는 닉네임입니다. 다른 닉네임을 사용해주세요.")
        # 4. 비밀번호 일치 확인
        elif new_password != confirm_password:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            # 5. 비밀번호 유효성 검사 (숫자, 영어, 특수문자 포함, 8자 이상)
            if len(new_password) < 8:
                st.error("비밀번호는 최소 8자 이상이어야 합니다.")
            elif not re.search(r"[0-9]", new_password):
                st.error("비밀번호에 숫자가 포함되어야 합니다.")
            elif not re.search(r"[a-zA-Z]", new_password):
                st.error("비밀번호에 영문(대소문자)이 포함되어야 합니다.")
            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
                st.error("비밀번호에 특수문자가 포함되어야 합니다.")
            else:
                # 새로운 사용자 정보 저장 (비밀번호와 닉네임 모두 저장)
                st.session_state.users[new_username] = {"password": new_password, "nickname": new_nickname}
                st.success("회원가입이 완료되었습니다.")
                st.session_state.page = "로그인"
                st.rerun()
