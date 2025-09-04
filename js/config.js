/**
 * 전역 설정 파일
 */

// API 기본 URL 설정
window.API = window.API || "";

// 환경별 설정
const CONFIG = {
  // API 업데이트 간격 (밀리초)
  RANKING_UPDATE_INTERVAL: 30000, // 30초
  
  // 기본 순위 표시 개수
  DEFAULT_RANKING_LIMIT: 5,
  
  // 로컬 스토리지 키
  STORAGE_KEYS: {
    USER_ID: 'user_id',
    NICKNAME: 'nickname',
    POINTS: 'points'
  },
  
  // 페이지 경로
  PAGES: {
    LOGIN: '/pages/login.html',
    HOME: '/index.html'
  }
};

// 전역으로 설정 객체 노출
window.CONFIG = CONFIG;