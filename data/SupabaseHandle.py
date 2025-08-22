import pandas as pd
import numpy as np
from supabase import Client, create_client


# 엔드포인트 URL 및 API 키 설정
SUPABASE_URL = 'https://yhayrbotkkuuvoxzhqct.supabase.co'
SUPABASE_KEY = 'sb_secret_5rUltxbkuiB3wFcTyMs1qw_cJHFo3kf'

# 클라이언트 연결
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[Supabase] Client connect success")
except Exception as e:
    print(f"[Supabase] Client connect failed: {e}")

def request_table(table_name) -> pd.DataFrame:
    """ Get All Rows in supabase """
    all_data = []
    page_size = 1000
    page = 0

    while True:
        start_index = page * page_size
        end_index = start_index + page_size - 1
        response = (supabase.from_(table_name).select('*').range(start_index, end_index).execute())
        data = response.data

        if not data and page == 0: # 첫 페이지부터 데이터가 없으면 바로 중단
            print("[Alert] No Data in table")
            return pd.DataFrame() # 비어있는 데이터프레임 반환

        all_data.extend(data)

        if len(data) < page_size:
            print("[Alert] All data get Success")
            break
        page += 1

    df = pd.DataFrame(all_data)

    if not df.empty and 'stock_code' in df.columns:
        df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)

    return df

def insert_rows(df):
    """ 데이터프레임을 supabase technical_data 테이블에 업로드 """
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    df_to_dictionary = df.to_dict('records')
    response = supabase.table('technical_data').insert(df_to_dictionary).execute()
    print("[Alert] Success Insert Rows.")

    return response