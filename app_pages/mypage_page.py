### 서브 콘텐츠 7: 마이페이지
"""
[이 파일의 역할 (세 줄 요약)]
- Streamlit 화면에서 '마이페이지' 섹션을 그립니다.
- 로그인되어 있으면 FastAPI(/mypage/{user_id})를 통해 supabase DB의 사용자 정보를 가져옵니다.
- 서버에서 받거나(또는 아직 로그인 전/통신 실패 시) 안전한 기본값을 session_state에 채운 뒤 화면에 출력합니다.

[데이터 흐름]
FastAPI (백엔드) → (HTTP GET) → Streamlit(프론트) → st.session_state 저장 → UI 렌더링
"""

# ────────────────────────────────────────────────────────────────────────────
# 1. 필수 라이브러리 임포트
#    - streamlit: 웹 UI 작성 라이브러리. st로 사용합니다.
#    - requests: FastAPI(백엔드)에 HTTP 요청을 보내고, 응답(JSON)을 받습니다.
# ────────────────────────────────────────────────────────────────────────────
import streamlit as st
import requests

# ────────────────────────────────────────────────────────────────────────────
# 2. 백엔드(FastAPI) 기본 주소
#    - "http://localhost:8000"는 내 컴퓨터(=localhost)에서 8000 포트로 실행 중인 FastAPI를 의미합니다.
#    - 실제 배포 시에는 "https://api.example.com" 같은 실제 도메인으로 교체합니다.
#      (http ↔ https 차이: 개발 중엔 http(보안X) / 운영에선 https(보안O) 사용)
# ────────────────────────────────────────────────────────────────────────────
FASTAPI_ENDPOINT = "http://localhost:8000"

