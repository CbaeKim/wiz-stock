# uvicorn app.main:app --reload
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from app.dependency.connect_supabase import connect_supabase
import asyncio, subprocess

# add router files
from app.routers import login, quiz, mypage_router, sign_up, point, shop_router

def get_news_datas():
    """ A function to run when the server starts """
    print("[Function: get_news_datas] Start News data mining & Sentimental analysis")

    subprocess.run(['python', './data/DataPipeline.py'])

    print("Process Complete.")

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
    scheduler.add_job(get_news_datas, CronTrigger(hour = 10, minute = 0))      # AM 10:00
    scheduler.add_job(get_news_datas, CronTrigger(hour = 15, minute = 30))      # PM 3:30
    scheduler.add_job(get_news_datas, CronTrigger(hour = 18, minute = 0))      # PM 6:00
    scheduler.add_job(reset_day_process, CronTrigger(hour = 0, minute = 0))    # AM 12:00

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(lifespan = lifespan)  # Definition FastAPI Object
scheduler = AsyncIOScheduler()      # Definition Scheduler object

app.include_router(login.router)            # 로그인 관련 기능
app.include_router(quiz.router)             # quiz 관련 기능
app.include_router(mypage_router.router)    # mypage 관련 기능'
app.include_router(sign_up.router)
app.include_router(point.router)
app.include_router(shop_router.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}