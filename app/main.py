# uvicorn app.main:app --reload
from fastapi import FastAPI

# add router files
from app.routers import login

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(login.router)