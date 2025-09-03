from fastapi import APIRouter, HTTPException
from app.dependency.connect_supabase import connect_supabase
from typing import List, Dict, Any

router = APIRouter(prefix="/ranking", tags=["ranking"])

@router.get("/top-points")
async def get_top_points_ranking(limit: int = 5) -> List[Dict[str, Any]]:
    """
    보유 포인트 기준 상위 사용자 순위를 반환합니다.
    
    Args:
        limit: 반환할 순위 수 (기본값: 5)
    
    Returns:
        List[Dict]: 순위 정보 리스트
    """
    try:
        supabase = connect_supabase()
        
        # total_point 기준으로 내림차순 정렬하여 상위 사용자 조회
        # null 값을 제외하고 실제 포인트가 있는 사용자만 조회
        response = supabase.table('user_info')\
            .select('nickname, total_point')\
            .not_.is_('total_point', 'null')\
            .order('total_point', desc=True)\
            .limit(limit)\
            .execute()
        
        if not response.data:
            return []
        
        # 순위 정보 추가
        ranking_data = []
        for idx, user in enumerate(response.data, 1):
            # total_point가 null인 경우 0으로 처리
            total_point = user.get("total_point")
            if total_point is None:
                total_point = 0
            
            ranking_data.append({
                "rank": idx,
                "nickname": user.get("nickname", "익명"),
                "total_point": total_point
            })
        
        return ranking_data
        
    except Exception as e:
        print(f"Error fetching ranking data: {e}")
        raise HTTPException(status_code=500, detail="순위 데이터를 가져오는 중 오류가 발생했습니다.")

@router.get("/user-rank/{user_id}")
async def get_user_rank(user_id: str) -> Dict[str, Any]:
    """
    특정 사용자의 순위 정보를 반환합니다.
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        Dict: 사용자 순위 정보
    """
    try:
        supabase = connect_supabase()
        
        # 사용자 정보 조회
        user_response = supabase.table('user_info')\
            .select('nickname, total_point')\
            .eq('id', user_id)\
            .execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_data = user_response.data[0]
        user_points = user_data.get("total_point", 0)
        
        # 해당 사용자보다 포인트가 높은 사용자 수를 세어서 순위 계산
        rank_response = supabase.table('user_info')\
            .select('id', count='exact')\
            .gt('total_point', user_points)\
            .execute()
        
        user_rank = rank_response.count + 1 if rank_response.count is not None else 1
        
        return {
            "user_id": user_id,
            "nickname": user_data.get("nickname", "익명"),
            "total_point": user_points,
            "rank": user_rank
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user rank: {e}")
        raise HTTPException(status_code=500, detail="사용자 순위 정보를 가져오는 중 오류가 발생했습니다.")