# ────────────────────────────────────────────────────────────────────────────
# 3. mypage_content = Streamlit에서 "마이페이지 화면"을 그리는 함수입니다.
#    - index.py 에서 이 함수를 호출하면 화면이 렌더링됩니다.
# ────────────────────────────────────────────────────────────────────────────
def mypage_content():
    st.title("👤 마이페이지")
    st.subheader("내 정보")

    # ────────────────────────────────────────────────────────────────────────
    # [A] 로그인된 경우에만 백엔드 서버(FastAPI)에 요청을 보내서 DB(supabase)의 값을 가져옵니다
    #     - 조건: session_state에 user_id가 있고, 값이 "익명 사용자"가 아닐 때
    #     - 성공: 응답 JSON을 session_state에 채움
    # ────────────────────────────────────────────────────────────────────────
    if "user_id" in st.session_state and st.session_state.user_id != "익명 사용자":
        try:
            # res = requests.get(url)
            # - GET: 서버에서 "읽기" 요청을 보낼 때 쓰는 HTTP 메서드
            # - f"{...}": f-string. 중괄호({...}) 안에 파이썬 변수가 들어가 문자열이 완성됨
            res = requests.get(f"{FASTAPI_ENDPOINT}/mypage/{st.session_state.user_id}")

            # res.status_code: HTTP 상태 코드(200=성공, 404=없음, 500=서버오류 등)
            if res.status_code == 200:
                data = res.json()  # 응답 본문(JSON)을 파이썬 dict/list로 변환

                # 라우터가 실패 시 {"message": "..."} 형태로 응답(mypage_router.py 참조)
                # "message" 키가 없으면 정상 데이터로 간주합니다.
                if "message" not in data:
                    # dict.get("키"): 키가 없으면 None을 돌려줍니다(안전)
                    st.session_state.nickname = data.get("name")
                    st.session_state.nickname_color = data.get("nickname_color")

                    st.session_state.contact = data.get("contact")
                    st.session_state.email = data.get("email")

                    st.session_state.points = data.get("total_point")
                    st.session_state.daily_point_bonus = data.get("daily_point_bonus")

                    st.session_state.attendance = data.get("attendance")
                    st.session_state.continuous_attendance = data.get("continuous_attendance")
                    st.session_state.last_attendance_date = data.get("last_attendance_date")

                    st.session_state.my_trophies = data.get("my_trophies")
                    st.session_state.purchased_indicators = data.get("purchased_indicators")

        except Exception as e:
            # except: 네트워크/서버 에러 등 → 사용자에게 알림 (앱 중단 X)
            # str(e): 예외 객체를 사람이 읽을 수 있는 문자열로 변환
            st.error(f"서버에서 데이터를 불러오지 못했습니다. (사유: {str(e)})")

    # ────────────────────────────────────────────────────────────────────────
    # [B] 세션 기본값 보장
    #     - 서버에서 값을 못 불러오거나, 로그인 전이라 비어있을 경우 대비
    #     - 'defaults' 딕셔너리: 안전하게 화면에 표시할 예비 값 목록
    #     - for문: 목록을 돌면서 세션에 값이 없거나(None) 비어있으면 기본값으로 채움
    # ────────────────────────────────────────────────────────────────────────
    defaults = {
        "user_id": "익명 사용자",                # 로그인 전 기본 아이디
        "nickname": "익명",                      # 기본 닉네임

        "contact": "미등록",                     # 기본 연락처
        "email": "미등록",                       # 기본 이메일

        "points": 0,                             # 기본 포인트
        "daily_point_bonus": 0,                  # 기본 보너스 점수

        "attendance": 0,                         # 기본 출석일 수
        "continuous_attendance": 0,              # 기본 연속 출석일 수
        "last_attendance_date": "기록 없음",      # 기본 마지막 출석일

        "my_trophies": [],                       # 기본 훈장 목록(비어있음)
        "purchased_indicators": [],              # 기본 구매 목록(비어있음)
    }

    # dict.items(): (키, 값) 쌍을 순회 → 세션에 기본값 채우기
    for key, value in defaults.items():
        # 조건: 키가 없거나(None 포함) → 기본값으로 설정
        if key not in st.session_state or st.session_state[key] is None:
            st.session_state[key] = value

    # ────────────────────────────────────────────────────────────────────────
    # [C] 화면에 표시하기 쉽게, session_state의 값을 지역 변수로 꺼내 둡니다.
    #     (읽기 편하고 오타 줄이기 목적)
    # ────────────────────────────────────────────────────────────────────────
    user_id = st.session_state.user_id
    nickname = st.session_state.nickname
    nickname_color = st.session_state.get("nickname_color", None)  # 색상이 없을 수도 있으므로 None 기본값

    contact = st.session_state.contact
    email = st.session_state.email

    points = st.session_state.points
    daily_bonus = st.session_state.daily_point_bonus  # 보너스는 양수/음수 모두 가능(사용/지급)

    attendance = st.session_state.attendance
    continuous_attendance = st.session_state.continuous_attendance
    last_attendance_date = st.session_state.last_attendance_date

    my_trophies = st.session_state.my_trophies
    purchased_indicators = st.session_state.purchased_indicators

    # ────────────────────────────────────────────────────────────────────────
    # [D] 닉네임 출력 (색상 적용)
    # ────────────────────────────────────────────────────────────────────────
    if nickname_color:
        # HTML <span> 태그를 사용해 글자 색상 적용
        # - style="color:...": 글자색 지정 (예: #ff0000 또는 'red')
        # - unsafe_allow_html=True: HTML을 실제로 그리도록 허용(기본은 보안상 비활성)
        st.markdown(
            f'**닉네임:** <span style="color:{nickname_color}; font-weight:700;">{nickname}</span>',
            unsafe_allow_html=True
        )
    else:
        # 색상 정보가 없으면 그냥 굵게만 표시
        st.markdown(f"**닉네임:** {nickname}")

    # ────────────────────────────────────────────────────────────────────────
    # [E] 기본 정보(좌) / 출석 정보(우) — CSS 없이 2열 배치 + 인라인 출력
    # ────────────────────────────────────────────────────────────────────────
    #   - st.columns(2): 화면을 2개의 세로 영역으로 나눕니다.
    #   - gap="medium": 두 열 사이 간격을 중간 정도로 맞춥니다.
    left, right = st.columns(2, gap="medium")

    #   - st.markdown(f"**라벨:** 값") 형태로 한 줄씩 출력합니다(굵게는 ** 로 감쌈)
    # 왼쪽: 계정 기본정보
    with left:
        st.markdown(f"**아이디:** {user_id}")
        st.markdown(f"**연락처:** {contact}")
        st.markdown(f"**이메일:** {email}")

    # 오른쪽: 출석 관련정보
    with right:
        st.markdown(f"**총 출석일:** {attendance}")
        st.markdown(f"**연속 출석일:** {continuous_attendance}")
        st.markdown(f"**마지막 출석일:** {last_attendance_date}")

    # 시각적 구분선
    st.divider()

    # ────────────────────────────────────────────────────────────────────────
    # [F] 포인트/보너스 지표: metric 2개
    #   - st.metric(label, value, delta=None, delta_color="normal"):
    #       * value: 현재 값(굵게 크게)
    #       * delta: 변화량(예: +5, -3)
    # ────────────────────────────────────────────────────────────────────────
    m1, m2 = st.columns(2)
    with m1:
        # 총 보유 포인트 현재값 + 오늘(또는 이번 렌더링 기준)의 보너스를 delta로 표기
        st.metric("총 보유 포인트", f"{points:,} P", delta=f"{daily_bonus:+,} P")
    with m2:
        # 보너스 자체도 별도 지표로 보여줌
        st.metric("일일 추가 포인트 보너스", f"{daily_bonus:,} P")

    # 시각적 구분선
    st.divider()

    # ────────────────────────────────────────────────────────────────────────
    # [G] 훈장 섹션 (하나 이상의 훈장이 있다면 실행합니다.)
    # ────────────────────────────────────────────────────────────────────────
    st.subheader("획득한 훈장")
    if my_trophies:
        # 훈장 코드(키) → 이름/희귀도/색상 등의 메타 정보(값)를 미리 정의해둔 딕셔너리입니다.
        trophies_meta = {
            "quiz_master_7days": {"name": "퀴즈 마스터 (7일 연속)", "rarity": "레어", "color": "#1E90FF"},
            "daily_champion": {"name": "데일리 챔피언", "rarity": "노말", "color": "#A9A9A9"},
            "unique_learner": {"name": "유니크 러너", "rarity": "유니크", "color": "#800080"},
            "legendary_investor": {"name": "레전드 투자자", "rarity": "레전드", "color": "#FFD700"}
        }

        # 내가 가진 훈장 코드들을 하나씩 꺼내서 화면에 표시합니다.
        # 만약 정의되지 않은 훈장 코드가 들어와도 앱이 죽지 않도록 "알 수 없는 훈장"으로 안전 처리합니다.
        for trophy_key in my_trophies:
            trophy = trophies_meta.get(
                trophy_key,
                {"name": "알 수 없는 훈장", "rarity": "", "color": "#000000"}  # 안전 기본값
            )

            # 아래는 HTML 인라인 스타일을 잠깐 사용(간단한 박스 시각화용).
            # - unsafe_allow_html=True: HTML을 실제로 그려도 된다는 허용 스위치.
            st.markdown(f"""
                <div style="border:1px solid #ddd; padding:8px; margin-bottom:4px; border-radius:4px; background-color:#f0f8ff;">
                    <strong style="color:{trophy['color']};">{trophy['name']} ({trophy['rarity']})</strong>
                </div>
            """, unsafe_allow_html=True)
    else:
        # 보유 훈장이 하나도 없을 때
        st.write("아직 획득한 훈장이 없습니다.")

    # ────────────────────────────────────────────────────────────────────────
    # [H] 구매한 보조지표 섹션
    #     - 리스트가 비어있지 않으면 하나씩 목록으로 출력합니다, 없으면 상점 안내 문구
    # ────────────────────────────────────────────────────────────────────────
    st.subheader("구매한 보조지표")
    if purchased_indicators:
        for indicator in purchased_indicators:
            st.markdown(f"- {indicator}")
    else:
        st.write("아직 구매한 보조지표가 없습니다. '보조지표 상점' 페이지에서 구매할 수 있습니다. ")
