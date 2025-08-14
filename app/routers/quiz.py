from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import datetime
import random
import traceback 
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

# --- API 엔드포인트(Endpoint) 정의 ---
@router.get("/get-by-topic", summary="주제별 퀴즈 가져오기")
def get_quizzes(topic: str, db: Client = Depends(connect_supabase)):
    """
    쿼리 파라미터로 받은 주제(topic)에 해당하는 퀴즈를 DB에서 3개 랜덤으로 가져옵니다.
    """
    try:
        # Supabase의 'quiz' 테이블에서 필요한 컬럼들을 조회합니다.
        # .eq('sub_category', topic)는 'sub_category' 컬럼 값이 topic 변수와 같은 행만 필터링합니다.
        response = db.table('quiz').select("identify_code, question, answer, explanation").eq('sub_category', topic).execute()
        
        # 조회된 데이터가 없으면 404 에러를 발생시킵니다.
        if not response.data:
            raise HTTPException(status_code=404, detail="해당 주제의 퀴즈가 없습니다.")
        
        # 조회된 퀴즈 중에서 랜덤으로 3개를 뽑아 반환합니다.
        return random.sample(response.data, 3)
    
    except Exception:
        # 예상치 못한 에러가 발생하면, 서버 터미널에 상세 오류를 출력합니다.
        traceback.print_exc()
        # 클라이언트(프론트엔드)에는 간단한 500 에러 메시지를 보냅니다.
        raise HTTPException(status_code=500, detail="서버 오류: 퀴즈 데이터를 가져오는 데 실패했습니다.")

@router.post("/submit-answer", summary="퀴즈 답변 제출 및 채점")
def submit_answer(req_body: AnswerRequest, request: Request, db: Client = Depends(connect_supabase)):
    """
    사용자가 제출한 답변을 채점하고, 포인트를 지급하며, 관련 로그를 DB에 기록합니다.
    """
    try:
        # 1. 정답 확인
        # 사용자가 푼 문제(req_body.quiz_id)의 정답을 DB에서 조회합니다.
        # .single()은 반드시 결과가 한 개일 때 사용하며, 없거나 많으면 에러를 발생시킵니다.
        quiz_info_res = db.table('quiz').select('answer').eq('identify_code', req_body.quiz_id).single().execute()
        correct_answer = quiz_info_res.data['answer']
        
        # 사용자의 답과 정답을 비교하여 채점하고 포인트를 계산합니다.
        is_correct = (req_body.user_answer == correct_answer)
        points_to_add = 5 if is_correct else 2

        # 2. 사용자 포인트 업데이트
        # 'user_info' 테이블에서 해당 사용자를 찾아 현재 포인트를 조회합니다.
        user_info_res = db.table('user_info').select('total_point').eq('id', req_body.user_id).execute()
        if not user_info_res.data:
            raise HTTPException(status_code=404, detail=f"User '{req_body.user_id}' not found.")
        
        # 현재 포인트가 NULL(None)일 경우를 대비해 0으로 처리하고, 획득한 포인트를 더합니다.
        current_points = user_info_res.data[0].get('total_point') or 0
        new_total_points = current_points + points_to_add
        # 계산된 새로운 총 포인트를 DB에 업데이트합니다.
        db.table('user_info').update({'total_point': new_total_points}).eq('id', req_body.user_id).execute()

        # 3. 포인트 획득 로그 기록
        # 'point_log' 테이블에 포인트 획득 내역을 기록합니다.
        db.table('point_log').insert({
            "id": req_body.user_id,
            "category": req_body.topic,
            "point_value": points_to_add,
            "path": "주식 퀴즈",
            "timestamp": datetime.now().isoformat(), # 현재 시간을 ISO 형식의 문자열로 기록
            "ip_address": request.client.host      # 요청한 클라이언트의 IP 주소 기록
        }).execute()
        
        # 프론트엔드에 채점 결과와 획득 포인트를 반환합니다.
        return {"is_correct": is_correct, "points_awarded": points_to_add}
    
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 답변을 처리하는 데 실패했습니다.")
