# uvicorn app.main:app --reload
from fastapi import FastAPI

# add router files
from app.routers import login
from app.routers import execute

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(login.router)            # 로그인 관련 기능
app.include_router(execute.router)          # 데이터 수집 코드 파일 실행 기능