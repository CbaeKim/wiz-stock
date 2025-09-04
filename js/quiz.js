document.addEventListener('DOMContentLoaded', () => {
    // --- 로그인 상태 확인 로직 (localStorage 사용) ---
    const userId = localStorage.getItem('user_id');

    // 'user_id'가 스토리지에 없으면 로그인 페이지로 리디렉션합니다.
    if (!userId) {
        alert('로그인이 필요한 서비스입니다.');
        window.location.href = './pages/login.html'; 
        return; // 리디렉션 후 아래 코드 실행을 중단합니다.
    }
    // --- 여기까지 ---

    // --- DOM 요소 ---
    const mainContentContainer = document.getElementById('main-content-container');

    // --- 상태 변수 ---
    let quizData = [];
    let currentQuestionIndex = 0;
    let totalPoints = 0;
    let selectedTopic = '';
    
    // --- 로그인 연동 ---
    console.log(`현재 사용자 ID: ${userId}`); // 개발자 도구 콘솔에서 확인용

    /**
     * 페이지를 초기화하고 사용자의 참여 상태를 확인합니다.
     */
    async function initializePage() {
        showLoading('참여 가능 여부를 확인 중입니다...');
        try {
            const canParticipate = await checkParticipationStatus();
            if (canParticipate) {
                // 퀴즈 참여가 가능하면 초기 화면을 렌더링합니다.
                renderInitialScreen();
            } else {
                // 이미 참여했다면 참여 완료 메시지를 보여줍니다.
                showParticipationMessage();
            }
        } catch (error) {
            console.error('Participation check failed:', error);
            showError('참여 여부를 확인하는 중 오류가 발생했습니다. 페이지를 새로고침해주세요.');
        }
    }

    /**
     * API를 호출하여 사용자의 퀴즈 참여 가능 여부를 확인합니다.
     * @returns {Promise<boolean>} 참여 가능하면 true, 아니면 false
     */
    async function checkParticipationStatus() {
        // API 경로를 절대 경로 ('/')로 시작하도록 수정
        const response = await fetch(`/quiz/check-participation?user_id=${userId}`);
        if (!response.ok) {
            if (response.status === 404) {
                console.warn(`User '${userId}' not found. Assuming new user.`);
                return true;
            }
            throw new Error(`Server error: ${response.status}`);
        }
        const data = await response.json();
        return data.can_participate;
    }

    /**
     * 퀴즈 주제를 선택하는 초기 화면을 렌더링합니다.
     */
    function renderInitialScreen() {
        mainContentContainer.innerHTML = `
            <header class="content-header">
                <h1 class="main-title">오늘의 주식 퀴즈</h1>
                <p class="subtitle">매일 새로운 퀴즈를 풀고 포인트를 얻어보세요!</p>
            </header>
            <div id="participation-message-container" class="participation-message" style="display: none;">
                🎉 오늘의 퀴즈에 이미 참여하셨습니다. 내일 다시 도전해주세요!
            </div>
            <section class="quiz-section">
                <h2 class="quiz-title">오늘 공부할 주제를 선택하세요 (1일 1회)</h2>
                <div class="quiz-container">
                    <div class="quiz-box checked" data-topic-kr="기초지식">
                        <span class="box-icon">💡</span>
                        <span class="box-text">기초지식</span>
                    </div>
                    <div class="quiz-box" data-topic-kr="기술적 지표">
                        <span class="box-icon">📈</span>
                        <span class="box-text">기술적 지표</span>
                    </div>
                    <div class="quiz-box" data-topic-kr="재무제표">
                        <span class="box-icon">📊</span>
                        <span class="box-text">재무제표</span>
                    </div>
                </div>
                <button class="start-quiz-button">퀴즈 시작하기</button>
            </section>
        `;
    }

    /**
     * 이미 퀴즈에 참여한 사용자에게 메시지를 보여주고 UI를 비활성화합니다.
     */
    function showParticipationMessage() {
        renderInitialScreen(); // 기본 UI를 먼저 그리고
        const quizSection = mainContentContainer.querySelector('.quiz-section');
        const messageContainer = mainContentContainer.querySelector('#participation-message-container');

        if (quizSection) {
            // 퀴즈 선택 영역을 비활성화 처리합니다.
            quizSection.querySelectorAll('.quiz-box, .start-quiz-button').forEach(el => {
                el.style.pointerEvents = 'none';
                el.style.opacity = '0.5';
            });
        }
        if (messageContainer) {
            messageContainer.style.display = 'block'; // 참여 완료 메시지를 보여줍니다.
        }
    }

    // --- 이벤트 위임: 동적으로 생성되는 요소들의 이벤트를 처리합니다. ---
    mainContentContainer.addEventListener('click', (event) => {
        const target = event.target;
        if (target.closest('.start-quiz-button')) handleStartQuiz();
        else if (target.closest('.quiz-box')) handleTopicSelection(target.closest('.quiz-box'));
        else if (target.closest('.start-solving-button')) renderQuizPage();
        else if (target.closest('.ox-button')) handleAnswerSubmit(target.closest('.ox-button').dataset.answer);
        else if (target.closest('.next-quiz-button')) handleNextQuestion();
        else if (target.closest('.restart-quiz-button')) window.location.reload();
    });

    /** 퀴즈 주제 선택을 처리합니다. */
    function handleTopicSelection(selectedBox) {
        mainContentContainer.querySelectorAll('.quiz-box').forEach(box => box.classList.remove('checked'));
        selectedBox.classList.add('checked');
    }

    /** '퀴즈 시작하기' 버튼 클릭을 처리하고, 퀴즈 데이터를 가져옵니다. */
    async function handleStartQuiz() {
        const selectedBox = mainContentContainer.querySelector('.quiz-box.checked');
        if (!selectedBox) {
            alert('먼저 공부할 주제를 선택해주세요.');
            return;
        }
        selectedTopic = selectedBox.dataset.topicKr;
        
        showLoading('퀴즈를 불러오는 중입니다...');
        try {
            // API 경로를 절대 경로 ('/')로 시작하도록 수정
            const response = await fetch(`/quiz/get-by-topic?topic=${encodeURIComponent(selectedTopic)}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            quizData = await response.json();
            if (quizData && quizData.length > 0) {
                renderExplanationsPage();
            } else {
                showError('해당 주제의 퀴즈를 불러올 수 없습니다.');
            }
        } catch (error) {
            console.error('Failed to load quiz data:', error);
            showError('퀴즈 데이터를 불러오는 중 오류가 발생했습니다.');
        }
    }
    
    /** 퀴즈 시작 전 해설 페이지를 렌더링합니다. */
    function renderExplanationsPage() {
        const explanationsHtml = quizData.map((quiz, index) => `
            <div class="explanation-item">
                <p class="explanation-title"><strong>해설 ${index + 1}</strong></p>
                <p class="explanation-text">${quiz.explanation}</p>
            </div>`).join('');

        mainContentContainer.innerHTML = `
            <div class="explanations-page">
                <h1 class="main-title">📚 [${selectedTopic}] 미리 학습하기</h1>
                <p class="subtitle">퀴즈에 출제될 ${quizData.length}문제의 해설을 미리 확인하세요.</p>
                <div class="explanations-container">${explanationsHtml}</div>
                <button class="start-solving-button">학습 완료! 퀴즈 풀기</button>
            </div>`;
    }

    /** 현재 문제 페이지를 렌더링합니다. */
    function renderQuizPage() {
        const quiz = quizData[currentQuestionIndex];
        mainContentContainer.innerHTML = `
            <div class="quiz-page">
                <p class="quiz-progress">총 ${quizData.length}문제 중 ${currentQuestionIndex + 1}번째</p>
                <h1 class="quiz-question-title">Q. ${quiz.question}</h1>
                <div class="quiz-card">
                    <div class="ox-options">
                        <button class="ox-button" data-answer="O">O</button>
                        <button class="ox-button" data-answer="X">X</button>
                    </div>
                </div>
                <div class="feedback-container"></div>
            </div>`;
    }

    /** 사용자 답변을 서버로 제출하고 결과를 처리합니다. */
    async function handleAnswerSubmit(userAnswer) {
        mainContentContainer.querySelectorAll('.ox-button').forEach(btn => btn.disabled = true);
        
        const quiz = quizData[currentQuestionIndex];
        const payload = {
            user_id: userId,
            quiz_id: quiz.identify_code,
            user_answer: userAnswer,
            topic: selectedTopic,
            quiz_index: currentQuestionIndex,
            total_questions: quizData.length,
        };

        try {
            // API 경로를 절대 경로 ('/')로 시작하도록 수정
            const response = await fetch('/quiz/submit-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error('답변 제출에 실패했습니다.');
            
            const result = await response.json();
            totalPoints += result.points_awarded;
            showFeedback(result.is_correct, result.points_awarded, quiz.explanation, userAnswer);
        } catch (error) {
            console.error('Answer submission error:', error);
            showError('답변 처리 중 오류가 발생했습니다. 다시 시도해주세요.', true);
        }
    }
    
    /** 정답/오답 피드백을 화면에 보여줍니다. */
    function showFeedback(isCorrect, points, explanation, userAnswer) {
        const feedbackContainer = mainContentContainer.querySelector('.feedback-container');
        const selectedBtn = mainContentContainer.querySelector(`.ox-button[data-answer="${userAnswer}"]`);
        
        const feedbackClass = isCorrect ? 'correct' : 'wrong';
        const feedbackMessage = isCorrect
            ? `👍 정답입니다! (+${points}포인트)`
            : `👎 아쉽네요! 정답은 '${quizData[currentQuestionIndex].answer}' 입니다. (+${points}포인트)`;

        if(selectedBtn) selectedBtn.classList.add(feedbackClass);

        const nextButtonText = (currentQuestionIndex === quizData.length - 1) ? '결과 보기' : '다음 문제';
        feedbackContainer.innerHTML = `
            <div class="feedback-message ${feedbackClass}">${feedbackMessage}</div>
            <div class="explanation-item feedback-explanation">
                <p class="explanation-title"><strong>상세 해설</strong></p>
                <p class="explanation-text">${explanation}</p>
            </div>
            <button class="next-quiz-button">${nextButtonText}</button>`;
    }

    /** 다음 문제로 넘어가거나 결과 페이지를 보여줍니다. */
    function handleNextQuestion() {
        currentQuestionIndex++;
        if (currentQuestionIndex < quizData.length) {
            renderQuizPage();
        } else {
            renderResultPage();
        }
    }

    /** 최종 결과 페이지를 렌더링합니다. */
    function renderResultPage() {
        mainContentContainer.innerHTML = `
            <div class="result-page">
                <h1 class="main-title">🎉 퀴즈 완료!</h1>
                <p class="subtitle">오늘의 주식 퀴즈 학습을 마쳤습니다.</p>
                <div class="result-summary">
                    <p>오늘 획득한 총 포인트</p>
                    <p class="total-points">${totalPoints} P</p>
                </div>
                <button class="restart-quiz-button">메인으로 돌아가기</button>
            </div>`;
    }
    
    /** 로딩 중임을 나타내는 UI를 보여줍니다. */
    function showLoading(message) {
        mainContentContainer.innerHTML = `<div class="loading-container"><div class="loading-spinner"></div><p>${message}</p></div>`;
    }

    /** 오류 메시지를 보여줍니다. */
    function showError(message, showRetryButton = false) {
        const retryButtonHtml = showRetryButton ? `<button class="restart-quiz-button" onclick="window.location.reload()">다시 시도</button>` : '';
        mainContentContainer.innerHTML = `<div class="error-container"><p>${message}</p>${retryButtonHtml}</div>`;
    }

    // --- 페이지 로드 시점의 시작점 ---
    initializePage();
});

