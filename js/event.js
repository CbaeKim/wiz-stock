document.addEventListener('DOMContentLoaded', () => {
    const mainEventList = document.getElementById('main-event-list');
    const dailyCheckinPage = document.getElementById('daily-checkin-page');
    const numberGamePage = document.getElementById('number-game-page');
    const adWatchPage = document.getElementById('ad-watch-page');

    // --- 백엔드 연동을 위한 전역 변수 ---
    const USER_ID = localStorage.getItem('user_id'); // 로그인 시 저장된 사용자 ID 가져오기
    if (!USER_ID) {
        alert('로그인이 필요합니다.');
        window.location.href = '/pages/login.html'; // 로그인 페이지로 리디렉션
        return;
    }

    // 사용자 이벤트 상태를 저장할 객체
    let userEventStatus = {};

    // --- 페이지 전환 함수---
    function showPage(page) {
        mainEventList.style.display = 'none';
        dailyCheckinPage.style.display = 'none';
        numberGamePage.style.display = 'none';
        adWatchPage.style.display = 'none';
        page.style.display = 'block';
    }

    function showMain() {
        mainEventList.style.display = 'block';
        dailyCheckinPage.style.display = 'none';
        numberGamePage.style.display = 'none';
        adWatchPage.style.display = 'none';
    }

    // --- 이벤트 카드 클릭 리스너  ---
    document.querySelectorAll('.event-card').forEach(card => {
        card.addEventListener('click', (e) => {
            const eventType = e.currentTarget.dataset.event;
            if (eventType === 'dailyCheckin') {
                showPage(dailyCheckinPage);
                renderCheckinCalendar();
            } else if (eventType === 'numberGame') {
                showPage(numberGamePage);
                setupNumberGame();
            } else if (eventType === 'adWatch') {
                showPage(adWatchPage);
                setupAdWatch();
            }
        });
    });
    
    // --- 뒤로가기 버튼 클릭 리스너 ---
    document.querySelectorAll('.back-btn').forEach(btn => {
        btn.addEventListener('click', showMain);
    });

    // --- 일일 출석 체크 로직 ---
    const checkinCalendar = document.getElementById('checkin-calendar');
    
    function renderCheckinCalendar() {
        checkinCalendar.innerHTML = '';
        const consecutiveDays = userEventStatus.consecutive_days || 0;
        
        for (let i = 0; i < 7; i++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'checkin-day';
            const point = (i === 6) ? 11 : 1; // 7일차는 보너스 포함
            
            dayElement.innerHTML = `
                <span class="day-number">${i + 1}일차</span>
                <span class="day-reward">+${point}P</span>
            `;

            // 서버 데이터 기준으로 '출석 완료' 상태 표시
            if (i < consecutiveDays) {
                dayElement.classList.add('checked');
                dayElement.innerHTML += '<span class="check-mark">✅</span>';
            }

            // 오늘 출석해야 할 날 표시
            if (i === consecutiveDays && !userEventStatus.attendance_participate) {
                dayElement.classList.add('today');
            }
            
            // 이미 오늘 출석을 완료한 경우
            if (i === consecutiveDays - 1 && userEventStatus.attendance_participate) {
                 dayElement.classList.add('checked');
                 dayElement.innerHTML += '<span class="check-mark">✅</span>';
            }

            dayElement.addEventListener('click', async () => {
                // 오늘 출석해야 할 날이고, 아직 출석하지 않았을 때만 API 호출
                if (i === consecutiveDays && !userEventStatus.attendance_participate) {
                    try {
                        const response = await fetch('/point/attendance', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: USER_ID })
                        });

                        const data = await response.json();

                        if (!response.ok) {
                            throw new Error(data.detail || '출석 체크에 실패했습니다.');
                        }
                        
                        alert(data.message + (data.bonus_message ? `\n${data.bonus_message}` : ''));
                        
                        // 성공 시, 최신 상태를 다시 불러와서 화면 갱신
                        await loadUserEventStatus();
                        renderCheckinCalendar();

                    } catch (error) {
                        console.error('Error during check-in:', error);
                        alert(error.message);
                    }
                } else if (userEventStatus.attendance_participate) {
                    alert('오늘은 이미 출석을 완료했습니다.');
                } else {
                    alert('출석할 수 있는 날이 아닙니다.');
                }
            });
            checkinCalendar.appendChild(dayElement);
        }
    }

    // ---  숫자 맞추기 게임 로직 ---
    const chancesLeftSpan = document.getElementById('chances-left');
    const numberInput = document.getElementById('number-input');
    const guessBtn = document.getElementById('guess-btn');
    const gameResult = document.getElementById('game-result');
    let chances = 5;
    let randomNumber;

    function setupNumberGame() {
        if (userEventStatus.dailygame_participate) {
            gameResult.textContent = '오늘은 이미 게임에 참여했습니다.';
            gameResult.className = 'game-result';
            numberInput.disabled = true;
            guessBtn.disabled = true;
            return;
        }

        randomNumber = Math.floor(Math.random() * 100) + 1;
        chances = 5;
        chancesLeftSpan.textContent = chances;
        numberInput.value = '';
        gameResult.textContent = '';
        numberInput.disabled = false;
        guessBtn.disabled = false;
    }

    async function handleGameEnd(won) {
        numberInput.disabled = true;
        guessBtn.disabled = true;

        try {
            const response = await fetch('/point/game-result', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: USER_ID, won: won })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail);

            // 서버 메시지를 화면에 표시
            if (won) {
                gameResult.textContent = `정답입니다! 🎉 ${data.message}`;
                gameResult.className = 'game-result correct';
            } else {
                gameResult.textContent = `아쉽습니다. 정답은 ${randomNumber}였습니다. ${data.message}`;
                gameResult.className = 'game-result down';
            }
            // 게임 참여 후 상태 갱신
            await loadUserEventStatus();

        } catch (error) {
            alert(error.message);
        }
    }
    
    guessBtn.addEventListener('click', () => {
        const userGuess = parseInt(numberInput.value, 10);
        if (isNaN(userGuess) || userGuess < 1 || userGuess > 100) {
            gameResult.textContent = '1부터 100 사이의 숫자를 입력해주세요.';
            return;
        }

        chances--;
        chancesLeftSpan.textContent = chances;

        if (userGuess === randomNumber) {
            handleGameEnd(true); // 게임 승리
        } else if (chances === 0) {
            handleGameEnd(false); // 게임 패배
        } else if (userGuess < randomNumber) {
            gameResult.textContent = 'UP! 더 큰 수를 입력해주세요.';
            gameResult.className = 'game-result up';
        } else {
            gameResult.textContent = 'DOWN! 더 작은 수를 입력해주세요.';
            gameResult.className = 'game-result down';
        }
    });

    // ---  광고 시청 로직 ---
    const videoThumbnail = document.getElementById('video-thumbnail');
    const playButton = document.getElementById('play-button');
    const videoOverlay = document.getElementById('video-overlay');
    const adReward = 5;
    const maxAdWatches = 3;
    let adTimer;

    function updateOverlayContent(currentTimerValue) {
        const adWatchCount = userEventStatus.ad_participation || 0;
        if (adWatchCount >= maxAdWatches) {
            videoOverlay.innerHTML = `<span style="color: #ef4444; text-align: center;">오늘 참여 가능한 광고 시청 횟수를 모두 소진했습니다.</span>`;
        } else if (currentTimerValue > 0) {
            videoOverlay.innerHTML = `<span id="ad-timer">${currentTimerValue}</span><p>초 후 포인트 적립</p>`;
        } else {
            videoOverlay.innerHTML = `<span class="reward-message">적립 완료! (+${adReward}P)</span>`;
            videoOverlay.innerHTML += `<p style="font-size:0.9rem; margin-top:10px;">남은 참여 횟수: ${maxAdWatches - (adWatchCount + 1)}회</p>`;
        }
    }

    function setupAdWatch() {
        const adWatchCount = userEventStatus.ad_participation || 0;
        if (adTimer) {
            clearInterval(adTimer);
            adTimer = null;
        }
        
        videoThumbnail.style.backgroundImage = 'url("https://i.ytimg.com/vi/1_1234_abc/maxresdefault.jpg")';
        playButton.style.display = 'block';
        videoOverlay.style.display = 'none';

        if (adWatchCount >= maxAdWatches) {
            videoThumbnail.style.backgroundImage = 'none';
            videoThumbnail.style.backgroundColor = '#444';
            playButton.style.display = 'none';
            videoOverlay.style.display = 'flex';
            updateOverlayContent(0);
        }
    }

    videoThumbnail.addEventListener('click', () => {
        const adWatchCount = userEventStatus.ad_participation || 0;
        if (adWatchCount >= maxAdWatches) {
            alert('오늘 참여 가능한 광고 시청 횟수를 모두 소진했습니다.');
            return;
        }

        if (!adTimer) {
            playButton.style.display = 'none';
            videoOverlay.style.display = 'flex';
            
            let timerValue = 30;
            updateOverlayContent(timerValue);

            adTimer = setInterval(async () => {
                timerValue--;
                updateOverlayContent(timerValue);

                if (timerValue <= 0) {
                    clearInterval(adTimer);
                    adTimer = null;
                    
                    try {
                        const response = await fetch('/point/gain/ad', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: USER_ID })
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.detail);

                        alert(`광고 시청 완료! ${adReward} 포인트를 적립했습니다.`);
                        
                        // 상태 갱신 및 UI 재설정
                        await loadUserEventStatus();
                        setupAdWatch();

                    } catch (error) {
                        alert(error.message);
                        setupAdWatch(); // 실패 시에도 UI는 리셋
                    }
                }
            }, 1000);
        }
    });

    // --- 페이지 로드 시 사용자 이벤트 상태를 가져오는 함수 ---
    async function loadUserEventStatus() {
        try {
            const response = await fetch(`/point/${USER_ID}/status`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || '사용자 정보를 불러오는데 실패했습니다.');
            }
            userEventStatus = data; // 전역 변수에 상태 저장
        } catch (error) {
            console.error('Failed to load user status:', error);
            alert(error.message);
        }
    }

    // --- 페이지 최초 진입 시 초기화 함수 실행 ---
    async function initializePage() {
        await loadUserEventStatus();
        // 초기화 함수들을 여기서 호출할 수 있습니다.
        // 예를 들어, 메인 화면의 카드에 오늘 참여했는지 여부를 표시하는 등의 로직 추가 가능
    }

    initializePage();
});