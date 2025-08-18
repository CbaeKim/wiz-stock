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
        # Definition ID, PW, Confirm_PW, Nickname
        new_username = st.text_input("새 아이디", key="signup_username")
        new_password = st.text_input("새 비밀번호", type="password", key="signup_password")
        st.info("비밀번호는 최소 8자 이상이며, 숫자, 영어(대소문자), 특수문자를 포함해야 합니다.")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_confirm_password")
        new_nickname = st.text_input("닉네임", key="signup_nickname")
        
        if new_nickname:
            st.info("닉네임은 회원가입 버튼 클릭 시 자동으로 중복 확인됩니다.")
            
        st.markdown("---")
        col1, col2 = st.columns([1,1])
        with col1:
            signup_button = st.form_submit_button("회원가입 완료")
        with col2:
            if st.form_submit_button("로그인 페이지로"):
                st.session_state.page = "로그인"
                st.rerun()

    if signup_button:
        # Reinforce client side validation
        if not new_username or not new_password or not confirm_password or not new_nickname:
            st.error("모든 필드를 입력해주세요.")
        elif new_password != confirm_password:
            st.error("비밀번호가 일치하지 않습니다.")
        elif len(new_password) < 8 or \
           not re.search(r"[0-9]", new_password) or \
           not re.search(r"[a-zA-Z]", new_password) or \
           not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
            st.error("비밀번호는 최소 8자 이상이며, 숫자, 영어(대소문자), 특수문자를 포함해야 합니다.")
        else:
            try:
                # Request Sign up to FastAPI Server
                response = requests.post(
                    FASTAPI_ENDPOINT + "/sign_up/",
                    json = {
                        "username": new_username,
                        "password": new_password,
                        "nickname": new_nickname
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success(data["message"])
                    st.session_state.page = "로그인"
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"회원가입 실패: {response.json().get('detail', '알 수 없는 오류')}")

            except requests.exceptions.ConnectionError:
                st.error("서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인해주세요.")
            except Exception as e:
                st.error(f"오류 발생: {e}")