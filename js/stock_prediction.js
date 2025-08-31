document.addEventListener('DOMContentLoaded', () => {
    // DOM 요소들 - 메뉴
    const mainMenu = document.getElementById('main-menu');
    const historyView = document.getElementById('history-view');
    const predictionGame = document.getElementById('prediction-game');
    
    const startPredictionBtn = document.getElementById('start-prediction');
    const viewHistoryBtn = document.getElementById('view-history');
    const backFromHistoryBtn = document.getElementById('back-from-history');
    const backFromGameBtn = document.getElementById('back-from-game');
    
    // DOM 요소들 - 게임
    const predictionButtons = document.querySelectorAll('.prediction-btn');
    const submitBtn = document.getElementById('submit-prediction');
    const resetBtn = document.getElementById('reset-game');
    const resultSection = document.getElementById('result-section');
    const userTextarea = document.getElementById('user-prediction');
    
    // 게임 상태
    let selectedPrediction = null;
    let gameSubmitted = false;
    let aiPredictionData = null;
    
    // 예측 기록 저장소 (실제로는 서버나 로컬스토리지 사용)
    let predictionHistory = [
        {
            date: '2025-01-20',
            prediction: 'up',
            reasoning: '긍정적인 실적 발표 예상',
            aiPrediction: 'up',
            result: 'correct'
        },
        {
            date: '2025-01-19',
            prediction: 'down',
            reasoning: '시장 불안정성 증가',
            aiPrediction: 'up',
            result: 'incorrect'
        },
        {
            date: '2025-01-18',
            prediction: 'up',
            reasoning: '기술적 지표 상승 신호',
            aiPrediction: 'up',
            result: 'correct'
        },
        {
            date: '2025-01-17',
            prediction: 'up',
            reasoning: '반도체 업황 개선',
            aiPrediction: 'down',
            result: 'correct'
        },
        {
            date: '2025-01-16',
            prediction: 'down',
            reasoning: '글로벌 경기 둔화 우려',
            aiPrediction: 'down',
            result: 'correct'
        }
    ];
    
    // 메뉴 네비게이션 이벤트
    startPredictionBtn.addEventListener('click', () => {
        showPredictionGame();
    });
    
    viewHistoryBtn.addEventListener('click', () => {
        showHistoryView();
    });
    
    backFromHistoryBtn.addEventListener('click', () => {
        showMainMenu();
    });
    
    backFromGameBtn.addEventListener('click', () => {
        showMainMenu();
    });
    
    // 화면 전환 함수들
    function showMainMenu() {
        mainMenu.style.display = 'block';
        historyView.style.display = 'none';
        predictionGame.style.display = 'none';
    }
    
    function showHistoryView() {
        mainMenu.style.display = 'none';
        historyView.style.display = 'block';
        predictionGame.style.display = 'none';
        renderHistoryView();
    }
    
    function showPredictionGame() {
        mainMenu.style.display = 'none';
        historyView.style.display = 'none';
        predictionGame.style.display = 'block';
        generateAIPrediction();
    }
    
    // 예측 기록 렌더링
    function renderHistoryView() {
        const totalPredictions = predictionHistory.length;
        const correctPredictions = predictionHistory.filter(item => item.result === 'correct').length;
        const accuracyRate = Math.round((correctPredictions / totalPredictions) * 100);
        
        // 통계 업데이트
        document.getElementById('total-predictions').textContent = totalPredictions;
        document.getElementById('accuracy-rate').textContent = `${accuracyRate}%`;
        document.getElementById('correct-predictions').textContent = correctPredictions;
        
        // 기록 목록 렌더링
        const historyItemsContainer = document.getElementById('history-items');
        historyItemsContainer.innerHTML = '';
        
        predictionHistory.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = `history-item ${item.result}`;
            
            historyItem.innerHTML = `
                <div class="history-item-header">
                    <span class="history-date">${item.date}</span>
                    <span class="history-result ${item.result}">
                        ${item.result === 'correct' ? '✓ 정답' : '✗ 오답'}
                    </span>
                </div>
                <div class="history-prediction">
                    예측: ${item.prediction === 'up' ? '📈 상승' : '📉 하락'}
                    ${item.aiPrediction !== item.prediction ? '(AI와 다른 예측)' : '(AI와 동일한 예측)'}
                </div>
                <div class="history-reasoning">
                    "${item.reasoning || '예측 근거 없음'}"
                </div>
            `;
            
            historyItemsContainer.appendChild(historyItem);
        });
    }
    
    // 예측 버튼 클릭 이벤트
    predictionButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (gameSubmitted) return;
            
            // 모든 버튼에서 selected 클래스 제거
            predictionButtons.forEach(button => {
                button.classList.remove('selected');
            });
            
            // 클릭된 버튼에 selected 클래스 추가
            btn.classList.add('selected');
            selectedPrediction = btn.getAttribute('data-prediction');
            
            // 제출 버튼 활성화
            submitBtn.disabled = false;
            
            console.log('선택된 예측:', selectedPrediction);
        });
    });
    
    // 예측 제출 버튼 클릭 이벤트
    submitBtn.addEventListener('click', () => {
        if (!selectedPrediction) {
            alert('먼저 UP 또는 DOWN을 선택해주세요!');
            return;
        }
        
        // 게임 제출 처리
        submitPrediction();
    });
    
    // 다시 예측하기 버튼 클릭 이벤트
    resetBtn.addEventListener('click', () => {
        resetGame();
    });
    
    // 예측 제출 함수
    function submitPrediction() {
        gameSubmitted = true;
        
        // 버튼들 비활성화
        predictionButtons.forEach(btn => {
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.7';
        });
        
        submitBtn.disabled = true;
        submitBtn.textContent = '제출 완료';
        
        // 사용자 입력 비활성화
        userTextarea.disabled = true;
        
        // 사용자 결과 생성 및 표시
        generateUserResult();
        
        // 결과 섹션 표시
        resultSection.style.display = 'block';
        resetBtn.style.display = 'inline-block';
        
        // 결과 섹션으로 스크롤
        setTimeout(() => {
            resultSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }, 300);
    }
    
    // AI 예측 정보 생성 함수
    function generateAIPrediction() {
        const currentPrice = 62000;
        
        // 랜덤 뉴스 감성 분석 결과
        const sentiments = ['긍정적 전망', '부정적 전망', '중립적 전망', '혼재된 전망'];
        const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
        
        // AI 예측가 계산 (현재가 기준 ±500원 범위)
        const aiVariation = Math.floor(Math.random() * 1000) - 500; // -500 ~ +500
        const aiPredictedPrice = currentPrice + aiVariation;
        
        // AI 예측 방향 결정
        const aiDirection = aiPredictedPrice > currentPrice ? 'up' : 'down';
        
        aiPredictionData = {
            sentiment: randomSentiment,
            prevPrice: currentPrice,
            predictedPrice: aiPredictedPrice,
            direction: aiDirection
        };
        
        // UI 업데이트
        document.getElementById('news-sentiment').textContent = randomSentiment;
        document.getElementById('ai-prev-price').textContent = `${currentPrice.toLocaleString()}원`;
        document.getElementById('ai-today-price').textContent = `${aiPredictedPrice.toLocaleString()}원`;
        
        // AI 예측가 색상 설정
        const aiTodayElement = document.getElementById('ai-today-price');
        if (aiPredictedPrice > currentPrice) {
            aiTodayElement.style.color = '#10b981'; // 상승 - 초록색
        } else if (aiPredictedPrice < currentPrice) {
            aiTodayElement.style.color = '#ef4444'; // 하락 - 빨간색
        } else {
            aiTodayElement.style.color = '#fbbf24'; // 동일 - 노란색
        }
        
        console.log('AI 예측 생성:', aiPredictionData);
    }
    
    // 사용자 결과 생성 함수
    function generateUserResult() {
        const userText = userTextarea.value.trim();
        
        // 사용자 예측 텍스트
        const predictionText = selectedPrediction === 'up' ? '상승 예측' : '하락 예측';
        
        // 예측 근거
        const reasoning = userText || '텍스트 입력 없음';
        
        // AI와 일치도 계산
        const aiMatch = (selectedPrediction === aiPredictionData.direction) ? '일치함' : '불일치';
        
        // 결과 업데이트
        document.getElementById('user-prediction-result').textContent = predictionText;
        document.getElementById('user-reasoning').textContent = reasoning;
        document.getElementById('ai-match').textContent = aiMatch;
        
        // AI 일치도에 따른 색상 변경
        const matchElement = document.getElementById('ai-match');
        if (aiMatch === '일치함') {
            matchElement.style.color = '#10b981'; // 일치 - 초록색
        } else {
            matchElement.style.color = '#ef4444'; // 불일치 - 빨간색
        }
        
        console.log('사용자 결과 생성:', {
            prediction: selectedPrediction,
            reasoning: reasoning,
            aiMatch: aiMatch
        });
    }
    
    // 게임 리셋 함수
    function resetGame() {
        // 상태 초기화
        selectedPrediction = null;
        gameSubmitted = false;
        
        // 버튼들 초기화
        predictionButtons.forEach(btn => {
            btn.classList.remove('selected');
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        });
        
        // 제출 버튼 초기화
        submitBtn.disabled = true;
        submitBtn.textContent = '예측 제출하기';
        
        // 사용자 입력 초기화
        userTextarea.disabled = false;
        userTextarea.value = '';
        
        // 결과 섹션 숨기기
        resultSection.style.display = 'none';
        resetBtn.style.display = 'none';
        
        // 새로운 AI 예측 생성
        generateAIPrediction();
        
        // 상단으로 스크롤
        document.querySelector('.game-header').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
        console.log('게임 리셋 완료');
    }
    
    // 초기 상태 설정
    submitBtn.disabled = true;
    
    // 로그아웃 버튼 이벤트 (기존 코드와 일관성 유지)
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            alert('로그아웃 되었습니다.');
        });
    }
    
    console.log('주가 예측 게임 초기화 완료');
});