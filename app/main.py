# uvicorn app.main:app --reload
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from app.dependency.connect_supabase import connect_supabase
import asyncio, subprocess

# add router files
from app.routers import login, quiz, mypage_router, sign_up, point, shop_router, pred_stock

# --- 기존 함수들 (변경 없음) ---
def get_news_datas():
    """ A function to run when the server starts """
    print("[Function: get_news_datas] Start News data mining & Sentimental analysis")
    subprocess.run(['python', './data/DataPipeline.py'])
    print("Process Complete.")

def run_predict_modeling():
    """Function to run PredictModel.py"""
    print("[Function: run_predict_modeling] Start predictive modeling process.")
    subprocess.run(['python', './data/PredictModel.py'])
    print("Predictive Modeling Complete.")

def run_auto_grading():
    """Function to run GradePredictions.py for automatic grading"""
    print("[Function: run_auto_grading] Start automatic grading process.")
    subprocess.run(['python', './data/GradePredictions.py'])
    print("Automatic Grading Complete.")

def reset_day_process():
    """ Function to reset participation values """
    print("[Function: reset_day_process] Start")
    update_data = {
        'quiz_participation': False,
        'predict_game_participation': False
    }
    supabase = connect_supabase()
    response = supabase.table('user_info').update(update_data).not_.is_('id', None).execute()
    return print("[Function: reset_day_process] Success")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ A function to run when the server starts """
    scheduler.add_job(get_news_datas, CronTrigger(hour = 10, minute = 43))      # AM 10:00
    scheduler.add_job(get_news_datas, CronTrigger(hour = 15, minute = 30))      # PM 3:30
    scheduler.add_job(run_predict_modeling, CronTrigger(hour = 16, minute = 0)) # PM 4:00
    scheduler.add_job(run_auto_grading, CronTrigger(hour = 16, minute = 30 ))   # PM 4:30
    scheduler.add_job(get_news_datas, CronTrigger(hour = 18, minute = 0))      # PM 6:00
    scheduler.add_job(reset_day_process, CronTrigger(hour = 0, minute = 0))    # AM 12:00
    scheduler.start()
    yield
    scheduler.shutdown()

scheduler = AsyncIOScheduler()
app = FastAPI(lifespan=lifespan)

# --- CORS 미들웨어 (변경 없음) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # 개발 환경 (Live Server 등)에서 API를 호출할 수 있도록 허용하는 주소입니다.
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        # TODO: 향후 웹사이트 배포 시, 실제 서비스 도메인을 여기에 추가해야 합니다.
        # 예: "https://www.wiz-stock.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 포함 (변경 없음) ---
app.include_router(login.router)
app.include_router(quiz.router)
app.include_router(mypage_router.router)
app.include_router(sign_up.router)
app.include_router(point.router)
app.include_router(shop_router.router)
app.include_router(pred_stock.router)


# --- ✨✨✨ 이 부분이 중요합니다 ✨✨✨ ---

# 1. 정적 파일 폴더 마운트
# /js URL을 실제 js 폴더에, /pages URL을 실제 pages 폴더에 연결합니다.
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/images", StaticFiles(directory="images"), name="images")

# 2. 루트 경로('/') 요청 처리
@app.get("/")
def read_root():
    # 프로젝트 최상위 폴더에 있는 'index.html'을 반환합니다.
    return FileResponse('./index.html')

