# app/routers/shop_router.py
# ─────────────────────────────────────────────────────────────────────────────
# 목적:
#   - "상점(Shop)" 관련 백엔드 API 라우터
#   - 구매 시 포인트를 먼저 차감하고, 랜덤 보상(RNG)이 있는 상품이면
#     서버가 직접 보상을 계산/지급한 뒤 총 포인트를 돌려줌
#   - 포인트 내역(point_log)도 함께 기록
#
# 전제(사용 중인 테이블/컬럼):
#   user_info(id, total_point)          : 유저의 현재 보유 포인트를 저장
#   point_log(timestamp, id, category, point_value, path, ip_address)
#     - id         : 유저 ID (user_info.id와 같은 값)
#     - point_value: 증가(+)/감소(-) 포인트
#     - path       : "purchase/..." 또는 "reward/..." 등 이벤트 구분용 문자열
#     - category   : "shop" 고정
#     - timestamp  : ISO-8601(UTC) 문자열
#     - ip_address : 요청한 클라이언트의 IP
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, Depends, Request  # FastAPI 라우팅/에러/DI/요청객체
from pydantic import BaseModel                                 # 요청 바디 검증용 모델
from app.dependency.connect_supabase import connect_supabase   # Supabase 커넥션 함수
from supabase import Client                                    # Supabase 클라이언트 타입
from datetime import datetime, timezone                        # 시간(UTC) 처리
import random                                                  # RNG(랜덤) 추첨

# 라우터 인스턴스 생성
#  - prefix="/shop"  : 이 파일의 모든 엔드포인트는 /shop/... 경로가 됨
#  - tags=["shop"]   : 문서화(Swagger)에서 "shop" 그룹으로 묶임
router = APIRouter(prefix="/shop", tags=["shop"])

# ─────────────────────────────────────────────────────────────────────────────
# 서버 신뢰 가격표(PRICING) 프론트에서 사용하는 금액이 백엔드에서 사용하는 금액과 같은지
#  - 프론트가 보내는 price는 "검증용"으로만 사용
#  - 최종 가격은 항상 서버의 이 표를 기준으로 판단(조작 방지)
#  - 프론트의 ITEM 가격과 반드시 동일해야 함 (다르면 "가격 검증 실패")
# ─────────────────────────────────────────────────────────────────────────────
PRICING = {
    "AD_COOLDOWN_RESET": 1,   # 광고 쿨다운 초기화
    "GAME_COOLDOWN_SKIP": 5,  # 게임 재도전 패스
    "RNG_BOX_SMALL": 20,      # 랜덤 박스 (소)
    "RNG_BOX_BIG": 50,        # 랜덤 박스 (대)
    "COFFEE_AMERICANO": 180,  # 아메리카노
    "COFFEE_LATTE": 200,      # 카페라떼
    "ICECREAM_CONE" : 150,    # 콘 아이스크림
    "SANDWICH_BASIC" : 250,   # 샌드위치
}

