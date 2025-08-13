from fastapi import APIRouter, HTTPException
from pathlib import Path
import subprocess

# 라우터 설정
router = APIRouter(
    prefix = '/execute',
    tags = ['execute']
)

current_path = Path.cwd()
code_path = current_path / 'data' / 'DataPipeline.py'

@router.get('/', summary = "데이터 수집 코드 파일을 실행하는 함수")
def execute_py(path = code_path):
    if not code_path.exists():
        raise HTTPException(status_code = 500, detail=f"File not Found: {code_path}")
    try:
        result = subprocess.run(
            ['python', str(code_path)]
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Script Execution Failed: {e}")