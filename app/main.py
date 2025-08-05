# uvicorn app.main:app --reload
from fastapi import FastAPI
from pydantic import BaseModel
from app.routers import login
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(login.router)