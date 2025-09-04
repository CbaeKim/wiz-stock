#!/bin/bash
# 매일 오후 4시에 실행되는 자동 채점 스크립트

cd /path/to/your/project
python data/GradePredictions.py

# 또는 API 호출 방식
# curl -X POST http://localhost:8000/stock-predict/grade-predictions