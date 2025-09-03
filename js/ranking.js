/**
 * 실시간 포인트 순위 관리 모듈
 */

class RankingManager {
  constructor() {
    this.API = window.API || "";
    this.updateInterval = window.CONFIG?.RANKING_UPDATE_INTERVAL || 30000;
    this.intervalId = null;
  }

  /**
   * 순위 시스템 초기화
   */
  init() {
    this.updateRanking();
    this.startAutoUpdate();
  }

  /**
   * 상위 포인트 순위 데이터 가져오기
   */
  async fetchTopRanking(limit = 5) {
    try {
      const response = await fetch(`${this.API}/ranking/top-points?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("순위 데이터 가져오기 실패:", error);
      return [];
    }
  }

  /**
   * 특정 사용자의 순위 정보 가져오기
   */
  async fetchUserRank(userId) {
    try {
      const response = await fetch(`${this.API}/ranking/user-rank/${userId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("사용자 순위 정보 가져오기 실패:", error);
      return null;
    }
  }

  /**
   * 순위 목록 UI 업데이트
   */
  async updateRanking() {
    const rankingList = document.querySelector('.ranking-list');
    if (!rankingList) return;

    try {
      const rankingData = await this.fetchTopRanking(5);
      
      if (rankingData.length === 0) {
        rankingList.innerHTML = '<li class="ranking-item no-data">순위 데이터가 없습니다.</li>';
        return;
      }

      rankingList.innerHTML = rankingData.map(user => `
        <li class="ranking-item">
          <span class="ranking-number">${user.rank}</span>
          <span class="user-name">${user.nickname}</span>
          <span class="user-points">${user.total_point.toLocaleString()}P</span>
        </li>
      `).join('');

    } catch (error) {
      console.error("순위 업데이트 실패:", error);
      rankingList.innerHTML = '<li class="ranking-item error">순위를 불러올 수 없습니다.</li>';
    }
  }

  /**
   * 현재 사용자의 순위 정보 업데이트
   */
  async updateUserRank() {
    const userId = localStorage.getItem(window.CONFIG?.STORAGE_KEYS?.USER_ID || 'user_id');
    if (!userId) return;

    try {
      const userRankData = await this.fetchUserRank(userId);
      if (!userRankData) return;

      // 사용자 순위 정보를 표시할 요소가 있다면 업데이트
      const userRankElement = document.querySelector('.user-rank-info');
      if (userRankElement) {
        userRankElement.innerHTML = `
          <div class="user-rank-item">
            <span class="rank-label">내 순위:</span>
            <span class="rank-value">${userRankData.rank}위</span>
          </div>
          <div class="user-rank-item">
            <span class="points-label">내 포인트:</span>
            <span class="points-value">${userRankData.total_point.toLocaleString()}P</span>
          </div>
        `;
      }

      // 로컬 스토리지에 포인트 정보 업데이트
      localStorage.setItem(window.CONFIG?.STORAGE_KEYS?.POINTS || 'points', userRankData.total_point.toString());

    } catch (error) {
      console.error("사용자 순위 업데이트 실패:", error);
    }
  }

  /**
   * 자동 업데이트 시작
   */
  startAutoUpdate() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    this.intervalId = setInterval(() => {
      this.updateRanking();
      this.updateUserRank();
    }, this.updateInterval);
  }

  /**
   * 자동 업데이트 중지
   */
  stopAutoUpdate() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  /**
   * 수동으로 순위 새로고침
   */
  async refresh() {
    await this.updateRanking();
    await this.updateUserRank();
  }
}

// 전역 인스턴스 생성
window.rankingManager = new RankingManager();

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
  window.rankingManager.init();
});

// 페이지 언로드 시 자동 업데이트 중지
window.addEventListener('beforeunload', () => {
  window.rankingManager.stopAutoUpdate();
});