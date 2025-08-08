import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime, timedelta
from GetData import analyze_data
from supabase import Client, create_client

# 엔드포인트 URL 및 API 키 설정
SUPABASE_URL = 'https://yhayrbotkkuuvoxzhqct.supabase.co'
SUPABASE_KEY = 'sb_secret_5rUltxbkuiB3wFcTyMs1qw_cJHFo3kf'

# 클라이언트 연결
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase 클라이언트 연결 완료.")
except Exception as e:
    print(f"Supabase 클라이언트 연결 실패: {e}")

def validation(response):
    """ Supabase Data 조작 완료 검증 함수 """
    if response.data:
        print("데이터베이스 적용 완료")
    else:
        print("코드를 재확인해주세요.")

def get_recent_date(stock_list):
    """ 입력받은 Stock List Dict의 가장 최근 데이터의 날짜 딕셔너리 반환 """
    stock_codes = [stock['code'][:-3] for stock in stock_list]
    stock_recent_dates = []
    stock_dict = {'code': stock_codes}
    today = datetime.now().strftime('%Y-%m-%d')

    # loop: return stock_dict
    for stock_code in stock_codes:
        recent_date = (
            supabase.from_('technical_data')
            .select('Date', 'stock_code')
            .eq('stock_code', stock_code)
            .order('Date', desc= True)
            .limit(1)
            .execute().data
        )
        
        # Get recent Date & None Data Classification
        if len(recent_date) == 0:
            stock_recent_dates.append("max")
            print(f"[{today}] max priod data append success")
        else:
            stock_recent_dates.append(recent_date[0]["Date"])
            print(f"[{today}] date append success")
    
    # update dictionary key: value
    stock_dict['recent_date'] = stock_recent_dates

    return stock_dict

def get_stocks_top_10(stocks_list):
    """ analyze_data 함수 실행 """
    # 전역 변수 정의
    repeat_value = len(stocks_list)
    stock_dict = get_recent_date(stocks_list)
    df_list = []

    # Today Date (ex. '2025-08-08')
    today = datetime.now().strftime('%Y-%m-%d')

    for i in range(repeat_value):
        stock_code = stock_dict['code'][i]+'.KS'
        recent_date = stock_dict['recent_date'][i]
        recent_date_tr = datetime.strptime(recent_date, '%Y-%m-%d')

        # No Data in database
        if today == recent_date:
            print(f"DB is latest: {today}")

        elif recent_date == "max":
            df = analyze_data(stock_code, period = 'max')
            df_list.append(df)
        
        # Recent Data Update
        else:
            insert_date = recent_date_tr + timedelta(days = 1)  # Date + 1
            start_date = insert_date.strftime('%Y-%m-%d')       # datetime >> str
            df = analyze_data(stock_code, start_date = start_date)
            df_list.append(df)
    
    return df_list

def insert_rows(df_list):
    """ 데이터프레임을 supabase technical_data 테이블에 업로드 """
    for df in df_list:
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        df_to_dictionary = df.to_dict('records')
        response = supabase.table('technical_data').insert(df_to_dictionary).execute()

    return response

def table_to_csv(table_name, path, batch_size = 1000):
    """ 모든 테이블 조회 후 CSV 파일로 저장 """
    all_data = []
    offset = 0

    while True:
        try:
            response = supabase.table(table_name).select('*').range(offset, offset + batch_size-1).execute()
            chunk = response.data

            if len(chunk) < batch_size:
                print("Success load all data")
                all_data.extend(chunk)
                break

            all_data.extend(chunk)

            offset += batch_size

        except Exception as e:
            print(f"Data load error: {e}")
            break
    
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(path)
        print("Save Success")

        return df
    else:
        return print("No data")

if __name__=="__main__":

    # 시가 총액 기준 주식 Top 10 리스트
    top_10_stocks = [
        {'name': '삼성전자', 'code': '005930.KS'},
        {'name': 'SK하이닉스', 'code': '000660.KS'},
        {'name': 'LG에너지솔루션', 'code': '373220.KS'},
        {'name': '삼성바이오로직스', 'code': '207940.KS'},
        {'name': '한화에어로스페이스', 'code': '012450.KS'},
        {'name': '삼성전자우', 'code': '005935.KS'},
        {'name': '현대차', 'code': '005380.KS'},
        {'name': 'KB금융', 'code': '105560.KS'},
        {'name': '두산에너빌리티', 'code': '034020.KS'},
        {'name': 'HD현대중공업', 'code': '329180.KS'},
    ]

    # 주가 데이터 및 기술적 지표 산출 -> 데이터프레임들이 담긴 리스트 반환
    df_list = get_stocks_top_10(top_10_stocks)

    try:
        response = insert_rows(df_list)
        print(validation(response))
    except:
        print("None")

    # 최종 데이터 CSV 파일로 저장
    df = table_to_csv('technical_data', path = './data/stock_data.csv')