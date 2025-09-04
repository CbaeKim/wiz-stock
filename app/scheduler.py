from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import subprocess
from pathlib import Path

scheduler = AsyncIOScheduler()

async def run_daily_grading():
    """매일 오후 4시에 자동 채점 실행"""
    try:
        project_root = Path(__file__).parent.parent
        script_path = project_root / "data" / "GradePredictions.py"
        
        result = subprocess.run(
            ["python", str(script_path)], 
            capture_output=True, 
            text=True,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            print(f"[SCHEDULER] 자동 채점 성공: {result.stdout}")
        else:
            print(f"[SCHEDULER] 자동 채점 실패: {result.stderr}")
            
    except Exception as e:
        print(f"[SCHEDULER] 스케줄러 오류: {e}")

def start_scheduler():
    """스케줄러 시작"""
    # 매일 오후 4시에 실행
    scheduler.add_job(
        run_daily_grading,
        CronTrigger(hour=16, minute=0),  # 16:00
        id="daily_grading",
        replace_existing=True
    )
    
    scheduler.start()
    print("[SCHEDULER] 일일 채점 스케줄러가 시작되었습니다. (매일 16:00)")

def stop_scheduler():
    """스케줄러 중지"""
    scheduler.shutdown()