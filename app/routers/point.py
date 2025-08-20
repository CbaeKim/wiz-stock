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
    사용자의 포인트를 업데이트하고 로그를 기록하는 핵심 로직입니다.
    - daily_point_bonus의 일일 한도(20점)를 확인하여 적용합니다.
    """
    try:
        # 1. user_info 테이블에서 현재 총 포인트와 일일 보너스 포인트를 조회
        user_res = db.table("user_info").select("total_point, daily_point_bonus").eq("id", user_id).single().execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user = user_res.data
        
        # 2. 오늘 추가로 받을 수 있는 보너스 포인트(daily_point_bonus)를 계산 (일일 한도 20점 - 이미 받은 점수)
        current_daily_bonus = user.get('daily_point_bonus') or 0
        available_bonus_space = DAILY_POINT_LIMIT - current_daily_bonus
        
        # 실제 daily_point_bonus에 추가될 점수를 계산(획득할 포인트와 남은 공간 중 더 작은 값)
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

        # 4. point_log 테이블에 포인트 획득 기록을 남깁니다.
        db.table("point_log").insert({
            "id": user_id, 
            "category": category,
            "point_value": points_to_add, 
            "path": path,
            "timestamp": datetime.now().isoformat(), 
            "ip_address": ip_address
        }).execute()
        
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
    - 하루에 한 번만 참여 가능합니다.
    - 7일 연속 출석 시 보너스 포인트를 지급합니다.
    """
    today = date.today()
    # 필요한 모든 사용자 정보를 한 번에 조회
    user_res = db.table("user_info").select("last_attendance_date, consecutive_days, attendance_participate").eq("id", request_body.user_id).single().execute()
    if not user_res.data: raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    user = user_res.data

    # 오늘 이미 참여했는지 확인
    if user.get('attendance_participate') is True: 
        raise HTTPException(status_code=400, detail="오늘은 이미 출석체크를 완료했습니다.")
    
    # 마지막 출석일을 기준으로 연속 출석일을 계산
    last_attendance = date.fromisoformat(user['last_attendance_date']) if user.get('last_attendance_date') else None
    new_consecutive = (user.get('consecutive_days') or 0) + 1 if last_attendance == (today - timedelta(days=1)) else 1
    
    points_to_add = ATTENDANCE_POINTS
    bonus_message = ""
    final_consecutive = new_consecutive
    
    # 7일 연속 출석 시 보너스 지급 및 연속 출석일 초기화
    if new_consecutive == 7:
        points_to_add += ATTENDANCE_BONUS_POINTS
        final_consecutive = 0 # 7일 보상 후 0으로 초기화
        bonus_message = f"7일 연속 출석! 보너스 {ATTENDANCE_BONUS_POINTS}포인트 획득!"

    # 중앙 포인트 처리 함수를 호출하여 포인트 업데이트 및 로그 기록
    new_total_point = _process_point_update(db, request_body.user_id, points_to_add, "출석체크", "포인트 센터", http_request.client.host)
    
    # 출석 관련 정보를 DB에 업데이트
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
    # 참여 횟수가 제한(3회)을 넘었는지 확인
    if participation_count >= AD_PARTICIPATION_LIMIT:
        raise HTTPException(status_code=400, detail="오늘은 더 이상 광고에 참여할 수 없습니다.")

    # 중앙 포인트 처리 함수 호출
    new_total = _process_point_update(db, request_body.user_id, AD_WATCH_POINTS, "광고시청", "포인트 센터", http_request.client.host)
    
    # 광고 참여 횟수를 1 증가시켜 DB에 업데이트
    db.table("user_info").update({"ad_participation": participation_count + 1}).eq("id", request_body.user_id).execute()
    
    return {"message": "포인트가 적립되었습니다.", "total_point": new_total, "new_ad_count": participation_count + 1}

@router.post("/game-result", summary="숫자 게임 결과 처리")
def process_game_result(request_body: GameResultRequest, http_request: Request, db: Client = Depends(connect_supabase)):
    """
    숫자 게임의 승패 결과를 기록하고, 승리 시 포인트를 지급합니다.
    - 하루에 한 번만 참여 가능합니다.
    """
    user_res = db.table("user_info").select("dailygame_participate").eq("id", request_body.user_id).single().execute()
    if not user_res.data: raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user_res.data.get('dailygame_participate') is True: raise HTTPException(status_code=400, detail="오늘은 이미 게임에 참여했습니다.")

    # 게임에 참여했으므로, 승패와 상관없이 참여 상태를 True로 변경
    db.table("user_info").update({"dailygame_participate": True}).eq("id", request_body.user_id).execute()

    # 게임에서 이겼을 경우에만 포인트를 지급
    if request_body.won:
        new_total_point = _process_point_update(db, request_body.user_id, GAME_WIN_POINTS, "숫자게임", "포인트 센터", http_request.client.host)
        return {"message": f"게임 승리! {GAME_WIN_POINTS}포인트 획득!", "total_point": new_total_point}
    else:
        # 졌을 경우에는 참여 기록만 남기고 종료
        return {"message": "게임 참여가 기록되었습니다."}

@router.get("/{user_id}/status", summary="사용자 상태 정보 조회")
def get_user_status(user_id: str, db: Client = Depends(connect_supabase)):
    """
    포인트 센터에 필요한 사용자의 모든 상태 정보를 조회합니다.
    (총 포인트, 연속 출석일, 활동별 참여 여부/횟수 등)
    """
    try:
        # user_info 테이블에서 프론트엔드에 필요한 모든 컬럼을 한 번에 조회
        response = db.table("user_info").select(
            "total_point", "consecutive_days", "ad_participation", "attendance_participate", "dailygame_participate"
        ).eq("id", user_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return response.data
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 서버 오류가 발생했습니다.")