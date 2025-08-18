from supabase import Client
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.dependency.connect_supabase import connect_supabase
import pandas as pd
import bcrypt
import requests

# 라우터 설정
router = APIRouter(
    prefix = '/login',
    tags = ['login']
)

# 아이디, 패스워드 입력값 검증
class Item(BaseModel):
    username: str
    password: str

FASTAPI_ENDPOINT = 'http://localhost:8000'

# 로그인 기능 구현
@router.post("/validation", summary = "로그인을 구현하는 함수")
async def login(request: Request, item: Item, db: Client = Depends(connect_supabase)):
    # 계정 정보 초기화
    input_username = item.username
    input_password = item.password
    
    # DB -> 유저 정보 조회
    user_info = db.from_('user_info').select('id', 'password').execute().data
    
    try:
        df = pd.DataFrame(user_info)

        # 유저가 입력한 ID에 매칭되는 ID / PW 행 필터
        user_search = df[(df['id'] == input_username)]

        # ID / PW 추출
        db_id = user_search['id'].iloc[0]
        db_pw = user_search['password'].iloc[0]

        # ID/PW 입력값 검증 (return True or False)
        validation_result = bcrypt.checkpw(input_password.encode('utf-8'), str(db_pw).encode('utf-8'))
    
    # 없는 유저 정보일경우 실행
    except:
        return {"message": "LoginFail"}

    # 패스워드 일치
    if validation_result is True:
        # IP 추출
        ip_address_request = await get_hostip(request)
        ip_address = ip_address_request['host_ip']

        # 로그인 로그 추가
        add_log = await add_login_log(id = db_id, ip_address = ip_address, db = db)

        return {"message": "LoginSuccess"}
    # 패스워드 오류
    else:
        return {"message": "LoginFail"}
    
# 유저 이름 조회
@router.post("/get_name", summary = "유저의 이름을 가져옴")
async def get_name(item: Item, db: Client = Depends(connect_supabase)):
    input_username = item.username
    input_password = item.password

    # DB -> 유저 정보 조회
    user_info = db.from_('user_info').select('id', 'nickname').execute().data

    try:
        df = pd.DataFrame(user_info)

        # ID에 해당하는 정보 추출
        user_search = df[(df['id'] == input_username)]

        user_name = user_search['nickname'].iloc[0]

        return {'user_name': user_name}

    except:
        return {'message': "NotFound"}

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

async def add_login_log(id, ip_address, db: Client):
    """ 로그인 로그를 추가합니다. """
    # 행 정보 입력
    insert_row = {
        'id': id,
        'ip_address': ip_address,
        'category': 'login',
        'path': 'login',
        'content': '로그인',
    }

    response = db.table('service_log').insert(insert_row).execute()
    
    return {'message': 'success'}