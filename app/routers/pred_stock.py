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
    reasoning: str = ""

class ClaimPointsRequest(BaseModel):
    prediction_id: str

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

@router.get("/get-game-data", summary="삼성전자 주가 예측 게임 데이터 가져오기")
async def get_game_data(user_id: str, db: Client = Depends(connect_supabase)):
    """
    삼성전자 주가 예측 게임에 필요한 모든 데이터를 가져옵니다.
    1. 삼성전자 현재가
    2. AI 최신 예측 데이터
    3. 감성분석 데이터
    4. 사용자 참여 가능 여부
    """
    try:
        stock_code = "005930"  # 삼성전자 고정
        
        # 1. 참여 가능 여부 확인
        participation_check = await check_participation(user_id, db)
        
        # 2. 삼성전자 현재가 (FDR에서 실시간 데이터)
        try:
            # FinanceDataReader로 삼성전자 최신 주가 데이터 가져오기
            samsung_data = fdr.DataReader(stock_code, start=datetime.now().date() - timedelta(days=5))
            if not samsung_data.empty:
                latest_price = samsung_data['Close'].iloc[-1]  # 가장 최근 종가
                latest_date = samsung_data.index[-1].strftime('%Y-%m-%d')
                current_price_data = {
                    "Close": float(latest_price),
                    "Date": latest_date
                }
                print(f"[INFO] FDR에서 삼성전자 현재가 조회 성공: {latest_price}원 ({latest_date})")
            else:
                raise Exception("FDR에서 데이터를 가져올 수 없습니다.")
        except Exception as fdr_error:
            print(f"[WARNING] FDR 조회 실패, DB에서 대체 데이터 사용: {fdr_error}")
            # FDR 실패 시 DB에서 대체 데이터 사용
            technical_res = db.table('technical_data').select('Close, Date').eq('stock_code', stock_code).order('Date', desc=True).limit(1).execute()
            current_price_data = technical_res.data[0] if technical_res.data else None
        
        # 3. AI 최신 예측 데이터
        predict_res = db.table('predict_modeling').select('price_predict, trend_predict, predict_date, top_feature').eq('stock_code', stock_code).order('predict_date', desc=True).limit(1).execute()
        ai_prediction = predict_res.data[0] if predict_res.data else None
        
        # 4. 감성분석 데이터 (최신)
        sentiment_res = db.table('sentimental_score').select('date, score, label').eq('stock_code', stock_code).order('date', desc=True).limit(1).execute()
        sentiment_data = sentiment_res.data[0] if sentiment_res.data else None
        
        # 데이터 검증
        if not current_price_data:
            raise HTTPException(status_code=404, detail="삼성전자 주가 데이터를 찾을 수 없습니다.")
        
        # 감성분석 결과 해석
        sentiment_outlook = "중립적 전망"
        if sentiment_data:
            if sentiment_data.get('label') == 1:
                sentiment_outlook = "긍정적 전망"
            elif sentiment_data.get('label') == 0:
                sentiment_outlook = "부정적 전망"
        
        # AI 예측 방향 해석
        ai_trend_outlook = "보합"
        if ai_prediction and ai_prediction.get('trend_predict'):
            trend = ai_prediction['trend_predict']
            if isinstance(trend, str):
                if "상승" in trend or "up" in trend.lower():
                    ai_trend_outlook = "상승"
                elif "하락" in trend or "down" in trend.lower():
                    ai_trend_outlook = "하락"
            elif isinstance(trend, (int, float)):
                if trend > 0:
                    ai_trend_outlook = "상승"
                elif trend < 0:
                    ai_trend_outlook = "하락"
        
        return {
            "can_participate": participation_check["can_participate"],
            "stock_info": {
                "stock_code": stock_code,
                "stock_name": "삼성전자",
                "current_price": current_price_data["Close"],
                "price_date": current_price_data["Date"]
            },
            "ai_prediction": {
                "price_predict": ai_prediction["price_predict"] if ai_prediction else None,
                "trend_predict": ai_trend_outlook,
                "predict_date": ai_prediction["predict_date"] if ai_prediction else None,
                "top_feature": ai_prediction["top_feature"] if ai_prediction else "데이터 없음"
            },
            "sentiment_analysis": {
                "date": sentiment_data["date"] if sentiment_data else None,
                "score": sentiment_data["score"] if sentiment_data else 0,
                "outlook": sentiment_outlook
            }
        }
        
    except Exception as e:
        print(f"[ERROR] 게임 데이터 조회 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류: 게임 데이터를 가져오는 데 실패했습니다. {str(e)}")

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
    """
    사용자의 주가 예측을 제출합니다.
    - 1일 1회만 참여 가능
    - 참여 후 user_info.predict_game_participation을 True로 변경
    - service_log에 참여 로그 기록
    """
    try:
        # 참여 가능 여부 확인
        check_res = await check_participation(req_body.user_id, db)
        if not check_res["can_participate"]:
            raise HTTPException(status_code=400, detail="이미 오늘 게임에 참여했습니다.")

        # 예측 방향을 한글로 변환
        trend_mapping = {"up": "상승", "down": "하락"}
        predicted_trend_kr = trend_mapping.get(req_body.user_predict_trend, req_body.user_predict_trend)
        
        # 예측 데이터 저장
        prediction_insert = db.table('predict_game').insert({
            "user_id": req_body.user_id,
            "stock_code": req_body.stock_code,
            "predicted_trend": predicted_trend_kr,
            "predict_opinion": req_body.reasoning,  # 사용자의 생각 저장
            "prediction_date": datetime.now().date().isoformat(),
            "is_checked": False,
            "result": None,
            "points_awarded": None,
            "actual_trend": None,
            "actual_price": None
        }).execute()
        
        # 사용자 참여 상태 업데이트
        db.table("user_info").update({
            'predict_game_participation': True
        }).eq("id", req_body.user_id).execute()
        
        # 서비스 로그 기록
        reasoning_text = req_body.reasoning if req_body.reasoning else "근거 없음"
        db.table('service_log').insert({
            "date": datetime.now().isoformat(),
            "id": req_body.user_id,
            "ip_address": request.client.host,
            "category": "예측 게임 참여",
            "path": "주식 예측 게임",
            "content": f"종목: {req_body.stock_code}, 예측: {predicted_trend_kr}, 근거: {reasoning_text}",
            "predict_opinion": req_body.reasoning  # service_log에도 predict_opinion 저장
        }).execute()

        print(f"[INFO] 예측 제출 완료 - 사용자: {req_body.user_id}, 종목: {req_body.stock_code}, 예측: {predicted_trend_kr}")
        
        return {
            "message": "예측이 성공적으로 제출되었습니다. 결과는 다음 날 확인 가능합니다.",
            "prediction_id": prediction_insert.data[0]["id"] if prediction_insert.data else None,
            "predicted_trend": predicted_trend_kr,
            "stock_code": req_body.stock_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 예측 제출 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 오류: 예측 제출에 실패했습니다.")

@router.get("/get-history", summary="사용자의 최근 5개 예측 기록 조회")
async def get_history(user_id: str, db: Client = Depends(connect_supabase)):
    """
    특정 사용자의 최근 5개 주가 예측 기록을 최신순으로 반환합니다.
    """
    try:
        print(f"[DEBUG] 예측 기록 조회 요청 - user_id: {user_id}")
        
        # 최근 5개 예측 기록 가져오기
        history_res = db.table('predict_game').select('*').eq('user_id', user_id).order('prediction_date', desc=True).limit(5).execute()
        
        print(f"[DEBUG] 데이터베이스 응답: {len(history_res.data) if history_res.data else 0}개 기록")
        
        if not history_res.data:
            print("[DEBUG] 예측 기록이 없음")
            return {
                "total_predictions": 0,
                "correct_predictions": 0,
                "accuracy_rate": 0,
                "history": []
            }

        # 종목명 매핑 (주요 종목만 하드코딩으로 빠르게 처리)
        name_map = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '005380': '현대차',
            '006400': '삼성SDI',
            '051910': 'LG화학',
            '035720': '카카오',
            '207940': '삼성바이오로직스',
            '068270': '셀트리온',
            '323410': '카카오뱅크'
        }
        print("[DEBUG] 종목명 매핑 완료 (하드코딩)")

        # 각 기록에 종목명 추가 및 데이터 정리
        total_predictions = len(history_res.data)
        correct_predictions = 0
        
        for record in history_res.data:
            record['stock_name'] = name_map.get(record['stock_code'], record['stock_code'])
            
            # predict_opinion을 reasoning으로 매핑 (프론트엔드 호환성)
            record['reasoning'] = record.get('predict_opinion', '') or "예측 근거 없음"
            
            # result 필드를 기반으로 is_correct 계산 (result는 boolean)
            if record.get('is_checked', False) and record.get('result') is not None:
                is_correct = record['result']  # result가 이미 boolean
                record['is_correct'] = is_correct
                if is_correct:
                    correct_predictions += 1
            else:
                record['is_correct'] = None
        
        # 정확도 계산 (체크된 예측만 대상)
        checked_predictions = sum(1 for record in history_res.data if record.get('is_checked', False))
        accuracy_rate = round((correct_predictions / checked_predictions * 100)) if checked_predictions > 0 else 0
        
        result = {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "accuracy_rate": accuracy_rate,
            "history": history_res.data
        }
        
        print(f"[DEBUG] 최종 결과: {result}")
        return result
        
    except Exception as e:
        print(f"[ERROR] 예측 기록 조회 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류: 예측 기록을 가져오는 데 실패했습니다. {str(e)}")

