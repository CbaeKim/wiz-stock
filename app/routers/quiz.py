# app/routers/quiz.py

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import datetime 
import random
import traceback

# --- ✨ 프로젝트의 다른 파일에서 Supabase 연결 함수를 가져옵니다 ---
from app.dependency.connect_supabase import connect_supabase

# --- 라우터(Router) 설정 ---
router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)

# --- 요청 본문(Request Body) 모델 정의 ---
class AnswerRequest(BaseModel):
    user_id: str
    quiz_id: int
    user_answer: str
    topic: str
    # 마지막 문제인지 확인하기 위해 quiz_index와 total_questions를 추가합니다.
    quiz_index: int
    total_questions: int

# --- API 엔드포인트(Endpoint) 정의 ---

@router.get("/check-participation", summary="퀴즈 참여 가능 여부 확인")
def check_participation(user_id: str, db: Client = Depends(connect_supabase)):
    """
    사용자가 오늘 퀴즈에 참여했는지 여부를 확인합니다.
    user_info 테이블의 quiz_participation 컬럼 값을 기반으로 판단합니다.
    """
    try:
        # 'user_info' 테이블에서 해당 사용자의 'quiz_participation' 값을 조회합니다.
        user_info_res = db.table('user_info').select('quiz_participation').eq('id', user_id).execute()
        if not user_info_res.data:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
        
        # quiz_participation 값을 가져옵니다. 값이 없으면 기본값으로 False를 사용합니다.
        has_participated = user_info_res.data[0].get('quiz_participation', False)
        
        # 참여했다면(True), 참여 가능 여부(can_participate)는 False가 됩니다.
        # 참여 안했다면(False), 참여 가능 여부(can_participate)는 True가 됩니다.
        return {"can_participate": not has_participated}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 참여 여부 확인에 실패했습니다.")


@router.get("/get-by-topic", summary="주제별 퀴즈 가져오기")
def get_quizzes(topic: str, db: Client = Depends(connect_supabase)):
    """
    쿼리 파라미터로 받은 주제(topic)에 해당하는 퀴즈를 DB에서 3개 랜덤으로 가져옵니다.
    """
    try:
        # Supabase의 'quiz' 테이블에서 필요한 컬럼들을 조회합니다.
        response = db.table('quiz').select("identify_code, question, answer, explanation").eq('sub_category', topic).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="해당 주제의 퀴즈가 없습니다.")
        
        # 조회된 퀴즈 중에서 랜덤으로 3개를 뽑아 반환합니다.
        return random.sample(response.data, 3)
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 퀴즈 데이터를 가져오는 데 실패했습니다.")

@router.post("/submit-answer", summary="퀴즈 답변 제출 및 채점")
def submit_answer(req_body: AnswerRequest, request: Request, db: Client = Depends(connect_supabase)):
    """
    사용자가 제출한 답변을 채점하고, 포인트를 지급하며, 관련 로그를 DB에 기록합니다.
    마지막 문제일 경우, quiz_participation 상태를 True로 업데이트합니다.
    """
    try:
        # 1. 정답 확인 및 포인트 계산
        quiz_info_res = db.table('quiz').select('answer').eq('identify_code', req_body.quiz_id).single().execute()
        correct_answer = quiz_info_res.data['answer']
        is_correct = (req_body.user_answer == correct_answer)
        points_to_add = 5 if is_correct else 2

        # 2. 사용자 포인트 업데이트
        user_info_res = db.table('user_info').select('total_point').eq('id', req_body.user_id).execute()
        if not user_info_res.data:
            raise HTTPException(status_code=404, detail=f"User '{req_body.user_id}' not found.")
        
        current_points = user_info_res.data[0].get('total_point') or 0
        new_total_points = current_points + points_to_add
        db.table('user_info').update({'total_point': new_total_points}).eq('id', req_body.user_id).execute()

        # 3. 포인트 획득 로그 기록
        db.table('point_log').insert({
            "id": req_body.user_id, "category": req_body.topic,
            "point_value": points_to_add, "path": "주식 퀴즈",
            "timestamp": datetime.now().isoformat(), "ip_address": request.client.host
        }).execute()

        # 4. 마지막 문제인지 확인하고, 상태 업데이트
        is_last_question = (req_body.quiz_index == req_body.total_questions - 1)
        if is_last_question:
            # 마지막 문제가 맞으면, quiz_participation을 True로 변경하여 오늘 더 이상 참여할 수 없도록 합니다.
            db.table('user_info').update({'quiz_participation': True}).eq('id', req_body.user_id).execute()
        
        # 프론트엔드에 채점 결과와 획득 포인트를 반환합니다.
        return {"is_correct": is_correct, "points_awarded": points_to_add}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 답변을 처리하는 데 실패했습니다.")
