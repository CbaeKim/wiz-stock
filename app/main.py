# uvicorn app.main:app --reload
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import asyncio, subprocess

# add router files
from app.routers import login, quiz, mypage_router, sign_up

def get_news_datas():
    """ A function to run when the server starts """
    print("Start News data mining & Sentimental analysis")

    subprocess.run(['python', './data/DataPipeline.py'])

    print("Process Complete.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ A function to run when the server starts """
    scheduler.add_job(
        get_news_datas,
        CronTrigger(hour = 9, minute = 41)  # AM 10:00
    )

    scheduler.add_job(
        get_news_datas,
        CronTrigger(hour = 15, minute = 30)  # PM 3:30
    )

    scheduler.add_job(
        get_news_datas,
        CronTrigger(hour = 18, minute = 00)  # PM 6:00
    )

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(lifespan = lifespan)  # Definition FastAPI Object
scheduler = AsyncIOScheduler()      # Definition Scheduler object

app.include_router(login.router)            # 로그인 관련 기능
app.include_router(quiz.router)             # quiz 관련 기능
app.include_router(mypage_router.router)    # mypage 관련 기능'
app.include_router(sign_up.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}