from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
import os

# Define Endpoint URL, API
current_path = Path.cwd()
env_path = current_path / '.env'

load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Supabase 클라이언트 연결
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# supabase 클라이언트 연결 함수 정의
def connect_supabase():
    return supabase