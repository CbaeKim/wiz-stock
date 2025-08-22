# wiz-stock/app/router/pred_stock.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import datetime
import traceback
import pandas as pd
from app.dependency.connect_supabase import connect_supabase
from pathlib import Path
import FinanceDataReader as fdr

# --- 라우터 설정 ---
router = APIRouter(
    prefix="/stock-predict",
    tags=["stock-predict"]
)

# --- 요청 모델 ---
class StockPredictionRequest(BaseModel):
    user_id: str
    stock_code: str
    user_predict_trend: str

# --- API 엔드포인트 ---
@router.get("/check-participation", summary="주가 예측 게임 참여 가능 여부 확인")
async def check_participation(user_id: str, db: Client = Depends(connect_supabase)):
    """
    사용자가 오늘 주가 예측 게임에 참여했는지 여부를 확인
    """
    try:
        user_info_res = db.table('user_info').select('predict_game_participation').eq('id', user_id).execute()
    
        if not user_info_res.data:
            return {"can_participate": False}
        
        has_participated = user_info_res.data[0].get('predict_game_participation', False)
        
        return {"can_participate": not has_participated}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 참여 여부 확인에 실패했습니다.")

@router.get("/get-top10", summary="최신 날짜 기준 상위 10개 종목 가져오기")
async def get_top10(db: Client = Depends(connect_supabase)):
    """
    stock_data.csv 파일에서 최신 날짜를 기준으로 10개 종목을 가져옴
    """
    try:
        # 데이터 파일의 절대 경로 생성
        current_file_path = Path(__file__).resolve()
        project_root_path = current_file_path.parent.parent.parent 
        csv_file_path = project_root_path / "cache" / "stock_data.csv"

        # stock_data.csv 파일에서 데이터 읽기
        df = pd.read_csv(csv_file_path, dtype={'stock_code': str})
        
        # 종목 이름 가져오기
        # FinanceDataReader를 이용해 실시간으로 전체 종목 목록과 이름을 가져와 매핑
        try:
            krx_df = fdr.StockListing('KRX')
            name_map = krx_df.set_index('Code')['Name'].to_dict()

        except Exception as e:
            # fdr에서 데이터를 가져오지 못할 경우를 대비한 예외 처리
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="FinanceDataReader에서 종목 목록을 가져오는 데 실패했습니다.")


        # 'Date' 컬럼을 datetime 형식으로 변환
        df['Date'] = pd.to_datetime(df['Date'])

        # 가장 최신 날짜를 찾습니다.
        latest_date = df['Date'].max()
        
        # 최신 날짜의 데이터만 필터링하고, 그 중 상위 10개 행을 가져옴
        latest_stocks_df = df[df['Date'] == latest_date].head(10).copy()
        
        # stock_name을 매핑
        latest_stocks_df['stock_name'] = latest_stocks_df['stock_code'].map(name_map)

        # stock_code와 stock_name만 추출
        top10_stocks = [
            {"stock_code": row['stock_code'], "stock_name": row['stock_name']}
            for index, row in latest_stocks_df.iterrows()
        ]

        return top10_stocks
    
    except FileNotFoundError:
        # 디버깅을 위해 파일 경로를 에러 메시지에 추가
        raise HTTPException(status_code=404, detail=f"stock_data.csv 파일을 찾을 수 없습니다. 확인된 경로: {csv_file_path}. DataPipeline.py를 먼저 실행했는지 확인해주세요.")
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 종목 데이터를 가져오는 데 실패했습니다.")


@router.get("/get-stock-info", summary="특정 종목의 예측 및 감성 분석 정보 가져오기")
async def get_stock_info(stock_code: str, db: Client = Depends(connect_supabase)):
    """
    사용자가 선택한 종목에 대한 현재가, 모델 예측 정보, 감성 분석 점수 가져오기
    """
    try:
        # 최신 예측 모델링 정보 가져오기
        predict_res = db.table('predict_modeling').select('*').eq('stock_code', stock_code).order('predict_date', desc=True).limit(1).execute()
        predict_data = predict_res.data[0] if predict_res.data else None

        technical_res = db.table('technical_data').select('Close').eq('stock_code', stock_code).order('Date', desc=True).limit(1).execute()
        current_price = technical_res.data[0]['Close'] if technical_res.data else None
        
        sentiment_res = db.table('sentimental_score').select('score').eq('stock_code', stock_code).order('date', desc=True).limit(1).execute()
        sentiment_score = sentiment_res.data[0]['score'] if sentiment_res.data else None

        # 데이터가 하나라도 없으면 오류 반환
        if not all([predict_data, current_price, sentiment_score is not None]):
            raise HTTPException(status_code=404, detail=f"Stock data for {stock_code} not found.")

        # 감성 분석 점수 기반으로 전망 결정
        sentiment_outlook = "긍정적 전망" if sentiment_score >= 51 else "부정적 전망"
        
        return {
            "current_price": current_price,
            "trend_predict": predict_data['trend_predict'],
            "price_predict": predict_data['price_predict'],
            "top_feature": predict_data['top_feature'],
            "sentiment_score": sentiment_score,
            "sentiment_outlook": sentiment_outlook
        }
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 종목 정보를 가져오는 데 실패했습니다.")

@router.post("/submit-prediction", summary="사용자 주가 예측 답변 제출")
async def submit_prediction(req_body: StockPredictionRequest, request: Request, db: Client = Depends(connect_supabase)):
    """
    사용자의 주가 예측 선택을 DB에 저장하고, 참여 상태를 업데이트
    """
    try:
        # 참여 가능 여부 재확인
        check_res = await check_participation(req_body.user_id, db)
        if not check_res["can_participate"]:
            raise HTTPException(status_code=400, detail="이미 오늘 게임에 참여했습니다.")

        # 사용자 예측 데이터를 predict_game 테이블에 기록
        # 이 테이블은 추후 정답 확인 및 포인트 지급에 사용
        db.table('predict_game').insert({
            "user_id": req_body.user_id,
            "stock_code": req_body.stock_code,
            "predicted_trend": req_body.user_predict_trend,
            "prediction_date": datetime.now().isoformat()
        }).execute()
        
        # 사용자 정보에서 참여 상태 업데이트
        db.table("user_info").update({'predict_game_participation': True}).eq("id", req_body.user_id).execute()
        
        # 서비스 로그 기록
        db.table('service_log').insert({
            "date": datetime.now().isoformat(),
            "id": req_body.user_id,
            "ip_address": request.client.host,
            "category": "예측 게임 참여",
            "path": "주식 예측 게임",
            "content": f"종목: {req_body.stock_code}, 예측: {req_body.user_predict_trend}"
        }).execute()

        return {"message": "예측이 성공적으로 제출되었습니다. 결과는 다음 날 확인 가능합니다."}
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 예측 제출에 실패했습니다.")
