document.addEventListener('DOMContentLoaded', () => {
    const mainEventList = document.getElementById('main-event-list');
    const dailyCheckinPage = document.getElementById('daily-checkin-page');
    const numberGamePage = document.getElementById('number-game-page');
    const adWatchPage = document.getElementById('ad-watch-page');

    // 페이지 전환 함수
    function showPage(page) {
        mainEventList.style.display = 'none';
        dailyCheckinPage.style.display = 'none';
        numberGamePage.style.display = 'none';
        adWatchPage.style.display = 'none';
        page.style.display = 'block';
    }

    // 메인으로 돌아가는 함수
    function showMain() {
        mainEventList.style.display = 'block';
        dailyCheckinPage.style.display = 'none';
        numberGamePage.style.display = 'none';
        adWatchPage.style.display = 'none';
    }

    // 이벤트 카드 클릭 리스너
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

    // 뒤로가기 버튼 클릭 리스너
    document.querySelectorAll('.back-btn').forEach(btn => {
        btn.addEventListener('click', showMain);
    });

    // --- 일일 출석 체크 로직 ---
    const checkinCalendar = document.getElementById('checkin-calendar');
    const checkinState = {
        currentDay: new Date().getDay(),
        isCheckinDone: false,
        rewards: [1, 1, 1, 1, 1, 1, 1]
    };

    function renderCheckinCalendar() {
        checkinCalendar.innerHTML = '';
        for (let i = 0; i < 7; i++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'checkin-day';
            const point = checkinState.rewards[i];
            
            dayElement.innerHTML = `
                <span class="day-number">${i + 1}일차</span>
                <span class="day-reward">+${point}P</span>
            `;

            if (i === checkinState.currentDay) {
                dayElement.classList.add('today');
            }

            if (i < checkinState.currentDay || (i === checkinState.currentDay && checkinState.isCheckinDone)) {
                dayElement.classList.add('checked');
                dayElement.innerHTML += '<span class="check-mark">✅</span>';
            }
            
            dayElement.addEventListener('click', () => {
                if (i === checkinState.currentDay && !checkinState.isCheckinDone) {
                    checkinState.isCheckinDone = true;
                    let totalPoints = 1;
                    let message = `${i + 1}일차 출석 체크 완료! 1 포인트를 적립했습니다.`;
                    
                    if (i === 6) {
                        totalPoints += 10;
                        message += `\n7일 연속 출석 보너스 10포인트가 추가로 적립되었습니다!`;
                    }
                    
                    alert(message);
                    renderCheckinCalendar();
                } else if (i === checkinState.currentDay && checkinState.isCheckinDone) {
                    alert('이미 오늘의 출석을 완료했습니다.');
                } else {
                    alert('오늘은 이 날이 아닙니다!');
                }
            });
            
            checkinCalendar.appendChild(dayElement);
        }
    }

    // --- 숫자 맞추기 게임 로직 ---
    const chancesLeftSpan = document.getElementById('chances-left');
    const numberInput = document.getElementById('number-input');
    const guessBtn = document.getElementById('guess-btn');
    const gameResult = document.getElementById('game-result');
    let chances = 5;
    let randomNumber;

    function setupNumberGame() {
        randomNumber = Math.floor(Math.random() * 100) + 1;
        chances = 5;
        chancesLeftSpan.textContent = chances;
        numberInput.value = '';
        gameResult.textContent = '';
        numberInput.disabled = false;
        guessBtn.disabled = false;
    }

    guessBtn.addEventListener('click', () => {
        const userGuess = parseInt(numberInput.value, 10);
        
        if (isNaN(userGuess) || userGuess < 1 || userGuess > 100) {
            gameResult.textContent = '1부터 100 사이의 숫자를 입력해주세요.';
            gameResult.className = 'game-result';
            return;
        }

        chances--;
        chancesLeftSpan.textContent = chances;

        if (userGuess === randomNumber) {
            const reward = 10;
            gameResult.textContent = `정답입니다! 🎉 ${reward} 포인트를 획득했습니다.`;
            gameResult.className = 'game-result correct';
            numberInput.disabled = true;
            guessBtn.disabled = true;
        } else if (chances === 0) {
            gameResult.textContent = `아쉽습니다. 정답은 ${randomNumber}였습니다. 다음 기회에!`;
            gameResult.className = 'game-result down';
            numberInput.disabled = true;
            guessBtn.disabled = true;
        } else if (userGuess < randomNumber) {
            gameResult.textContent = 'UP! 더 큰 수를 입력해주세요.';
            gameResult.className = 'game-result up';
        } else {
            gameResult.textContent = 'DOWN! 더 작은 수를 입력해주세요.';
            gameResult.className = 'game-result down';
        }
    });

    // --- 광고 시청 로직 ---
    const videoThumbnail = document.getElementById('video-thumbnail');
    const playButton = document.getElementById('play-button');
    const videoOverlay = document.getElementById('video-overlay');
    const adReward = 5;
    const maxAdWatches = 3;
    let adTimer;
    
    let adWatchCount = 0;
    let lastWatchDate = new Date().toDateString();

    function updateOverlayContent(currentTimerValue) {
        if (adWatchCount >= maxAdWatches) {
            videoOverlay.innerHTML = `<span style="color: #ef4444; text-align: center;">오늘 참여 가능한 광고 시청 횟수를 모두 소진했습니다.</span>`;
        } else if (currentTimerValue > 0) {
            videoOverlay.innerHTML = `<span id="ad-timer">${currentTimerValue}</span><p>초 후 포인트 적립</p>`;
        } else {
            videoOverlay.innerHTML = `<span class="reward-message">적립 완료! (+${adReward}P)</span>`;
            videoOverlay.innerHTML += `<p style="font-size:0.9rem; margin-top:10px;">남은 참여 횟수: ${maxAdWatches - adWatchCount}회</p>`;
        }
    }

    function setupAdWatch() {
        if (new Date().toDateString() !== lastWatchDate) {
            adWatchCount = 0;
            lastWatchDate = new Date().toDateString();
        }

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
        if (adWatchCount >= maxAdWatches) {
            alert('오늘 참여 가능한 광고 시청 횟수를 모두 소진했습니다.');
            return;
        }

        if (!adTimer) {
            videoThumbnail.style.backgroundImage = 'url("https://i.ytimg.com/vi/1_1234_abc/maxresdefault.jpg")';
            playButton.style.display = 'none';
            videoOverlay.style.display = 'flex';
            
            let timerValue = 30;
            updateOverlayContent(timerValue);

            adTimer = setInterval(() => {
                timerValue--;
                updateOverlayContent(timerValue);

                if (timerValue <= 0) {
                    clearInterval(adTimer);
                    adTimer = null;
                    adWatchCount++;
                    alert(`광고 시청 완료! ${adReward} 포인트를 적립했습니다.`);
                    videoThumbnail.style.backgroundImage = 'url("https://i.ytimg.com/vi/1_1234_abc/maxresdefault.jpg")';
                }
            }, 1000);
        }
    });
});