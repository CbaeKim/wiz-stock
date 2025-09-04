# wiz-stock/data/GradePredictions.py
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

current_path = Path(__file__).resolve()
project_root = current_path.parent.parent
sys.path.append(str(project_root))

# .env 파일 로드
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def grade_predictions():
    """매일 예측 결과를 자동으로 채점하고 포인트를 지급하는 함수"""
    print("[+] 자동 채점 프로세스를 시작합니다...")

    # 로컬 stock_data.csv 파일 로드
    try:
        csv_path = project_root / "cache" / "stock_data.csv"
        stock_df = pd.read_csv(csv_path, dtype={'stock_code': str})
        stock_df['Date'] = pd.to_datetime(stock_df['Date']).dt.date
        print("[+] stock_data.csv 파일을 성공적으로 로드했습니다.")
    except FileNotFoundError:
        print(f"[!] {csv_path} 파일을 찾을 수 없습니다. DataPipeline.py가 먼저 실행되었는지 확인하세요.")
        return
    except Exception as e:
        print(f"[!] CSV 파일 로드 중 오류 발생: {e}")
        return

    # 어제의 채점되지 않은 모든 예측을 가져옴
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        response = supabase.table('predict_game').select('*') \
            .gte('prediction_date', yesterday.isoformat()) \
            .lt('prediction_date', today.isoformat()) \
            .eq('is_checked', False) \
            .execute()
        
        pending_predictions = response.data
        if not pending_predictions:
            print("[+] 채점할 예측이 없습니다. 프로세스를 종료합니다.")
            return
        print(f"[+] {len(pending_predictions)}개의 채점 대기 예측을 발견했습니다.")
    except Exception as e:
        print(f"[!] 예측 데이터 조회 중 오류 발생: {e}")
        return

    # 로드된 CSV 데이터에서 실제 등락 정보 추출
    actual_trends = {}
    unique_stock_codes = list(set(p['stock_code'] for p in pending_predictions))
    print(f"[+] {len(unique_stock_codes)}개 종목의 실제 데이터를 CSV에서 추출합니다...")
    for stock_code in unique_stock_codes:
        try:
            code_df = stock_df[stock_df['stock_code'] == stock_code]
            yesterday_data = code_df[code_df['Date'] == yesterday]
            today_data = code_df[code_df['Date'] == today]

            if not yesterday_data.empty and not today_data.empty:
                price_t = yesterday_data.iloc[0]['Close']
                price_t1 = today_data.iloc[0]['Close']
                actual_trends[stock_code] = "상승" if price_t1 > price_t else "하락"
        except Exception as e:
            print(f"[!] {stock_code} 종목 데이터 처리 실패: {e}")

    # 각 예측을 채점하고 사용자별 포인트 집계
    users_points = {}
    predictions_to_update = []
    print("[+] 각 예측을 채점합니다...")
    for pred in pending_predictions:
        user_id, stock_code = pred['user_id'], pred['stock_code']
        if stock_code not in actual_trends:
            continue

        actual_trend = actual_trends[stock_code]
        is_correct = (actual_trend == pred['predicted_trend'])
        points_awarded = 10 if is_correct else 5  # 포인트 정책 통일 (정답 10점, 오답 5점)

        predictions_to_update.append({
            'id': pred['id'], 
            'is_checked': True, 
            'actual_trend': actual_trend, 
            'result': is_correct,  # result 필드 추가
            'points_awarded': None  # 자동 포인트 지급 제거 (사용자가 수동으로 수령하도록)
        })
        # 포인트는 사용자가 수동으로 수령하도록 변경 (중복 지급 방지)

    # 채점 결과를 DB에 일괄 업데이트
    try:
        for update_data in predictions_to_update:
            pred_id = update_data.pop('id')
            supabase.table('predict_game').update(update_data).eq('id', pred_id).execute()
        print(f"[+] {len(predictions_to_update)}개 예측의 채점 결과를 DB에 업데이트했습니다.")
        print("[+] 포인트는 사용자가 직접 수령할 수 있도록 설정되었습니다.")
    except Exception as e:
        print(f"[!] 'predict_game' 테이블 업데이트 중 오류 발생: {e}")
        return

    print("[+] 자동 채점 프로세스를 성공적으로 완료했습니다.")

if __name__ == "__main__":
    grade_predictions()
