import pandas as pd
import FinanceDataReader as fdr
import os
from pathlib import Path
from GetData import get_all_stock_data, get_technical_data, extract_unique_rows
from GetNews import GetNewsData, combine_json_files, json_files_load
from SupabaseHandle import insert_rows, request_table
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

    # '~cache.csv' file read >> add technical metrics >> save 'stock_data.csv'
    get_technical_data()

    # Get All data in 'technical_data'
    try:
        supabase_table = request_table('technical_data')
        supabase_table_length = 1
    except:
        supabase_table_length = 0

    # no data in 'technical_data'
    if supabase_table_length == 0:
        print("There is no data in 'technical_data', start insert all data")
        all_data = pd.read_csv('./cache/stock_data.csv')
        insert_rows(all_data)
        print("All data insert success.")
    
    try:
        # Extract new data
        new_rows = extract_unique_rows()

        # If the new data is in 'new_rows'
        if len(new_rows) != 0:
            print("Find a new data, start insert new data")
            insert_rows(new_rows)
            print("New data insert success.")

        # If the data is latest
        else:
            print("Data is latest")

    except Exception as e:
        print(f"Error: {e}")

    """ Sentimental-Analyze Start """
    # Get News Data
    collect = GetNewsData()

    # Get Stock Name & Stock Code
    stock_names = [stock['name'] for stock in top_10_stocks]
    stock_codes = [stock['code'] for stock in top_10_stocks]

    # Get Naver News Page (1 value = 25 page)
    get_page_value = 1
    
    # Get News Data Sentimental-Analysis Result >> ./cache/~.json
    for stock_name in stock_names:
        collect.run(query = stock_name, get_page_value = get_page_value)
        combine_json_files(query = stock_name, get_page_value = get_page_value)

    # Final Json File >> Supabase Table insert
    update_json = json_files_load(top_10_stocks)