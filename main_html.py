# uvicorn main_html:app --reload

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어를 임포트합니다.

# 라우터들을 임포트합니다.
from app.routers import (
    login, mypage_router, point, pred_stock, quiz, sign_up, shop_router
)

app = FastAPI()

# --- CORS 설정 추가 시작 ---
# 이 설정은 브라우저의 CORS 정책으로 인한 요청 차단을 해결합니다.
# 프런트엔드(http://127.0.0.1:5500)에서 백엔드(http://127.0.0.1:8000)로의 요청을 허용합니다.
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500"  # 프런트엔드 서버의 주소를 정확히 명시합니다.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)
# --- CORS 설정 추가 끝 ---

# 템플릿(HTML) 파일을 제공할 디렉토리를 설정합니다.
templates = Jinja2Templates(directory="pages")

# 정적 파일들을 위한 디렉토리 설정
app.mount("/static/css", StaticFiles(directory="pages/css"), name="static_css")
app.mount("/static/js", StaticFiles(directory="js"), name="static_js")

# 각 라우터 파일에 정의된 라우터들을 메인 애플리케이션에 포함시킵니다.
app.include_router(login.router)
app.include_router(mypage_router.router)
app.include_router(point.router)
app.include_router(pred_stock.router)
app.include_router(quiz.router)
app.include_router(sign_up.router)
app.include_router(shop_router.router)

# --- HTML 페이지 라우트 ---
@app.get("/")
def serve_main_page(request: Request):
    """
    루트 경로('/')로 접속하면 'index.html'을 반환합니다.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", name="login")
def serve_login_page(request: Request):
    """
    '/login' 경로로 접속하면 'login.html'을 반환합니다.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/mypage", name="mypage")
def serve_mypage(request: Request):
    """
    '/mypage' 경로로 접속하면 'my_page.html'을 반환합니다.
    """
    return templates.TemplateResponse("my_page.html", {"request": request})

@app.get("/stock-prediction-game", name="stock-prediction-game")
def serve_stock_prediction_game(request: Request):
    """
    '/stock-prediction-game' 경로로 접속하면 'stock_prediction_game.html'을 반환합니다.
    """
    return templates.TemplateResponse("stock_prediction_game.html", {"request": request})

@app.get("/sign_up", name="sign_up")
def serve_signup_page(request: Request):
    """
    '/sign_up' 경로로 접속하면 'sign_up.html'을 반환합니다.
    """
    return templates.TemplateResponse("sign_up.html", {"request": request})
