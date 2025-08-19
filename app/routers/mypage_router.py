from fastapi import APIRouter, Depends
from supabase import Client
from app.dependency.connect_supabase import connect_supabase

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
    """ User information transform JSON and return JSON """
    try:
        # Get table 'user_info'
        response = db.from_("user_info").select(
            "id, nickname, nickname_color, total_point, daily_point_bonus, "
            "my_trophies, purchased_indicators, "
            "contact, email, attendance, continuous_attendance, last_attendance_date"
        ).eq("id", user_id).execute()

        
        if not response.data:
            return {"message": "UserNotFound"}
        
        # Extract first row in variable
        user_data = response.data[0]

        # if column is 'None', set default value
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

        return user_data

    except Exception as e:
        return {"message": "Error", "detail": str(e)}