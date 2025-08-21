# shop_page.py
# ─────────────────────────────────────────────────────────────────────────────
# 목적:
#   - 상점(Shop) 프론트엔드 화면 (Streamlit)
#   - 서버(FastAPI)의 /shop/purchase 엔드포인트를 호출하여
#     1) 포인트 차감
#     2) 랜덤 박스 보상 지급
#     3) 최종 포인트를 화면에 표시
#   - 화면(UI) 상의 버튼/모달/안내 메시지 관리
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st                # Streamlit UI 라이브러리
import requests                      # HTTP 요청 라이브러리 (서버와 통신)
from datetime import date            # 오늘 날짜 확인(필요 시)

# ─────────────────────────────────────────────────────────────────────────────
# 서버 기본 주소 (FastAPI)
#   - 예: http://localhost:8000
#   - 배포 환경에서는 환경변수/설정 파일로 관리 권장
# ─────────────────────────────────────────────────────────────────────────────
FASTAPI_ENDPOINT = "http://localhost:8000"

# ─────────────────────────────────────────────────────────────────────────────
# 네트워크 타임아웃(초) 상수
#   - 모든 requests 호출에 동일하게 사용
#   - 초보자 실수 방지: 숫자를 여기서만 바꾸면 전체에 반영됨
# ─────────────────────────────────────────────────────────────────────────────
TIMEOUT_S = 10

# ─────────────────────────────────────────────────────────────────────────────
# 세션 기본값 설정 함수
#   - st.session_state: 페이지 간/컴포넌트 간 공유되는 상태 저장소
#   - 키가 없을 때만 기본값을 넣음(setdefault)
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_session_defaults():
    s = st.session_state
    s.setdefault("user_id", "")                     # 로그인 후 채워짐(이메일/고유ID)
    s.setdefault("points", 0)                       # 현재 보유 포인트(서버와 동기화)
    s.setdefault("last_ad_watch_time", None)        # 광고 본 마지막 시각(기능형 아이템 연동)
    s.setdefault("ad_cooldown_active", False)       # 광고 쿨다운 여부
    s.setdefault("game_state", "initial")           # 게임 상태("initial"/"cooldown" 등)
    s.setdefault("game_cooldown_start_time", None)  # 게임 쿨다운 시작 시각
    s.setdefault("buying", False)                   # 중복 클릭 방지 플래그(구매 중 true)

# ─────────────────────────────────────────────────────────────────────────────
# 서버에서 최신 포인트를 가져와 세션에 반영
#   - user_id가 유효할 때만 요청
#   - 실패해도 UI는 계속 동작 (표시값만 잠시 다를 수 있음)
# ─────────────────────────────────────────────────────────────────────────────
def _sync_points_from_server(user_id: str):
    if not user_id:
        return
    try:
        # 예시: /mypage/{user_id}가 total_point를 내려준다는 전제
        r = requests.get(f"{FASTAPI_ENDPOINT}/mypage/{user_id}", timeout=TIMEOUT_S)
        if r.status_code == 200:
            data = r.json()
            # 서버 설계상 "message" 키가 오류 신호일 수 있어 예외 처리
            if "message" not in data:
                st.session_state.points = data.get("total_point", st.session_state.points)
    except Exception:
        # 네트워크 오류/서버 오류 등은 무시하고 넘어감(화면은 계속 표시)
        pass

# ─────────────────────────────────────────────────────────────────────────────
# 아이템 목록
#   - 서버의 PRICING(신뢰 가격표)과 "code/price"가 반드시 같아야 함
#   - desc(설명)는 사용자에게 보여주는 안내 문구
#   - RNG 보상 내용은 서버 RNG_TABLE과 일치하는 값으로 안내(혼동 방지)
# ─────────────────────────────────────────────────────────────────────────────
ITEMS = [
    
    # {
    #     "key": "ad_cooldown_reset",             # UI용 고유 키(버튼 키 등)
    #     "code": "AD_COOLDOWN_RESET",            # 서버 검증 코드(PRICING의 키)
    #     "name": "광고 쿨다운 초기화",             # 화면 표시 이름
    #     "price": 1,                             # 서버 가격표와 동일해야 함
    #     "desc": "광고 보기 대기시간을 즉시 초기화합니다."  # 설명
    # },
    # {
    #     "key": "game_cooldown_skip",
    #     "code": "GAME_COOLDOWN_SKIP",
    #     "name": "게임 재도전 패스",
    #     "price": 5,
    #     "desc": "게임 쿨다운 상태를 즉시 해제합니다."
    # },
    
# 인게임 아이템
    {
        "key": "rng_box_small",
        "code": "RNG_BOX_SMALL",
        "name": "랜덤 포인트 상자(소)",
        "price": 20,
        "desc": "확률적 보상 (0, 8, 20, 25, 100P 중 하나)",
    },
    {
        "key": "rng_box_big",
        "code": "RNG_BOX_BIG",
        "name": "랜덤 포인트 상자(대)",
        "price": 50,
        "desc": "확률적 보상 (0, 20, 50, 65, 250P 중 하나)",
    },

# 실제 상품
    {
        "key": "coffee_americano",
        "code": "COFFEE_AMERICANO",
        "name": "아메리카노 (예정)",
        "price": 180,
        "desc": "아메리카노 기프트쿠폰. 지금은 미리보기만 제공돼요.",
        "img": "https://image.homeplus.kr/td/ed6b7ce1-031f-45f2-a8ee-86fa781aa1e0",  
        "sellable": True
    },
    {
        "key": "coffee_latte",
        "code": "COFFEE_LATTE",
        "name": "카페라떼 (예정)",
        "price": 200,
        "desc": "카페라떼 기프트쿠폰. 지금은 미리보기만 제공돼요.",
        "img": "https://image.homeplus.kr/td/ad42d3de-ea74-4b95-b612-2267d50da108",
        "sellable": True
    },
    {
        "key": "icecream_cone",
        "code": "ICECREAM_CONE",
        "name": "아이스크림 콘 (예정)",
        "price": 150,
        "desc": "아이스크림 기프트쿠폰. 지금은 미리보기만 제공돼요.",
        "img": "https://image.homeplus.kr/td/e7bf9658-6132-4947-a818-fe2a8504c3d2",
        "sellable": False
    },
    {
        "key": "sandwich_basic",
        "code": "SANDWICH_BASIC",
        "name": "샌드위치 (예정)",
        "price": 250,
        "desc": "샌드위치 기프트쿠폰. 지금은 미리보기만 제공돼요.",
        "img": "https://image.homeplus.kr/td/111e0e48-4471-46ba-9040-1f79e6057b4b",
        "sellable": False
    }
    ]

