import pandas as pd
import numpy as np
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
    if response.data:
        print("데이터베이스 적용 완료")
    else:
        print("코드를 재확인해주세요.")

def request_table(table_name) -> pd.DataFrame:
    """ Get All Rows in supabase """
    all_data = []
    page_size = 1000
    page = 0

    while True:
        start_index = page * page_size
        end_index = start_index + page_size - 1

        # print(f"{page + 1}번째 페이지 데이터 요청 중 (범위: {start_index} - {end_index})...")

        # range()를 사용하여 페이지별로 데이터 요청
        response = (supabase.from_(table_name).select('*').range(start_index, end_index).execute())

        data = response.data

        if not data:
            print("No Data")

        all_data.extend(data)

        # 가져온 데이터가 페이지 크기보다 작으면 마지막 페이지이므로 종료
        if len(data) < page_size:
            print("모든 데이터를 성공적으로 가져왔습니다.")
            break

        page += 1

    df = pd.DataFrame(all_data)

    # Data Preprocess
    df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)

    return df

def insert_rows(df):
    """ 데이터프레임을 supabase technical_data 테이블에 업로드 """
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    df_to_dictionary = df.to_dict('records')
    response = supabase.table('technical_data').insert(df_to_dictionary).execute()
    print("Success Insert Rows.")

    return response