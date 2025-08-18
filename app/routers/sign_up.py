from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from app.dependency.connect_supabase import connect_supabase
from supabase import Client
import os, re
import bcrypt  # bcrypt 라이브러리 추가

router = APIRouter(
    prefix="/sign_up",
    tags=["sign_up"]
)

def hash_password(password: str) -> str:
    """ Hash a password using bcrypt. """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')

class User(BaseModel):
    """ Pydantic for sign up data"""
    username: str
    password: str
    nickname: str

class CheckNickname(BaseModel):
    """ Pydantic for check nickname data """
    nickname: str

@router.post("/", summary = "회원가입 로직 함수")
async def sign_up_user(request: Request, user: User, db: Client = Depends(connect_supabase)):
    try:
        # Check Password validation
        if len(user.password) < 8 or \
           not re.search(r"[0-9]", user.password) or \
           not re.search(r"[a-zA-Z]", user.password) or \
           not re.search(r"[!@#$%^&*(),.?\":{}|<>]", user.password):
            raise HTTPException(status_code=400, detail="비밀번호는 최소 8자 이상이며, 숫자, 영어(대소문자), 특수문자를 포함해야 합니다.")
        
        # Check duplication: ID
        response_username = db.table("user_info").select("id").eq("id", user.username).execute()
        if len(response_username.data) > 0:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

        # Check duplication: Nickname
        response_nickname = db.table("user_info").select("nickname").eq("nickname", user.nickname).execute()
        if len(response_nickname.data) > 0:
            raise HTTPException(status_code=400, detail="이미 존재하는 닉네임입니다.")

        # Hashing password
        hashed_password = hash_password(user.password)
        
        # Insert user information to supabase
        db.table("user_info").insert({
            "id": user.username,
            "password": hashed_password,
            "nickname": user.nickname
        }).execute()

        # Add Service log
        request_ip = await get_hostip(request)
        host_ip = request_ip['host_ip']

        db.table("service_log").insert({
            "id": user.username,
            "ip_address": host_ip,
            "category": "sign up",
            "path" : "sign up",
            "content": "회원가입"
        }).execute()

        return {"message": "회원가입이 완료되었습니다."}
    except Exception as e:
        error_message = str(e)
        if "already registered" in error_message:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.post("/get_host_ip", summary = "Client IP 주소 반환")
async def get_hostip(request: Request):
    """ Return Client IP address """
    x_forwarded_for = request.headers.get('X-Forwarded-For')

    # if have a proxy server
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()

    else:
        client_ip = request.client.host

    return {"host_ip": client_ip}