# ─────────────────────────────────────────────────────────────────────────────
# 구매 HTTP 호출
#   - 서버: POST /shop/purchase
#   - payload: user_id, item_code, item_name, price
#   - 서버는 "먼저 차감" 후, RNG 아이템이면 "보상 지급"까지 처리
#   - 성공 시 응답: {"ok": True, "total_point": 최종포인트, "rng_gain": 보상(없으면 0)}
# ─────────────────────────────────────────────────────────────────────────────
def _purchase(user_id: str, code: str, name: str, price: int):
    try:
        # 요청 바디(JSON)
        payload = {
            "user_id": user_id,
            "item_code": code,
            "item_name": name,   # 표시용(서버 검증에는 영향 없음)
            "price": price       # 서버 PRICING과 같아야 통과
        }

        # 서버로 POST (타임아웃 상수 적용)
        r = requests.post(f"{FASTAPI_ENDPOINT}/shop/purchase", json=payload, timeout=TIMEOUT_S)

        # 응답 JSON 파싱(서버가 JSON을 보낸다는 전제)
        data = r.json()

        # HTTP 200 + ok=True 이면 성공
        if r.status_code == 200 and data.get("ok"):
            # 서버가 내려준 "최종 포인트"를 그대로 세션에 저장
            #  - 프론트에서 직접 포인트를 더/빼지 않음(불일치 방지)
            if "total_point" in data:
                st.session_state.points = data["total_point"]
            return True, None, data  # (성공, 오류메시지없음, 서버응답)

        # 실패(HTTP 200이 아니거나 ok=False) → 서버의 detail/텍스트 노출
        detail = ""
        try:
            detail = data.get("detail", "")
        except Exception:
            detail = r.text
        return False, detail or f"구매 실패 (HTTP {r.status_code})", None

    except requests.exceptions.RequestException as e:
        # 네트워크 오류(연결/타임아웃 등)
        return False, f"서버 통신 오류: {e}", None

# ─────────────────────────────────────────────────────────────────────────────
# 효과 적용 (프론트 표시 전용)
#   - 포인트 변경은 이미 서버에서 반영됨(프론트는 메시지/애니메이션만)
#   - RNG: 보상 금액 안내
#   - 기능형: 쿨다운/게임 상태 변경(프론트 세션 값)
# ─────────────────────────────────────────────────────────────────────────────
def _apply_visual_effect(item_code: str, resp: dict | None):
    # RNG 아이템: 서버가 내려준 보상값 표시
    if item_code == "RNG_BOX_SMALL" or item_code == "RNG_BOX_BIG":
        gain = (resp or {}).get("rng_gain", 0)  # 보상 금액(없으면 0)
        if gain > 0:
            st.balloons()                       # 풍선 애니메이션
            st.success(f"🎁 보상 +{gain}P 지급 완료!")
        else:
            st.info("😵‍💫 꽝! 보상 0P")
        return
