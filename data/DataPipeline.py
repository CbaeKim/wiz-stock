import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime, timedelta
from GetData import get_all_stock_data, get_technical_data, extract_unique_rows
from SupabaseHandle import insert_rows
from supabase import Client, create_client

# 엔드포인트 URL 및 API 키 설정
SUPABASE_URL = 'https://yhayrbotkkuuvoxzhqct.supabase.co'
SUPABASE_KEY = 'sb_secret_5rUltxbkuiB3wFcTyMs1qw_cJHFo3kf'

# 클라이언트 연결
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[Supabase] Client connection Success.")
except Exception as e:
    print(f"Connection Error: {e}")

def validation(response):
    """ Supabase Data 조작 완료 검증 함수 """
    if response.data:
        print("DB Update Success")
    else:
        print("Please check your code")

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

    # create 'stock_data_cache.csv' : All Stock Data Mining result
    new_data = get_all_stock_data(top_10_stocks)

    # '~cache.csv' file read > get technical metrics > save 'stock_data.csv'
    get_technical_data()

    try:
        # Extract Unique rows >> Insert rows >> save 'stock_data.csv'
        new_rows = extract_unique_rows()
        insert_rows([new_rows])
        print("Data update success")

    except:
        select_table = supabase.from_('technical_data').select('*').execute()

        if len(select_table.data) == 0:
            # Insert New data
            insert_rows([new_data])
            print("New data insert success.")
        
        else:
            print("DB is latest")