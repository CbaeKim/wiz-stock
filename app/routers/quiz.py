from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import datetime
import random
import traceback

from app.dependency.connect_supabase import connect_supabase

# --- 라우터 설정 ---
router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)

# --- 요청 모델 ---
class AnswerRequest(BaseModel):
    user_id: str
    quiz_id: int
    user_answer: str
    topic: str
    quiz_index: int
    total_questions: int

# --- API 엔드포인트 ---
@router.get("/check-participation", summary="퀴즈 참여 가능 여부 확인")
def check_participation(user_id: str, db: Client = Depends(connect_supabase)):
    """
    사용자가 오늘 퀴즈에 참여했는지 여부를 확인합니다.
    """
    try:
        user_info_res = db.table('user_info').select('quiz_participation').eq('id', user_id).execute()
        if not user_info_res.data:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
        
        has_participated = user_info_res.data[0].get('quiz_participation', False)
        return {"can_participate": not has_participated}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 참여 여부 확인에 실패했습니다.")
# ---------------------------------

@router.get("/get-by-topic", summary="주제별 퀴즈 가져오기")
def get_quizzes(topic: str, db: Client = Depends(connect_supabase)):
    """
    쿼리 파라미터로 받은 주제(topic)에 해당하는 퀴즈를 DB에서 3개 랜덤으로 가져옵니다.
    """
    try:
        response = db.table('quiz').select("identify_code, question, answer, explanation").eq('sub_category', topic).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="해당 주제의 퀴즈가 없습니다.")
        return random.sample(response.data, 3)
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 퀴즈 데이터를 가져오는 데 실패했습니다.")

@router.post("/submit-answer", summary="퀴즈 답변 제출 및 채점")
def submit_answer(req_body: AnswerRequest, request: Request, db: Client = Depends(connect_supabase)):
    """
    사용자의 답변을 채점하고, 포인트를 지급하며, 모든 관련 로그를 DB에 기록합니다.
    """
    try:
        # 1. 정답 확인 및 포인트 계산
        quiz_info_res = db.table('quiz').select('answer').eq('identify_code', req_body.quiz_id).single().execute()
        correct_answer = quiz_info_res.data['answer']
        is_correct = (req_body.user_answer == correct_answer)
        points_to_add = 5 if is_correct else 2

        # 2. 사용자 정보 조회 (total_point만)
        user_res = db.table("user_info").select("total_point").eq("id", req_body.user_id).single().execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user = user_res.data
        
        # 3. total_point 업데이트
        current_total_point = user.get('total_point') or 0
        new_total_point = current_total_point + points_to_add
        
        db.table("user_info").update({
            "total_point": new_total_point
        }).eq("id", req_body.user_id).execute()

        # 4. point_log 기록
        db.table('point_log').insert({
            "id": req_body.user_id, "category": req_body.topic,
            "point_value": points_to_add, "path": "주식 퀴즈",
            "timestamp": datetime.now().isoformat(), "ip_address": request.client.host
        }).execute()

        # 5. service_log 기록
        log_content = f"퀴즈 {'정답' if is_correct else '오답'} : {points_to_add}포인트 지급"
        db.table('service_log').insert({
            "date": datetime.now().isoformat(), "id": req_body.user_id,
            "ip_address": request.client.host, "category": "포인트 지급",
            "path": "주식 퀴즈", "content": log_content
        }).execute()

        # 6. 마지막 문제일 경우 참여 상태 업데이트
        is_last_question = (req_body.quiz_index == req_body.total_questions - 1)
        if is_last_question:
            db.table('user_info').update({'quiz_participation': True}).eq('id', req_body.user_id).execute()
        
        return {"is_correct": is_correct, "points_awarded": points_to_add}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 답변을 처리하는 데 실패했습니다.")