import pandas as pd
import FinanceDataReader as fdr
import os
from pathlib import Path
from GetData import get_all_stock_data, get_technical_data, extract_unique_rows
from GetNews import GetNewsData, combine_json_files, json_files_load
from SupabaseHandle import insert_rows
from supabase import Client, create_client
from dotenv import load_dotenv

# Define Endpoint URL, API
current_path = Path.cwd()
env_path = current_path / '.env'

load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Connect Client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[Supabase] Client connection Success.")
except Exception as e:
    print(f"Connection Error: {e}")

if __name__=="__main__":
    """ Technical Data Upload start """
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
        insert_rows([new_rows[0]])
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

    """ Sentimental-Analyze Start """
    # Get News Data
    collect = GetNewsData()

    # Get Stock Name & Stock Code
    stock_names = [stock['name'] for stock in top_10_stocks]
    stock_codes = [stock['code'] for stock in top_10_stocks]

    # Get Naver News Page (1 value = 25 page)
    get_page_value = 1
    
    print(stock_names)
    # Get News Data Sentimental-Analysis Result >> ./cache/~.json
    for stock_name in stock_names:
        collect.run(query = stock_name, get_page_value = get_page_value)
        combine_json_files(query = stock_name, get_page_value = get_page_value)

    # Final Json File >> Supabase Table insert
    update_json = json_files_load(top_10_stocks)