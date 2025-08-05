### 사이드바 : 랭킹 시스템 함수

import streamlit as st
from datetime import date, timedelta, datetime
import pandas as pd

def get_or_create_weekly_ranking_data():
    """
    주간 랭킹 데이터를 가져오거나 초기화.
    매주 월요일을 시작으로 새로운 주간 랭킹 데이터를 생성.
    """
    if "weekly_rankings" not in st.session_state:
        st.session_state.weekly_rankings = {}
    
    today = date.today()
    # 월요일이 0, 일요일이 6
    start_of_week = today - timedelta(days=today.weekday())
    
    if start_of_week not in st.session_state.weekly_rankings:
        st.session_state.weekly_rankings[start_of_week] = {}
        
    return st.session_state.weekly_rankings[start_of_week]

def update_user_points(user_id, points_to_add):
    """
    사용자의 주간 포인트를 업데이트하고 총 포인트를 증가
        user_id (str): 사용자의 고유 ID (예: st.session_state.user_id)
        points_to_add (int): 추가할 포인트
    """
    # 총 포인트 업데이트
    st.session_state.points += points_to_add

    # 주간 랭킹 포인트 업데이트
    weekly_rankings = get_or_create_weekly_ranking_data()
    
    if user_id not in weekly_rankings:
        weekly_rankings[user_id] = {"points": 0, "nickname": st.session_state.get("nickname", user_id)}
    
    weekly_rankings[user_id]["points"] += points_to_add
    
def award_weekly_points():
    """
    매주 일요일 자정 기준으로 TOP 5에게 보너스 포인트를 지급
    사용자가 페이지에 접속했을 때만 실행
    """
    today = datetime.now().date()
    current_week = today.isocalendar()[1]
    
    # 세션 상태 초기화
    if "last_payout_week" not in st.session_state:
        st.session_state.last_payout_week = -1 # 아직 지급되지 않은 상태로 초기화

    # 일요일 자정 이후 아직 지급되지 않았을 경우
    if today.weekday() == 6 and st.session_state.last_payout_week != current_week:
        weekly_rankings = get_or_create_weekly_ranking_data()
        if weekly_rankings:
            # 랭킹 데이터 정렬
            sorted_rankings = sorted(weekly_rankings.items(), key=lambda item: item[1]["points"], reverse=True)
            top_5 = sorted_rankings[:5]

            st.markdown("---")
            st.success("🎉 주간 랭킹 보너스 포인트가 지급되었습니다!")

            for rank, (user_id, data) in enumerate(top_5, 1):
                bonus = 0
                if rank == 1: bonus = 500
                elif rank == 2: bonus = 300
                elif rank == 3: bonus = 200
                else: bonus = 100
                
                # 본인에게만 알림 표시
                if user_id == st.session_state.user_id:
                    st.session_state.points += bonus
                    st.info(f"🏆 주간 랭킹 TOP {rank} 달성! 보너스 포인트 {bonus}점을 획득했습니다!")
                    st.toast(f"🎉 주간 랭킹 TOP {rank} 달성! 보너스 포인트 {bonus}점 획득!")
                
            st.session_state.last_payout_week = current_week

def display_ranking_sidebar():
    """
    Streamlit 사이드바에 주간 랭킹을 표시
    """
    weekly_rankings = get_or_create_weekly_ranking_data()
    
    st.sidebar.markdown("### 🏆 주간 포인트 랭킹")
    
    # 랭킹 데이터가 있을 경우
    if weekly_rankings:
        # 포인트 기준으로 내림차순 정렬
        sorted_rankings = sorted(weekly_rankings.items(), key=lambda item: item[1]["points"], reverse=True)
        
        ranking_data = []
        for i, (user_id, data) in enumerate(sorted_rankings):
            rank = i + 1
            ranking_data.append({
                "순위": rank,
                "닉네임": data["nickname"],
                "포인트": data["points"]
            })
        
        df = pd.DataFrame(ranking_data)
        df.set_index("순위", inplace=True)
        st.sidebar.dataframe(df)

        # 현재 사용자 랭킹 표시
        current_user_rank = next((i + 1 for i, (uid, _) in enumerate(sorted_rankings) if uid == st.session_state.user_id), None)
        if current_user_rank:
            st.sidebar.info(f"내 랭킹: {current_user_rank}위")
    else:
        st.sidebar.write("아직 랭킹 데이터가 없습니다. 퀴즈를 풀어 포인트를 획득하세요!")
