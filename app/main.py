# uvicorn app.main:app --reload
from fastapi import FastAPI, Request
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from app.dependency.connect_supabase import connect_supabase
import asyncio, subprocess

# add router files
from app.routers import login, quiz, mypage_router, sign_up, point, shop_router, pred_stock, ranking

BASE_DIR = Path(__file__).resolve().parents[1]

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


# --- 라우터 포함 (변경 없음) ---
app.include_router(login.router)
app.include_router(quiz.router)
app.include_router(mypage_router.router)
app.include_router(sign_up.router)
app.include_router(point.router)
app.include_router(shop_router.router)
app.include_router(pred_stock.router)
app.include_router(ranking.router)


# 1. 정적 파일 폴더 마운트
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/index.html", include_in_schema=False)
def index_alias():
    return RedirectResponse(url="/", status_code=308)

# 모든 요청에 index.html을 반환하도록 변경
@app.get("/", include_in_schema=False)
def serve_root():
    return FileResponse(BASE_DIR / "index.html")