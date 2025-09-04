document.addEventListener('DOMContentLoaded', () => {
    // DOM 요소들 - 메뉴
    const mainMenu = document.getElementById('main-menu');
    const historyView = document.getElementById('history-view');
    const predictionGame = document.getElementById('prediction-game');
    
    const startPredictionBtn = document.getElementById('start-prediction');
    const viewHistoryBtn = document.getElementById('view-history');
    const backFromHistoryBtn = document.getElementById('back-from-history');
    const backFromGameBtn = document.getElementById('back-from-game');
    // 테스트 버튼들 제거됨
    
    // DOM 요소들 - 게임
    const predictionButtons = document.querySelectorAll('.prediction-btn');
    const submitBtn = document.getElementById('submit-prediction');
    // const resetBtn = document.getElementById('reset-game'); // 제거됨
    const resultSection = document.getElementById('result-section');
    const userTextarea = document.getElementById('user-prediction');
    
    // 게임 상태
    let selectedPrediction = null;
    let gameSubmitted = false;
    let aiPredictionData = null;
    
    // 예측 기록 데이터
    let predictionHistoryData = null;
    
    // 메뉴 네비게이션 이벤트
    startPredictionBtn.addEventListener('click', () => {
        showPredictionGame();
    });
    
    viewHistoryBtn.addEventListener('click', async () => {
        await loadPredictionHistory();
        showHistoryView();
    });
    
    // 테스트 함수들 제거됨
    
    // 포인트 수령 함수
    async function claimPoints(predictionId, buttonElement) {
        try {
            console.log('포인트 수령 시작:', predictionId);
            
            const response = await fetch('/stock-predict/claim-points', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prediction_id: predictionId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '포인트 수령에 실패했습니다.');
            }
            
            const result = await response.json();
            console.log('포인트 수령 성공:', result);
            
            // 버튼을 수령 완료 상태로 변경
            const pointsSection = buttonElement.parentElement;
            pointsSection.className = 'points-section received';
            pointsSection.innerHTML = `
                <span class="points-text">포인트 수령 완료: ${result.points_awarded}점</span>
            `;
            
            alert(`${result.message}\n총 포인트: ${result.total_points}점`);
            
        } catch (error) {
            console.error('포인트 수령 실패:', error);
            alert(`포인트 수령 실패: ${error.message}`);
        }
    }
    
    // 테스트 함수들 및 window 객체 할당 제거됨
    
    backFromHistoryBtn.addEventListener('click', () => {
        showMainMenu();
    });
    
    backFromGameBtn.addEventListener('click', () => {
        showMainMenu();
    });
    
    // 테스트 버튼 이벤트 리스너들 제거됨
    
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
    
    async function showPredictionGame() {
        mainMenu.style.display = 'none';
        historyView.style.display = 'none';
        predictionGame.style.display = 'block';
        await loadGameData();
    }
    
    // 예측 기록 API 호출
    async function loadPredictionHistory() {
        try {
            // 로컬스토리지에서 사용자 ID 가져오기 (로그인 시스템과 연동)
            const userId = localStorage.getItem('user_id') || 'test_user';
            console.log('사용자 ID:', userId);
            
            const url = `/stock-predict/get-history?user_id=${userId}`;
            console.log('API 호출 URL:', url);
            
            const response = await fetch(url);
            console.log('응답 상태:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API 에러 응답:', errorText);
                throw new Error(`예측 기록을 가져오는데 실패했습니다. 상태: ${response.status}`);
            }
            
            predictionHistoryData = await response.json();
            console.log('예측 기록 로드 완료:', predictionHistoryData);
        } catch (error) {
            console.error('예측 기록 로드 실패:', error);
            alert(`예측 기록 로드 실패: ${error.message}`);
            // 에러 시 기본 데이터 사용
            predictionHistoryData = {
                total_predictions: 0,
                correct_predictions: 0,
                accuracy_rate: 0,
                history: []
            };
        }
    }

    // 예측 기록 렌더링
    function renderHistoryView() {
        if (!predictionHistoryData) {
            console.error('예측 기록 데이터가 없습니다.');
            return;
        }
        
        // 통계 업데이트
        document.getElementById('total-predictions').textContent = predictionHistoryData.total_predictions;
        document.getElementById('accuracy-rate').textContent = `${predictionHistoryData.accuracy_rate}%`;
        document.getElementById('correct-predictions').textContent = predictionHistoryData.correct_predictions;
        
        // 기록 목록 렌더링
        const historyItemsContainer = document.getElementById('history-items');
        historyItemsContainer.innerHTML = '';
        
        if (predictionHistoryData.history.length === 0) {
            historyItemsContainer.innerHTML = `
                <div class="no-history">
                    <p>아직 예측 기록이 없습니다.</p>
                    <p>주가 예측 게임에 참여해보세요!</p>
                </div>
            `;
            return;
        }
        
        predictionHistoryData.history.forEach(item => {
            const historyItem = document.createElement('div');
            
            // 날짜 포맷팅
            const predictionDate = new Date(item.prediction_date).toLocaleDateString('ko-KR');
            
            // 결과 상태 결정
            let resultStatus = 'pending';
            let resultText = '결과 대기중';
            let pointsSection = '';
            
            if (item.is_checked) {
                resultStatus = item.is_correct ? 'correct' : 'incorrect';
                resultText = item.is_correct ? '✓ 정답' : '✗ 오답';
                
                // 포인트 관련 섹션
                if (item.points_awarded !== null && item.points_awarded !== undefined) {
                    // 이미 포인트를 받은 경우
                    pointsSection = `
                        <div class="points-section received">
                            <span class="points-text">포인트 수령 완료: ${item.points_awarded}점</span>
                        </div>
                    `;
                } else {
                    // 포인트를 아직 받지 않은 경우
                    const expectedPoints = item.is_correct ? 10 : 5;
                    pointsSection = `
                        <div class="points-section">
                            <span class="points-text">획득 가능 포인트: ${expectedPoints}점</span>
                            <button class="claim-points-btn" data-prediction-id="${item.id}">
                                포인트 받기
                            </button>
                        </div>
                    `;
                }
            }
            
            historyItem.className = `history-item ${resultStatus}`;
            
            historyItem.innerHTML = `
                <div class="history-item-header">
                    <span class="history-date">${predictionDate}</span>
                    <span class="history-result ${resultStatus}">
                        ${resultText}
                    </span>
                </div>
                <div class="history-stock">
                    종목: ${item.stock_name} (${item.stock_code})
                </div>
                <div class="history-prediction">
                    예측: ${item.predicted_trend === '상승' || item.predicted_trend === 'up' ? '📈 상승' : '📉 하락'}
                </div>
                <div class="history-reasoning">
                    "${item.reasoning || '예측 근거 없음'}"
                </div>
                ${pointsSection}
            `;
            
            historyItemsContainer.appendChild(historyItem);
        });
        
        // 포인트 받기 버튼 이벤트 리스너 추가
        document.querySelectorAll('.claim-points-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const predictionId = e.target.getAttribute('data-prediction-id');
                await claimPoints(predictionId, e.target);
            });
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
    
    // 다시 예측하기 버튼 제거됨
    
    // 예측 제출 함수
    async function submitPrediction() {
        try {
            // 사용자 ID 가져오기
            const userId = localStorage.getItem('user_id') || 'test_user';
            const reasoning = userTextarea.value.trim();
            
            // API 호출하여 예측 제출
            const response = await fetch('/stock-predict/submit-prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    stock_code: '005930', // 삼성전자 고정
                    user_predict_trend: selectedPrediction,
                    reasoning: reasoning
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '예측 제출에 실패했습니다.');
            }
            
            const result = await response.json();
            console.log('예측 제출 성공:', result);
            
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
            
            // 결과 섹션으로 스크롤
            setTimeout(() => {
                resultSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 300);
            
        } catch (error) {
            console.error('예측 제출 실패:', error);
            alert(error.message);
        }
    }
    
    // 게임 데이터 로드 함수
    async function loadGameData() {
        try {
            const userId = localStorage.getItem('user_id') || 'test_user';
            console.log('게임 데이터 로드 시작...');
            
            const response = await fetch(`/stock-predict/get-game-data?user_id=${userId}`);
            
            if (!response.ok) {
                throw new Error(`게임 데이터 로드 실패: ${response.status}`);
            }
            
            const gameData = await response.json();
            console.log('게임 데이터 로드 완료:', gameData);
            
            // 참여 가능 여부 확인
            if (!gameData.can_participate) {
                alert('오늘은 이미 게임에 참여하셨습니다. 내일 다시 참여해주세요!');
                showMainMenu();
                return;
            }
            
            // UI 업데이트
            updateGameUI(gameData);
            
        } catch (error) {
            console.error('게임 데이터 로드 실패:', error);
            alert(`게임 데이터 로드 실패: ${error.message}`);
            showMainMenu();
        }
    }
    
    // 게임 UI 업데이트 함수
    function updateGameUI(gameData) {
        const { stock_info, ai_prediction, sentiment_analysis } = gameData;
        
        // 현재가 업데이트
        document.getElementById('current-price').textContent = `${stock_info.current_price.toLocaleString()}원`;
        
        // 감성분석 결과 업데이트
        document.getElementById('news-sentiment').textContent = sentiment_analysis.outlook;
        
        // AI 예측 정보 업데이트 - 이전 예측가
        if (ai_prediction.prev_price_predict) {
            document.getElementById('ai-prev-price').textContent = `${ai_prediction.prev_price_predict.toLocaleString()}원`;
        } else {
            document.getElementById('ai-prev-price').textContent = '이전 예측 데이터 없음';
        }
        
        if (ai_prediction.price_predict) {
            document.getElementById('ai-today-price').textContent = `${ai_prediction.price_predict.toLocaleString()}원`;
            
            // AI 예측가 색상 설정
            const aiTodayElement = document.getElementById('ai-today-price');
            if (ai_prediction.price_predict > stock_info.current_price) {
                aiTodayElement.style.color = '#10b981'; // 상승 - 초록색
            } else if (ai_prediction.price_predict < stock_info.current_price) {
                aiTodayElement.style.color = '#ef4444'; // 하락 - 빨간색
            } else {
                aiTodayElement.style.color = '#fbbf24'; // 동일 - 노란색
            }
        } else {
            document.getElementById('ai-today-price').textContent = '예측 데이터 없음';
        }
        
        // AI 예측 데이터 저장 (결과 비교용)
        aiPredictionData = {
            sentiment: sentiment_analysis.outlook,
            prevPrice: stock_info.current_price,
            predictedPrice: ai_prediction.price_predict || stock_info.current_price,
            direction: ai_prediction.trend_predict === '상승' ? 'up' : 'down',
            topFeature: ai_prediction.top_feature
        };
        
        console.log('게임 UI 업데이트 완료:', aiPredictionData);
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
    async function resetGame() {
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
        
        // 새로운 게임 데이터 로드
        await loadGameData();
        
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