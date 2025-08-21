from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import date, timedelta, datetime
import traceback

from app.dependency.connect_supabase import connect_supabase

# --- 상수 정의 ---
ATTENDANCE_POINTS = 1          # 기본 출석 포인트
ATTENDANCE_BONUS_POINTS = 10   # 7일 연속 출석 보너스 포인트
AD_WATCH_POINTS = 5            # 광고 시청 포인트
GAME_WIN_POINTS = 10           # 숫자 게임 승리 포인트
DAILY_POINT_LIMIT = 20         # 일일 획득 가능한 보너스 포인트 한도
AD_PARTICIPATION_LIMIT = 3     # 일일 광고 참여 가능 횟수

# API 라우터를 생성
router = APIRouter(
    prefix="/point",
    tags=["point"],
)

# --- 요청 본문(Request Body) 모델 정의 ---
class UserIdRequest(BaseModel):
    user_id: str

class GameResultRequest(BaseModel):
    user_id: str
    won: bool

# --- 중앙 포인트 처리 함수 ---
def _process_point_update(db: Client, user_id: str, points_to_add: int, category: str, path: str, ip_address: str):
    """
    [내부 함수] 사용자의 포인트를 업데이트하고 모든 관련 로그를 기록하는 핵심 로직입니다.
    이 함수는 외부에서 직접 호출되지 않고, 다른 API 함수들을 통해 호출되어 코드 중복을 방지합니다.
    - daily_point_bonus의 일일 한도(20점)를 확인하여 적용합니다.
    - point_log 테이블에 포인트 거래 기록을 남깁니다.
    - service_log 테이블에 활동 서비스 기록을 남깁니다.
    """
    try:
        # 1. user_info 테이블에서 현재 총 포인트와 일일 보너스 포인트를 조회
        user_res = db.table("user_info").select("total_point, daily_point_bonus").eq("id", user_id).single().execute()
        if not user_res.data:
            # 사용자를 찾을 수 없으면 404 에러를 발생시킵니다.
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user = user_res.data
        
        # 2. 오늘 추가로 받을 수 있는 보너스 포인트(daily_point_bonus)를 계산
        current_daily_bonus = user.get('daily_point_bonus') or 0
        available_bonus_space = DAILY_POINT_LIMIT - current_daily_bonus
        
        # 실제 daily_point_bonus에 추가될 점수를 계산
        points_for_daily_bonus = 0
        if available_bonus_space > 0:
            points_for_daily_bonus = min(points_to_add, available_bonus_space)

        # 3. 사용자의 total_point와 daily_point_bonus를 업데이트
        current_total_point = user.get('total_point') or 0
        new_total_point = current_total_point + points_to_add
        new_daily_bonus = current_daily_bonus + points_for_daily_bonus
        
        db.table("user_info").update({
            "total_point": new_total_point,
            "daily_point_bonus": new_daily_bonus
        }).eq("id", user_id).execute()

        # 4. point_log 테이블에 포인트 획득 상세 기록을 남김
        db.table("point_log").insert({
            "id": user_id, 
            "category": category,
            "point_value": points_to_add, 
            "path": path,
            "timestamp": datetime.now().isoformat(), 
            "ip_address": ip_address
        }).execute()
        
        # 5. service_log 테이블에 서비스 활동 기록을 남김
        log_content = f"{category} : {points_to_add}포인트 지급"
        db.table("service_log").insert({
            "date": datetime.now().isoformat(),
            "id": user_id,
            "ip_address": ip_address,
            "category": category,
            "path": path,
            "content": log_content
        }).execute()
        
        # 업데이트된 총 포인트를 반환
        return new_total_point
    except Exception:
        # 데이터베이스 작업 중 에러가 발생하면 서버 로그에 기록하고 500 에러를 반환
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="포인트 업데이트 중 서버 오류가 발생했습니다.")