@router.get("/check-table-schema", summary="predict_game 테이블 스키마 확인")
async def check_table_schema(db: Client = Depends(connect_supabase)):
    """
    predict_game 테이블의 스키마를 확인합니다.
    """
    try:
        # 빈 쿼리로 테이블 구조 확인
        result = db.table('predict_game').select('*').limit(1).execute()
        
        if result.data:
            columns = list(result.data[0].keys())
            return {"columns": columns, "sample_data": result.data[0]}
        else:
            # 데이터가 없는 경우 빈 insert로 스키마 확인 시도
            return {"message": "테이블에 데이터가 없습니다.", "columns": []}
            
    except Exception as e:
        print(f"[ERROR] 스키마 확인 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"스키마 확인에 실패했습니다. {str(e)}")

@router.post("/create-test-data", summary="테스트용 예측 데이터 생성")
async def create_test_data(user_id: str, db: Client = Depends(connect_supabase)):
    """
    테스트용 예측 데이터를 생성합니다. (실제 스키마에 맞춤)
    """
    try:
        # 실제 스키마에 맞춘 테스트 데이터 생성 (result는 boolean)
        test_predictions = [
            {
                "user_id": user_id,
                "stock_code": "005930",
                "predicted_trend": "상승",
                "prediction_date": (datetime.now() - timedelta(days=4)).date().isoformat(),
                "is_checked": True,
                "result": True,  # boolean: True = 정답
                "points_awarded": 100,
                "actual_trend": "상승",
                "actual_price": 62500
            },
            {
                "user_id": user_id,
                "stock_code": "000660",
                "predicted_trend": "하락",
                "prediction_date": (datetime.now() - timedelta(days=3)).date().isoformat(),
                "is_checked": True,
                "result": False,  # boolean: False = 오답
                "points_awarded": 0,
                "actual_trend": "상승",
                "actual_price": 45200
            },
            {
                "user_id": user_id,
                "stock_code": "035420",
                "predicted_trend": "상승",
                "prediction_date": (datetime.now() - timedelta(days=2)).date().isoformat(),
                "is_checked": True,
                "result": True,  # boolean: True = 정답
                "points_awarded": 100,
                "actual_trend": "상승",
                "actual_price": 98000
            },
            {
                "user_id": user_id,
                "stock_code": "005930",
                "predicted_trend": "상승",
                "prediction_date": (datetime.now() - timedelta(days=1)).date().isoformat(),
                "is_checked": False,
                "result": None,
                "points_awarded": None,
                "actual_trend": None,
                "actual_price": None
            },
            {
                "user_id": user_id,
                "stock_code": "000660",
                "predicted_trend": "하락",
                "prediction_date": datetime.now().date().isoformat(),
                "is_checked": False,
                "result": None,
                "points_awarded": None,
                "actual_trend": None,
                "actual_price": None
            }
        ]
        
        # 기존 테스트 데이터 삭제
        db.table('predict_game').delete().eq('user_id', user_id).execute()
        
        # 새 테스트 데이터 삽입
        db.table('predict_game').insert(test_predictions).execute()
        
        return {"message": f"{len(test_predictions)}개의 테스트 예측 데이터가 생성되었습니다."}
        
    except Exception as e:
        print(f"[ERROR] 테스트 데이터 생성 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"테스트 데이터 생성에 실패했습니다. {str(e)}")

@router.post("/process-daily-results", summary="일일 예측 결과 처리 및 포인트 지급")
async def process_daily_results(target_date: str, db: Client = Depends(connect_supabase)):
    """
    특정 날짜의 예측 결과를 처리하고 포인트를 지급합니다.
    - target_date: YYYY-MM-DD 형식
    - 실제 주가와 예측을 비교하여 결과 계산
    - 맞춘 경우 10포인트, 틀린 경우 5포인트 지급
    - point_log에 포인트 지급 로그 기록
    """
    try:
        # 해당 날짜의 미처리 예측들 가져오기
        predictions = db.table('predict_game').select('*').eq('prediction_date', target_date).eq('is_checked', False).execute()
        
        if not predictions.data:
            return {"message": f"{target_date}에 처리할 예측이 없습니다."}
        
        processed_count = 0
        total_points_awarded = 0
        
        for prediction in predictions.data:
            try:
                stock_code = prediction['stock_code']
                user_id = prediction['user_id']
                predicted_trend = prediction['predicted_trend']
                
                # 다음 날 실제 주가 데이터 가져오기
                next_date = (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=1)).date()
                
                # 실제 주가 데이터 조회 (다음 날)
                actual_price_res = db.table('technical_data').select('Close, Date').eq('stock_code', stock_code).gte('Date', next_date.isoformat()).order('Date').limit(1).execute()
                
                if not actual_price_res.data:
                    print(f"[WARNING] {stock_code}의 {next_date} 주가 데이터를 찾을 수 없습니다.")
                    continue
                
                # 기준일 주가 (예측일)
                base_price_res = db.table('technical_data').select('Close').eq('stock_code', stock_code).eq('Date', target_date).execute()
                
                if not base_price_res.data:
                    print(f"[WARNING] {stock_code}의 {target_date} 기준 주가를 찾을 수 없습니다.")
                    continue
                
                base_price = base_price_res.data[0]['Close']
                actual_price = actual_price_res.data[0]['Close']
                
                # 실제 주가 변동 방향 계산
                if actual_price > base_price:
                    actual_trend = "상승"
                elif actual_price < base_price:
                    actual_trend = "하락"
                else:
                    actual_trend = "보합"
                
                # 예측 결과 판정
                is_correct = (predicted_trend == actual_trend) or (actual_trend == "보합")
                
                # 포인트 계산 (지급하지 않고 계산만)
                points = 10 if is_correct else 5
                
                # 예측 결과 업데이트 (포인트는 지급하지 않음)
                db.table('predict_game').update({
                    'is_checked': True,
                    'result': is_correct,
                    'points_awarded': None,  # 아직 포인트 미지급
                    'actual_trend': actual_trend,
                    'actual_price': actual_price
                }).eq('id', prediction['id']).execute()
                
                processed_count += 1
                
                print(f"[INFO] 처리 완료 - 사용자: {user_id}, 예측: {predicted_trend}, 실제: {actual_trend}, 결과: {'정답' if is_correct else '오답'}, 포인트: {points}")
                
            except Exception as e:
                print(f"[ERROR] 개별 예측 처리 실패: {e}")
                continue
        
        return {
            "message": f"{target_date}의 예측 결과 처리 완료",
            "processed_count": processed_count
        }
        
    except Exception as e:
        print(f"[ERROR] 일일 결과 처리 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"일일 결과 처리에 실패했습니다. {str(e)}")

@router.post("/reset-daily-participation", summary="일일 참여 상태 초기화")
async def reset_daily_participation(db: Client = Depends(connect_supabase)):
    """
    모든 사용자의 predict_game_participation을 False로 초기화합니다.
    (자정에 실행되는 배치 작업용)
    """
    try:
        result = db.table('user_info').update({
            'predict_game_participation': False
        }).neq('id', '').execute()  # 모든 사용자 대상
        
        affected_count = len(result.data) if result.data else 0
        
        print(f"[INFO] 일일 참여 상태 초기화 완료 - 대상 사용자: {affected_count}명")
        
        return {
            "message": "일일 참여 상태가 초기화되었습니다.",
            "affected_users": affected_count
        }
        
    except Exception as e:
        print(f"[ERROR] 참여 상태 초기화 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"참여 상태 초기화에 실패했습니다. {str(e)}")

@router.post("/claim-points", summary="예측 결과 포인트 수령")
async def claim_points(req_body: ClaimPointsRequest, request: Request, db: Client = Depends(connect_supabase)):
    """
    예측 결과에 대한 포인트를 수령합니다.
    - 이미 체크된 예측만 포인트 수령 가능
    - 정답: 10포인트, 오답: 5포인트
    - 한 번만 수령 가능
    """
    try:
        # 예측 기록 조회
        prediction_res = db.table('predict_game').select('*').eq('id', req_body.prediction_id).execute()
        
        if not prediction_res.data:
            raise HTTPException(status_code=404, detail="예측 기록을 찾을 수 없습니다.")
        
        prediction = prediction_res.data[0]
        
        # 검증: 결과가 체크되었는지 확인
        if not prediction.get('is_checked', False):
            raise HTTPException(status_code=400, detail="아직 결과가 확인되지 않은 예측입니다.")
        
        # 검증: 이미 포인트를 받았는지 확인
        if prediction.get('points_awarded') is not None:
            raise HTTPException(status_code=400, detail="이미 포인트를 수령한 예측입니다.")
        
        # 포인트 계산
        is_correct = prediction.get('result', False)
        points = 10 if is_correct else 5
        user_id = prediction['user_id']
        
        # 사용자 포인트 업데이트
        user_res = db.table('user_info').select('point').eq('id', user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")
        
        current_points = user_res.data[0]['point'] or 0
        new_points = current_points + points
        
        # 트랜잭션처럼 처리
        # 1. 예측 기록에 포인트 지급 표시
        db.table('predict_game').update({
            'points_awarded': points
        }).eq('id', req_body.prediction_id).execute()
        
        # 2. 사용자 포인트 업데이트
        db.table('user_info').update({
            'point': new_points
        }).eq('id', user_id).execute()
        
        # 3. 포인트 로그 기록
        db.table('point_log').insert({
            'timestamp': datetime.now().isoformat(),
            'id': user_id,
            'ip_address': request.client.host,
            'category': '주가 예측 게임 포인트',
            'point_value': points,
            'path': '주식 예측 게임 결과'
        }).execute()
        
        print(f"[INFO] 포인트 지급 완료 - 사용자: {user_id}, 포인트: {points}, 총 포인트: {new_points}")
        
        return {
            "message": f"포인트 {points}점이 지급되었습니다!",
            "points_awarded": points,
            "total_points": new_points,
            "result": "정답" if is_correct else "오답"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 포인트 수령 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"포인트 수령에 실패했습니다. {str(e)}")

@router.get("/debug-prediction", summary="특정 예측 기록 디버깅")
async def debug_prediction(prediction_date: str, db: Client = Depends(connect_supabase)):
    """
    특정 날짜의 예측 기록과 관련 데이터를 확인합니다.
    """
    try:
        # 해당 날짜의 예측 기록들
        predictions = db.table('predict_game').select('*').eq('prediction_date', prediction_date).execute()
        
        if not predictions.data:
            return {"message": f"{prediction_date}에 예측 기록이 없습니다."}
        
        result = {
            "prediction_date": prediction_date,
            "predictions": predictions.data,
            "technical_data_check": {}
        }
        
        # 각 예측에 대해 기술적 데이터 확인
        for pred in predictions.data:
            stock_code = pred['stock_code']
            
            # 예측일 주가 확인
            base_price_res = db.table('technical_data').select('Close, Date').eq('stock_code', stock_code).eq('Date', prediction_date).execute()
            
            # 다음날 주가 확인
            next_date = (datetime.strptime(prediction_date, '%Y-%m-%d') + timedelta(days=1)).date()
            next_price_res = db.table('technical_data').select('Close, Date').eq('stock_code', stock_code).gte('Date', next_date.isoformat()).order('Date').limit(3).execute()
            
            result["technical_data_check"][stock_code] = {
                "base_date_price": base_price_res.data if base_price_res.data else "데이터 없음",
                "next_dates_prices": next_price_res.data if next_price_res.data else "데이터 없음"
            }
        
        return result
        
    except Exception as e:
        print(f"[ERROR] 디버깅 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"디버깅에 실패했습니다. {str(e)}")

@router.post("/process-september-2", summary="9월 2일 예측 결과 수동 처리 (임시: 9/1→9/2 비교)")
async def process_september_2(db: Client = Depends(connect_supabase)):
    """
    9월 2일 예측 결과를 수동으로 처리합니다.
    임시로 9월 1일 → 9월 2일 주가 변동으로 비교합니다.
    """
    try:
        target_date = "2025-09-02"
        
        # 9월 2일 예측들 가져오기
        predictions = db.table('predict_game').select('*').eq('prediction_date', target_date).execute()
        
        if not predictions.data:
            return {"message": f"{target_date}에 처리할 예측이 없습니다."}
        
        processed_results = []
        
        for prediction in predictions.data:
            try:
                stock_code = prediction['stock_code']
                user_id = prediction['user_id']
                predicted_trend = prediction['predicted_trend']
                
                print(f"[INFO] 처리 중: {user_id}, {stock_code}, 예측: {predicted_trend}")
                
                # 9월 1일 기준가 (전날 종가)
                base_date = "2025-09-01"
                base_price_res = db.table('technical_data').select('Close').eq('stock_code', stock_code).eq('Date', base_date).execute()
                
                # 9월 2일 실제가 (예측일 종가)
                actual_price_res = db.table('technical_data').select('Close').eq('stock_code', stock_code).eq('Date', target_date).execute()
                
                if not base_price_res.data or not actual_price_res.data:
                    print(f"[WARNING] {stock_code}의 주가 데이터가 없습니다. 기준일: {base_price_res.data}, 실제일: {actual_price_res.data}")
                    continue
                
                base_price = base_price_res.data[0]['Close']  # 9/1: 67,650원
                actual_price = actual_price_res.data[0]['Close']  # 9/2: 69,000원
                
                # 실제 주가 변동 방향 계산
                if actual_price > base_price:
                    actual_trend = "상승"  # 67,650 → 69,000 (상승)
                elif actual_price < base_price:
                    actual_trend = "하락"
                else:
                    actual_trend = "보합"
                
                # 예측 결과 판정
                is_correct = (predicted_trend == actual_trend) or (actual_trend == "보합")
                
                # 예측 결과 업데이트
                db.table('predict_game').update({
                    'is_checked': True,
                    'result': is_correct,
                    'points_awarded': None,  # 포인트는 수동으로 받도록
                    'actual_trend': actual_trend,
                    'actual_price': actual_price
                }).eq('id', prediction['id']).execute()
                
                processed_results.append({
                    "user_id": user_id,
                    "stock_code": stock_code,
                    "predicted_trend": predicted_trend,
                    "actual_trend": actual_trend,
                    "base_price": base_price,
                    "actual_price": actual_price,
                    "price_change": actual_price - base_price,
                    "is_correct": is_correct,
                    "result": "정답" if is_correct else "오답"
                })
                
                print(f"[SUCCESS] 처리 완료: {user_id}, 예측: {predicted_trend}, 실제: {actual_trend} ({base_price}→{actual_price}), 결과: {'정답' if is_correct else '오답'}")
                
            except Exception as e:
                print(f"[ERROR] 개별 예측 처리 실패: {e}")
                continue
        
        return {
            "message": f"9월 2일 예측 결과 처리 완료 (9/1→9/2 비교)",
            "processed_count": len(processed_results),
            "comparison": "9월 1일(67,650원) → 9월 2일(69,000원) = 상승",
            "results": processed_results
        }
        
    except Exception as e:
        print(f"[ERROR] 9월 2일 처리 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"9월 2일 처리에 실패했습니다. {str(e)}")

@router.get("/check-september-data", summary="9월 2일 데이터 확인")
async def check_september_data(db: Client = Depends(connect_supabase)):
    """
    9월 2일 관련 데이터를 모두 확인합니다.
    """
    try:
        result = {}
        
        # 1. 9월 2일 예측 기록 확인
        predictions = db.table('predict_game').select('*').eq('prediction_date', '2025-09-02').execute()
        result['predictions'] = {
            'count': len(predictions.data) if predictions.data else 0,
            'data': predictions.data if predictions.data else []
        }
        
        # 2. 9월 2일 주가 데이터 확인 (삼성전자)
        sep2_price = db.table('technical_data').select('*').eq('stock_code', '005930').eq('Date', '2025-09-02').execute()
        result['sep2_samsung_price'] = sep2_price.data if sep2_price.data else "데이터 없음"
        
        # 3. 9월 3일 주가 데이터 확인 (삼성전자)
        sep3_price = db.table('technical_data').select('*').eq('stock_code', '005930').eq('Date', '2025-09-03').execute()
        result['sep3_samsung_price'] = sep3_price.data if sep3_price.data else "데이터 없음"
        
        # 4. 9월 1일~5일 주가 데이터 범위 확인
        range_prices = db.table('technical_data').select('Date, Close').eq('stock_code', '005930').gte('Date', '2025-09-01').lte('Date', '2025-09-05').order('Date').execute()
        result['samsung_price_range'] = range_prices.data if range_prices.data else "데이터 없음"
        
        return result
        
    except Exception as e:
        print(f"[ERROR] 데이터 확인 실패: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"데이터 확인에 실패했습니다. {str(e)}")
