# wiz-stock/app/router/pred_stock.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client
from datetime import datetime, timedelta
import traceback
import pandas as pd
from app.dependency.connect_supabase import connect_supabase
from pathlib import Path
import FinanceDataReader as fdr

# 라우터 설정
router = APIRouter(
    prefix="/stock-predict",
    tags=["stock-predict"]
)

# 요청 모델
class StockPredictionRequest(BaseModel):
    user_id: str
    stock_code: str
    user_predict_trend: str

# API 엔드포인트
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
        current_file_path = Path(__file__).resolve()
        project_root_path = current_file_path.parent.parent.parent 
        csv_file_path = project_root_path / "cache" / "stock_data.csv"
        df = pd.read_csv(csv_file_path, dtype={'stock_code': str})
        
        krx_df = fdr.StockListing('KRX')
        name_map = krx_df.set_index('Code')['Name'].to_dict()

        df['Date'] = pd.to_datetime(df['Date'])
        latest_date = df['Date'].max()
        latest_stocks_df = df[df['Date'] == latest_date].head(10).copy()
        latest_stocks_df['stock_name'] = latest_stocks_df['stock_code'].map(name_map)

        top10_stocks = [
            {"stock_code": row['stock_code'], "stock_name": row['stock_name']}
            for index, row in latest_stocks_df.iterrows()
        ]
        return top10_stocks
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"stock_data.csv 파일을 찾을 수 없습니다. 확인된 경로: {csv_file_path}.")
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 종목 데이터를 가져오는 데 실패했습니다.")

@router.get("/get-stock-info", summary="특정 종목의 예측 및 감성 분석 정보 가져오기")
async def get_stock_info(stock_code: str, db: Client = Depends(connect_supabase)):
    try:
        predict_res = db.table('predict_modeling').select('*').eq('stock_code', stock_code).order('predict_date', desc=True).limit(1).execute()
        predict_data = predict_res.data[0] if predict_res.data else None

        technical_res = db.table('technical_data').select('Close').eq('stock_code', stock_code).order('Date', desc=True).limit(1).execute()
        current_price = technical_res.data[0]['Close'] if technical_res.data else None
        
        sentiment_res = db.table('sentimental_score').select('score, label').eq('stock_code', stock_code).order('date', desc=True).limit(1).execute()
        sentiment_data = sentiment_res.data[0] if sentiment_res.data else None

        if not all([predict_data, current_price, sentiment_data]):
            raise HTTPException(status_code=404, detail=f"Stock data for {stock_code} not found.")

        sentiment_label = sentiment_data.get('label')
        sentiment_outlook = "긍정적 전망" if sentiment_label == 1 else "부정적 전망"
        
        return {
            "current_price": current_price,
            "trend_predict": predict_data['trend_predict'],
            "price_predict": predict_data['price_predict'],
            "top_feature": predict_data['top_feature'],
            "sentiment_score": sentiment_data.get('score'), 
            "sentiment_outlook": sentiment_outlook
        }
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 종목 정보를 가져오는 데 실패했습니다.")

@router.post("/submit-prediction", summary="사용자 주가 예측 답변 제출")
async def submit_prediction(req_body: StockPredictionRequest, request: Request, db: Client = Depends(connect_supabase)):
    try:
        check_res = await check_participation(req_body.user_id, db)
        if not check_res["can_participate"]:
            raise HTTPException(status_code=400, detail="이미 오늘 게임에 참여했습니다.")

        db.table('predict_game').insert({
            "user_id": req_body.user_id,
            "stock_code": req_body.stock_code,
            "predicted_trend": req_body.user_predict_trend,
            "prediction_date": datetime.now().isoformat(),
            "is_checked": False
        }).execute()
        
        db.table("user_info").update({'predict_game_participation': True}).eq("id", req_body.user_id).execute()
        
        db.table('service_log').insert({
            "date": datetime.now().isoformat(),
            "id": req_body.user_id,
            "ip_address": request.client.host,
            "category": "예측 게임 참여",
            "path": "주식 예측 게임",
            "content": f"종목: {req_body.stock_code}, 예측: {req_body.user_predict_trend}"
        }).execute()

        return {"message": "예측이 성공적으로 제출되었습니다. 결과는 다음 날 확인 가능합니다."}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 예측 제출에 실패했습니다.")

@router.get("/get-history", summary="사용자의 전체 예측 기록 조회")
async def get_history(user_id: str, db: Client = Depends(connect_supabase)):
    """
    특정 사용자의 모든 주가 예측 기록을 최신순으로 반환합니다.
    """
    try:
        history_res = db.table('predict_game').select('*').eq('user_id', user_id).order('prediction_date', desc=True).execute()
        
        if not history_res.data:
            return []

        krx_df = fdr.StockListing('KRX')
        name_map = krx_df.set_index('Code')['Name'].to_dict()

        for record in history_res.data:
            record['stock_name'] = name_map.get(record['stock_code'], record['stock_code'])
            
        return history_res.data
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 예측 기록을 가져오는 데 실패했습니다.")