"""
    # 기능형 아이템: 프론트 세션 상태 업데이트
    if item_code == "AD_COOLDOWN_RESET":
        st.session_state.last_ad_watch_time = None     # 광고 마지막 시각 초기화
        st.session_state.ad_cooldown_active = False    # 쿨다운 해제
        st.success("✅ 광고 쿨다운이 초기화되었습니다!")
    elif item_code == "GAME_COOLDOWN_SKIP":
        if st.session_state.game_state == "cooldown":
            st.session_state.game_state = "initial"    # 게임 상태 초기화
            st.session_state.game_cooldown_start_time = None
            st.info("🔁 게임 쿨다운을 건너뛰었습니다. 바로 재도전 가능!")
"""
# ─────────────────────────────────────────────────────────────────────────────
# 모달(대화상자) UI
#   - @st.dialog: Streamlit 제공 팝업 컴포넌트
#   - '구매하기' 버튼 클릭 시 이 모달을 띄워 최종 확인
# ─────────────────────────────────────────────────────────────────────────────
@st.dialog("구매 확인")
def confirm_purchase_dialog(item, user_points: int):
    # 구매 정보 요약
    st.write(f"상품: **{item['name']}**")
    st.write(f"가격: **{item['price']}P**")
    st.write(f"보유 포인트: **{user_points}P**")

    # 두 개의 컬럼(확인/취소 버튼)
    c1, c2 = st.columns(2)

    # 왼쪽: "예, 구매" 버튼
    with c1:
        # use_container_width=True : 버튼 너비를 컬럼 너비에 맞춤
        if st.button("예, 구매할게요 ✅", use_container_width=True, key=f"confirm_yes_{item['key']}", disabled=st.session_state.buying):
            # 중복 클릭 방지: 구매 시작 → buying=True
            st.session_state.buying = True
            # 서버로 구매 요청
            ok, err, resp = _purchase(st.session_state.user_id, item["code"], item["name"], item["price"])
            if ok:
                # 시각 효과(메시지/풍선). 포인트는 이미 서버 응답으로 동기화됨
                _apply_visual_effect(item["code"], resp)
                st.success(f"구매 완료! 남은 포인트: {st.session_state.points}P")
            else:
                # 실패 사유 안내
                st.error(err or "구매 실패")
            # 구매 종료 → buying=False
            st.session_state.buying = False
            # 모달 닫고 화면 갱신
            st.rerun()

    # 오른쪽: "취소" 버튼
    with c2:
        if st.button("아니요, 취소", use_container_width=True, key=f"confirm_no_{item['key']}"):
            st.info("구매를 취소했습니다.")

# ─────────────────────────────────────────────────────────────────────────────
# 메인 페이지 함수(엔트리)
#   - 사이드바/라우팅에서 shop_page()를 호출
#   - 세션 초기화 → 로그인 확인 → 포인트 동기화 → 아이템 카드 렌더링
# ─────────────────────────────────────────────────────────────────────────────
def shop_page():
    # 1) 세션 기본값 보장
    _ensure_session_defaults()

    # 2) 제목
    st.title("🛒 아이템 상점")

    # 3) 로그인 여부 확인 (user_id가 비어 있으면 경고)
    if not st.session_state.get("user_id"):
        st.warning("구매하려면 먼저 로그인 해주세요.")
        return  # 로그인 전에는 상점 기능 비활성

    # 4) 페이지 진입 시 서버 포인트 동기화(표시값 신뢰성 ↑)
    _sync_points_from_server(st.session_state.user_id)

    # 5) 현재 보유 포인트 표시
    st.markdown(f"**보유 포인트:** {st.session_state.points}P")

    # (옵션) 공지/정책 안내: 확률형 보상 구조를 설명하고 싶다면 여기에 st.info()로 표기 가능
    # st.info("확률형 보상(랜덤 박스)의 상세 확률은 안내 페이지를 참고하세요.")

    # 6) 아이템 카드(2열) 렌더링
    # 2열 카드 UI
    cols = st.columns(2)
    for idx, item in enumerate(ITEMS):
        with cols[idx % 2]:
            box = st.container(border=True)
            with box:
                img = (item.get("img") or "").strip()
                if img:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c2:
                        st.image(img, width=250)

                st.markdown(
                    f"""
                    <div style="margin-top:8px; text-align: center;">
                        <div style="font-weight:600; font-size:18px; margin-bottom:6px;">{item['name']}</div>
                        <div style="color:#666; font-size:14px; margin-bottom:10px;">{item['desc']}</div>
                        <div style="font-weight:700; margin-bottom:10px;">{item['price']}P</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # --- 버튼 활성/비활성 판정 ---
                sellable = item.get("sellable", True)  # 기본 True(랜덤박스는 구매 가능), 실제상품은 False
                lack_point = st.session_state.points < item["price"]
                buying_now = st.session_state.buying

                # 라벨/비활성 사유 우선순위: 곧 오픈 > 포인트 부족 > 구매 중
                if not sellable:
                    label = "곧 오픈! 잠시만 기다려 주세요"
                    disabled = True
                elif lack_point:
                    label = "포인트 부족"
                    disabled = True
                else:
                    label = "구매하기"
                    disabled = buying_now

                if st.button(label, key=f"buy_{item['key']}", use_container_width=True, disabled=disabled):
                    # 판매 불가(곧 오픈)은 눌러도 아무 작업 안함
                    if not sellable:
                        st.info("이 상품은 곧 오픈됩니다. 조금만 기다려 주세요!")
                    else:
                        # 기존 구매 흐름 유지
                        confirm_purchase_dialog(item, st.session_state.points)

