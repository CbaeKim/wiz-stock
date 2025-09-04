/**
 * 세션 관리 및 자동 로그아웃 기능
 * 30분 비활성 시 자동 로그아웃
 */

class SessionManager {
    constructor() {
        this.TIMEOUT_DURATION = 30 * 60 * 1000; // 30분 (밀리초)
        this.WARNING_DURATION = 5 * 60 * 1000;  // 5분 전 경고 (밀리초)
        this.timeoutId = null;
        this.warningTimeoutId = null;
        this.lastActivityTime = Date.now();
        this.isWarningShown = false;

        this.init();
    }

    init() {
        // 로그인 상태 확인
        if (!this.isLoggedIn()) {
            return;
        }

        // 활동 감지 이벤트 등록
        this.registerActivityEvents();

        // 타이머 시작
        this.resetTimer();

        console.log('[SessionManager] 세션 관리 시작 - 30분 후 자동 로그아웃');
    }

    isLoggedIn() {
        const userId = localStorage.getItem(window.CONFIG?.STORAGE_KEYS?.USER_ID || 'user_id');
        return !!userId;
    }

    registerActivityEvents() {
        // 사용자 활동을 감지할 이벤트들
        const events = [
            'mousedown', 'mousemove', 'keypress', 'scroll',
            'touchstart', 'click', 'focus', 'blur'
        ];

        events.forEach(event => {
            document.addEventListener(event, () => {
                this.onActivity();
            }, true);
        });

        // 페이지 가시성 변경 감지 (탭 전환 등)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.onActivity();
            }
        });
    }

    onActivity() {
        this.lastActivityTime = Date.now();

        // 경고가 표시된 상태라면 숨기기
        if (this.isWarningShown) {
            this.hideWarning();
        }

        // 타이머 리셋
        this.resetTimer();
    }

    resetTimer() {
        // 기존 타이머 제거
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        if (this.warningTimeoutId) {
            clearTimeout(this.warningTimeoutId);
        }

        // 경고 타이머 설정 (25분 후)
        this.warningTimeoutId = setTimeout(() => {
            this.showWarning();
        }, this.TIMEOUT_DURATION - this.WARNING_DURATION);

        // 로그아웃 타이머 설정 (30분 후)
        this.timeoutId = setTimeout(() => {
            this.autoLogout();
        }, this.TIMEOUT_DURATION);
    }

    showWarning() {
        if (this.isWarningShown) return;

        this.isWarningShown = true;

        // 경고 모달 생성
        const modal = this.createWarningModal();
        document.body.appendChild(modal);

        console.log('[SessionManager] 5분 후 자동 로그아웃 경고 표시');
    }

    createWarningModal() {
        const modal = document.createElement('div');
        modal.id = 'session-warning-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            font-family: 'Noto Sans KR', Arial, sans-serif;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        `;

        modalContent.innerHTML = `
            <div style="color: #e74c3c; font-size: 48px; margin-bottom: 20px;">⚠️</div>
            <h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 20px;">세션 만료 경고</h3>
            <p style="color: #7f8c8d; margin-bottom: 25px; line-height: 1.5;">
                비활성 상태가 지속되어<br>
                <strong style="color: #e74c3c;">5분 후</strong> 자동 로그아웃됩니다.
            </p>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button id="extend-session-btn" style="
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                ">세션 연장</button>
                <button id="logout-now-btn" style="
                    background: #e74c3c;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                ">지금 로그아웃</button>
            </div>
        `;

        modal.appendChild(modalContent);

        // 이벤트 리스너 추가
        modal.querySelector('#extend-session-btn').addEventListener('click', () => {
            this.extendSession();
        });

        modal.querySelector('#logout-now-btn').addEventListener('click', () => {
            this.logout();
        });

        return modal;
    }

    extendSession() {
        console.log('[SessionManager] 사용자가 세션을 연장했습니다');
        this.hideWarning();
        this.onActivity(); // 활동으로 처리하여 타이머 리셋
    }

    hideWarning() {
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            modal.remove();
        }
        this.isWarningShown = false;
    }

    autoLogout() {
        console.log('[SessionManager] 30분 비활성으로 자동 로그아웃 실행');

        // 경고 모달이 있다면 제거
        this.hideWarning();

        // 로그아웃 실행
        this.logout('자동 로그아웃되었습니다.\n30분간 활동이 없어 보안을 위해 로그아웃됩니다.');
    }

    logout(message = '로그아웃되었습니다.') {
        // 로컬 스토리지 정리
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.USER_ID || 'user_id');
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.NICKNAME || 'nickname');
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.POINTS || 'points');

        // 타이머 정리
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        if (this.warningTimeoutId) {
            clearTimeout(this.warningTimeoutId);
        }

        // 사용자에게 알림
        alert(message);

        // 로그인 페이지로 리다이렉트
        window.location.href = window.CONFIG?.PAGES?.LOGIN || '/pages/login.html';
    }

    // 수동으로 세션 상태 확인 (디버깅용)
    getSessionInfo() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivityTime;
        const timeUntilLogout = this.TIMEOUT_DURATION - timeSinceLastActivity;

        return {
            lastActivity: new Date(this.lastActivityTime).toLocaleString(),
            timeSinceLastActivity: Math.floor(timeSinceLastActivity / 1000) + '초',
            timeUntilLogout: Math.floor(Math.max(0, timeUntilLogout) / 1000) + '초',
            isWarningShown: this.isWarningShown
        };
    }
}

// 전역 세션 매니저 인스턴스 생성
window.sessionManager = null;

// DOM 로드 완료 후 세션 매니저 초기화
document.addEventListener('DOMContentLoaded', () => {
    // 로그인 페이지에서는 세션 매니저를 실행하지 않음
    if (window.location.pathname.includes('login.html') ||
        window.location.pathname.includes('sign_up.html')) {
        return;
    }

    window.sessionManager = new SessionManager();
});

// 개발자 도구에서 세션 정보 확인용 함수
window.getSessionInfo = () => {
    if (window.sessionManager) {
        console.table(window.sessionManager.getSessionInfo());
    } else {
        console.log('세션 매니저가 초기화되지 않았습니다.');
    }
};