# FastAPI에서 라우터(경로)를 만들 때 사용하는 도구들 불러오기
# APIRouter: /mypage 같은 경로 그룹을 만들 때 사용
# Depends: 의존성 주입(특정 함수의 리턴값을 자동으로 받아서 쓰는 기능)
from fastapi import APIRouter, Depends

# Supabase 파이썬 클라이언트의 타입 힌트(형태)로 사용할 Client 불러오기
# 이 Client를 통해 데이터베이스 쿼리(읽기/쓰기)를 할 수 있음
from supabase import Client

# "Supabase 연결 함수"를 불러오기
# connect_supabase()는 내부에 "URL/KEY 설정 → Client 생성" 로직이 들어 있고
# FastAPI가 이 함수를 실행해서 DB 연결 객체(Client)를 주입(Depends)해 줌
from app.dependency.connect_supabase import connect_supabase


# ────────────────────────────────────────────────────────────────────────
# 라우터 생성
# ────────────────────────────────────────────────────────────────────────
router = APIRouter(
    prefix="/mypage",           # 이 파일의 모든 경로 앞에 "/mypage"가 붙음
    tags=["mypage"]             # Swagger UI에서 이 라우터를 'mypage' 그룹으로 묶어 보여줌
)

# ────────────────────────────────────────────────────────────────────────
# [GET] /mypage/{user_id}
# - {user_id}는 URL에서 변수로 받는 부분 (예: /mypage/qwer)
# - 목적: Supabase의 user_info 테이블에서 해당 유저의 정보를 가져와 JSON으로 반환
# - 반환 예: {"id": "qwer", "name": "...", "total_point": 10, ...}
# ────────────────────────────────────────────────────────────────────────
@router.get("/{user_id}")
async def get_mypage_data(
    user_id: str,                           # URL 경로에서 받은 사용자 ID (문자열)
    db: Client = Depends(connect_supabase)  # 의존성 주입: DB 연결 객체(Supabase Client)
):
    try:
        # ────────────────────────────────────────────────────────────────────────
        # 1) Supabase 테이블 질의 (쿼리)
        # - from_("user_info"): user_info 테이블에서
        # - select("..."): 아래 나열한 컬럼들만 가져오기 (불필요한 데이터 과다 전송 방지)
        # - eq("id", user_id): id 컬럼이 user_id와 "같은" 행만 선택(필터링)
        # - execute(): 실제로 쿼리를 실행하고 결과를 받음
        #   → response.data 형태로 리스트([{컬럼:값, ...}])가 들어옴
        # ────────────────────────────────────────────────────────────────────────
        response = db.from_("user_info").select(
            "id, name, nickname_color, total_point, daily_point_bonus, "
            "my_trophies, purchased_indicators, "
            "contact, email, attendance, continuous_attendance, last_attendance_date"
        ).eq("id", user_id).execute()

        # ────────────────────────────────────────────────────────────────────────
        # 2) 결과가 비어있을 때 처리
        # - 조회 결과가 없으면 response.data는 빈 리스트([])
        # - JSON으로 "UserNotFound" 메시지 반환
        # ────────────────────────────────────────────────────────────────────────
        if not response.data:
            return {"message": "UserNotFound"}
        
        # ────────────────────────────────────────────────────────────────────────
        # 3) 조회된 데이터에서 첫 번째 행만 사용(중복 방지)
        # - eq("id", ...)로 ID 1개를 찾았으므로, 결과는 보통 1행
        # - Supabase 파이썬 클라이언트는 리스트로 감싸서 반환 → [0]으로 꺼냄
        # - user_data는 파이썬 딕셔너리 형태: {"id": "...", "name": "...", ...}
        # ────────────────────────────────────────────────────────────────────────
        user_data = response.data[0]

        # ────────────────────────────────────────────────────────────────────────
        # 4) None(값 없음) 대비 기본값 세팅
        # - 이유: 프론트(예: Streamlit)에서 None 처리 로직을 줄이고,
        #         바로 화면에 뿌려도 깔끔히 보이도록 하기 위함
        # - .get("키")가 None이면 우리가 원하는 기본값으로 덮어씀
        # - 숫자 계열은 0, 문자열은 "미등록"/"기록 없음", 리스트는 [] 권장
        # ────────────────────────────────────────────────────────────────────────
        if user_data.get("contact") is None:
            user_data["contact"] = "미등록"                    # 연락처 기본값
        if user_data.get("email") is None:
            user_data["email"] = "미등록"                      # 이메일 기본값        
        
        if user_data.get("total_point") is None:
            user_data["total_point"] = 0                      # 포인트 기본값 0
        if user_data.get("daily_point_bonus") is None:
            user_data["daily_point_bonus"] = 0                # 보너스 기본값 0

        if user_data.get("attendance") is None:
            user_data["attendance"] = 0                       # 출석일수 기본값 0
        if user_data.get("continuous_attendance") is None:
            user_data["continuous_attendance"] = 0            # 연속 출석일 기본값 0
        if user_data.get("last_attendance_date") is None:
            user_data["last_attendance_date"] = "기록 없음"    # 마지막 출석일 기본값

        if user_data.get("my_trophies") is None:
            user_data["my_trophies"] = []                     # 훈장 기본값 빈 리스트
        if user_data.get("purchased_indicators") is None:
            user_data["purchased_indicators"] = []            # 보조지표 기본값 빈 리스트

        # ────────────────────────────────────────────────────────────────────────
        # 5) 최종 반환
        # - FastAPI는 파이썬 딕셔너리를 자동으로 JSON으로 변환하여 응답함
        # - 상태코드 200(기본)을 함께 보냄
        # ────────────────────────────────────────────────────────────────────────
        return user_data

    # ────────────────────────────────────────────────────────────────────────
    # 예외(에러) 처리
    # - DB 연결 문제, 쿼리 오류 등 모든 예외를 잡아
    #   구조화된 JSON으로 반환 (프론트에서 에러 메시지 파싱 용이)
    # - "message": "Error"  : 에러임을 나타내는 고정 키, ⚠️​ 프론트에서 요청 성공, 실패 기준
    # - "detail": str(e)    : 실제 예외 메시지(디버깅용)
    # ────────────────────────────────────────────────────────────────────────
    except Exception as e:
        return {"message": "Error", "detail": str(e)}