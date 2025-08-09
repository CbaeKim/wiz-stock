import pandas as pd
import FinanceDataReader as fdr
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
    # market capitalization Top 10
    krx_df = fdr.StockListing('KRX').sort_values(by = 'Marcap', ascending = False)
    print("KRX Data Mining Success")

    # KRX Data Preprocess
    top_10 = krx_df[:10][['Code', 'Name']]
    top_10.rename(columns = {'Code': 'code', 'Name': 'name'}, inplace = True)
    top_10 = top_10[['name', 'code']]
    top_10['code'] = top_10['code'] + '.KS'
    top_10_stocks = top_10.to_dict('records')
    print("KRX Top 10 Data Preprocess Success")
    
    # create 'stock_data_cache.csv' : All Stock Data Mining result
    new_data = get_all_stock_data(top_10_stocks)

    # '~cache.csv' file read > get technical metrics > save 'stock_data.csv'
    get_technical_data()

    try:
        # 1. Compare new_data and stock_data.csv
        # 2. Insert compare result rows
        # 3. save 'stock_data.csv'
        new_rows = extract_unique_rows()
        insert_rows([new_rows])
        print("Data update success")

    except:
        # Extract the sample DB and check its existence.
        select_table = supabase.from_('technical_data').select('*').execute()

        if len(select_table.data) == 0:
            # Insert New data
            insert_rows([new_data])
            print("New data insert success.")
        
        else:
            print("DB is latest")