# --- API 엔드포인트 ---
@router.post("/attendance", summary="출석 체크 처리")
def check_attendance(request_body: UserIdRequest, http_request: Request, db: Client = Depends(connect_supabase)):
    """
    사용자의 출석을 기록하고 포인트를 지급합니다.
    - 하루에 한 번만 참여 가능합니다. (attendance_participate 컬럼 확인)
    - 7일 연속 출석 시 보너스 포인트를 지급합니다.
    """
    today = date.today()
    user_res = db.table("user_info").select("last_attendance_date, consecutive_days, attendance_participate").eq("id", request_body.user_id).single().execute()
    if not user_res.data: raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    user = user_res.data

    if user.get('attendance_participate') is True: 
        raise HTTPException(status_code=400, detail="오늘은 이미 출석체크를 완료했습니다.")
    
    last_attendance = date.fromisoformat(user['last_attendance_date']) if user.get('last_attendance_date') else None
    new_consecutive = (user.get('consecutive_days') or 0) + 1 if last_attendance == (today - timedelta(days=1)) else 1
    
    points_to_add = ATTENDANCE_POINTS
    bonus_message = ""
    final_consecutive = new_consecutive
    
    if new_consecutive == 7:
        points_to_add += ATTENDANCE_BONUS_POINTS
        final_consecutive = 0
        bonus_message = f"7일 연속 출석! 보너스 {ATTENDANCE_BONUS_POINTS}포인트 획득!"

    new_total_point = _process_point_update(db, request_body.user_id, points_to_add, "출석체크", "포인트 센터", http_request.client.host)
    
    db.table("user_info").update({
        "last_attendance_date": today.isoformat(), "consecutive_days": final_consecutive, "attendance_participate": True
    }).eq("id", request_body.user_id).execute()
    
    return {"message": "출석체크 완료!", "total_point": new_total_point, "consecutive_days": final_consecutive, "bonus_message": bonus_message}

@router.post("/gain/ad", summary="광고 시청 포인트 획득")
def gain_points_for_ad(request_body: UserIdRequest, http_request: Request, db: Client = Depends(connect_supabase)):
    """
    광고 시청에 대한 포인트를 지급합니다.
    - 하루 참여 횟수가 3회로 제한됩니다. (ad_participation 컬럼 확인)
    """
    user_res = db.table("user_info").select("ad_participation").eq("id", request_body.user_id).single().execute()
    if not user_res.data: raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    participation_count = user_res.data.get('ad_participation') or 0
    if participation_count >= AD_PARTICIPATION_LIMIT:
        raise HTTPException(status_code=400, detail="오늘은 더 이상 광고에 참여할 수 없습니다.")

    new_total = _process_point_update(db, request_body.user_id, AD_WATCH_POINTS, "광고시청", "포인트 센터", http_request.client.host)
    
    db.table("user_info").update({"ad_participation": participation_count + 1}).eq("id", request_body.user_id).execute()
    
    return {"message": "포인트가 적립되었습니다.", "total_point": new_total, "new_ad_count": participation_count + 1}

@router.post("/game-result", summary="숫자 게임 결과 처리")
def process_game_result(request_body: GameResultRequest, http_request: Request, db: Client = Depends(connect_supabase)):
    """
    숫자 게임의 승패 결과를 기록하고, 승리 시 포인트를 지급합니다.
    - 하루에 한 번만 참여 가능합니다. (dailygame_participate 컬럼 확인)
    """
    user_res = db.table("user_info").select("dailygame_participate").eq("id", request_body.user_id).single().execute()
    if not user_res.data: raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user_res.data.get('dailygame_participate') is True: raise HTTPException(status_code=400, detail="오늘은 이미 게임에 참여했습니다.")

    db.table("user_info").update({"dailygame_participate": True}).eq("id", request_body.user_id).execute()

    if request_body.won:
        new_total_point = _process_point_update(db, request_body.user_id, GAME_WIN_POINTS, "숫자게임", "포인트 센터", http_request.client.host)
        return {"message": f"게임 승리! {GAME_WIN_POINTS}포인트 획득!", "total_point": new_total_point}
    else:
        return {"message": "게임 참여가 기록되었습니다."}

@router.get("/{user_id}/status", summary="사용자 상태 정보 조회")
def get_user_status(user_id: str, db: Client = Depends(connect_supabase)):
    """
    포인트 센터에 필요한 사용자의 모든 상태 정보를 조회합니다.
    (총 포인트, 연속 출석일, 활동별 참여 여부/횟수 등)
    """
    try:
        response = db.table("user_info").select(
            "total_point", "consecutive_days", "ad_participation", "attendance_participate", "dailygame_participate"
        ).eq("id", user_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return response.data
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 서버 오류가 발생했습니다.")