# ─────────────────────────────────────────────────────────────────────────────
# RNG(랜덤 보상) 테이블
#  - 각 아이템 코드에 대해 (보상값, 확률)의 리스트 5개(총 5티어)
#  - 정책(요구사항):
#      1) 꽝(0P)은 25% 이하
#      2) 3번째 티어의 보상값은 "구매가(=PRICE)"와 정확히 동일
#      3) 4/5번째 티어는 구매가보다 커야 함(초과 보상)
#      4) 전체 확률의 합은 1.0
#  - 현재 테이블은 "소비성(기대값 < 가격)"을 만족
# ─────────────────────────────────────────────────────────────────────────────
RNG_TABLE = {
    # 소(20P): [(보상, 확률)...] 5개
    # 합계: 0.24 + 0.155 + 0.40 + 0.20 + 0.005 = 1.0
    "RNG_BOX_SMALL": [
        (0,   0.24),   # 1) 꽝: 24% (<= 25%)
        (8,   0.155),  # 2) 저보상: 가격보다 작은 보상
        (20,  0.40),   # 3) 동가: 반드시 = 가격(20)
        (25,  0.20),   # 4) 고보상: 가격 초과
        (100, 0.005),  # 5) 대박: 매우 낮은 확률
    ],
    # 대(50P): 합계 동일하게 1.0
    "RNG_BOX_BIG": [
        (0,    0.24),
        (20,   0.155),
        (50,   0.40),  # 3) 동가: 반드시 = 가격(50)
        (65,   0.20),
        (250,  0.005),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# 요청 바디 모델(구매)
#  - user_id   : 유저 식별자 (user_info.id와 동일 값)
#  - item_code : 아이템 코드 (PRICING/RNG_TABLE 키와 일치)
#  - item_name : UI 표시용 이름 (서버 검증엔 사용하지 않음)
#  - price     : 프론트 표시 가격(검증용). 서버 PRICING과 일치해야 함
# ─────────────────────────────────────────────────────────────────────────────
class PurchaseBody(BaseModel):
    user_id: str
    item_code: str
    item_name: str
    price: int

# ─────────────────────────────────────────────────────────────────────────────
# 유틸: 현재 UTC 시각을 ISO-8601 문자열로 반환 (예: "2025-08-20T12:34:56.789012+00:00")
#  - DB에 저장할 timestamp로 사용
# ─────────────────────────────────────────────────────────────────────────────
def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

# ─────────────────────────────────────────────────────────────────────────────
# 유틸: RNG 테이블에서 "한 번" 추첨하여 보상값을 결정
#  - table: [(보상값, 확률), ...] 리스트 (확률의 합=1)
#  - 동작:
#      1) 0~1 사이의 난수 r 생성
#      2) 테이블을 순회하며 누적확률(acc)에 더함
#      3) r <= acc가 되는 지점의 "보상값"을 반환
#      4) 혹시 오차로 끝까지 못 찾으면 마지막 값을 반환(방어코드)
# ─────────────────────────────────────────────────────────────────────────────
def _rng_draw(table):
    r, acc = random.random(), 0.0  # r: 0~1 사이 난수, acc: 누적확률
    for val, p in table:           # 각 항목(보상값, 확률)을 순서대로 읽음
        acc += p                   # 누적확률에 현재 확률을 더함
        if r <= acc:               # 난수가 누적확률 이하가 되는 순간 당첨
            return val             # 해당 보상값을 반환
    return table[-1][0]            # 방어: 마지막 보상값 반환

# ─────────────────────────────────────────────────────────────────────────────
# POST /shop/purchase
#  - 아이템 구매(포인트 차감) + (해당 시) RNG 보상 지급
#  - 응답: {"ok": True, "total_point": 최종포인트, "rng_gain": 보상값(없으면 0)}
#  - @router.post("/purchase"): 프론트 엔드의 요청(HTTP POST 요청)과 Fast API(/shop/purchase 경로) 연결
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/purchase")
def purchase(body: PurchaseBody, request: Request, db: Client = Depends(connect_supabase)) -> dict:
    # (0) 입력 정리/가격 검증 ---------------------------------------------------
    uid = (body.user_id or "").strip()         # 공백 제거
    if not uid:                                 # 빈 값이면 요청 자체가 잘못됨
        raise HTTPException(status_code=422, detail="user_id is required")

    code = body.item_code                       # 아이템 코드
    if code not in PRICING:                     # 서버 가격표 딕셔너리에 이 코드가 없으면 400
        raise HTTPException(status_code=400, detail="유효하지 않은 아이템 코드입니다.")

    server_price = PRICING[code]                # 서버 기준 가격(신뢰 소스)
    if body.price != server_price:              # 프론트가 보낸 가격과 다르면 실패(조작 방지)
        raise HTTPException(status_code=400, detail="가격 검증 실패")



    # (1) 유저 현재 포인트 조회 -----------------------------------------------
    res = db.table("user_info").select("total_point").eq("id", uid).single().execute()
    if not res.data:                            # 유저가 없으면 404
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")
    current = (res.data.get("total_point") or 0)  # 현재 유저가 보유한 총 포인트 출력, None이면 0으로 처리

    # (2) 잔액 검증 -------------------------------------------------------------
    #  - 보유 포인트 < 가격이면 구매 불가
    if current < server_price:
        raise HTTPException(status_code=400, detail="포인트가 부족합니다.")

# 포인트 차감(소비) 확정 + 로그(-)

    # (3) AD_COOLDOWN_RESET(광고 시청후 대기시간 생략) / GAME_COOLDOWN_SKIP (게임 재시작 시간 생략)처럼 포인트 차감만 할 경우------
    #  실제 기능(쿨다운 초기화 등)은 프론트에서 상태를 갱신
    after_purchase = current - server_price     # 차감 후 포인트 계산
    # 3-1) 유저 포인트 업데이트
    db.table("user_info").update({"total_point": after_purchase}).eq("id", uid).execute()

    # 3-2) 포인트 로그: 차감 기록 (실패해도 결제를 롤백하지 않도록 try/except)
    try:
        db.table("point_log").insert({
            "timestamp": _utcnow(),             # UTC ISO 문자열
            "id": uid,                          # 유저 식별자
            "category": "shop",                 # 카테고리(고정)
            "point_value": -server_price,       # 음수(차감)
            "path": f"purchase/{code}",         # 이벤트 경로(분석용)
            "ip_address": request.client.host   # 요청 IP
        }).execute()
    except Exception as e:
        # 로그가 실패해도 결제 자체는 유효해야 하므로 에러를 삼킴(운영 로그로 남기는 걸 권장)
        print("[point_log insert error - purchase]", e)

    # (4) 랜덤 박스를 구매할 경우 (RNG_TABLE이 있을경우 포인트 차감후 적용하여 포인트 제공)----------------------------------------
    rng_gain = 0                                # 랜덤 보상 기본값 0
    total_after_effect = after_purchase         # 최종 포인트 초기값(차감만 반영된 상태)

    #  - RNG(랜덤 박스) 아이템이면 서버가 직접 추첨/지급
    if code in RNG_TABLE:
        rng_gain = _rng_draw(RNG_TABLE[code])   # 테이블 기반 1회 추첨
        if rng_gain > 0:                        # 보상이 0보다 크면 포인트 추가 지급
            total_after_effect = after_purchase + rng_gain

            # 4-1) 유저 포인트 업데이트(보상 반영)
            db.table("user_info").update({"total_point": total_after_effect}).eq("id", uid).execute()

            # 4-2) 포인트 로그: 보상 기록(양수). 실패해도 결제는 유지
            try:
                db.table("point_log").insert({
                    "timestamp": _utcnow(),
                    "id": uid,
                    "category": "shop",
                    "point_value": rng_gain,        # 양수(지급)
                    "path": f"reward/{code}",       # 이벤트 경로(보상)
                    "ip_address": request.client.host
                }).execute()
            except Exception as e:
                print("[point_log insert error - reward]", e)

    # (5) 최종 응답 -------------------------------------------------------------
    #  - 프론트는 total_point만 화면에 반영(프론트에서 직접 더하지 않음)
    return {
        "ok": True,                       # 성공 플래그
        "total_point": total_after_effect, # 서버 기준 최종 포인트(차감+보상 포함)
        "rng_gain": rng_gain              # RNG 보상값(없으면 0)
    }
