document.addEventListener('DOMContentLoaded', () => {
    const mainContentContainer = document.getElementById('main-content-container');
    const startQuizButton = document.querySelector('.start-quiz-button');
    const quizBoxes = document.querySelectorAll('.quiz-box');

    let currentQuestionIndex = 0;
    let correctAnswersCount = 0;
    let selectedQuizType = '';

    // 초기 선택된 퀴즈 타입 설정 (기본적으로 checked 클래스가 있는 박스)
    const initialSelectedBox = document.querySelector('.quiz-box.checked');
    if (initialSelectedBox) {
        selectedQuizType = initialSelectedBox.getAttribute('data-quiz-type');
        console.log('초기 선택된 퀴즈 타입:', selectedQuizType);
    }

    // 퀴즈 데이터 예시 (문제 3개로 구성)
    const quizData = {
        basic: [
            { question: "주식 시장에서 '매도'는 무엇을 의미하나요?", options: ["주식을 사는 것", "주식을 파는 것", "주식을 보유하는 것"], answer: "주식을 파는 것" },
            { question: "코스피 지수는 무엇을 나타내나요?", options: ["한국 거래소의 모든 기업", "유가증권 시장의 대표 기업", "코스닥 시장의 대표 기업"], answer: "유가증권 시장의 대표 기업" },
            { question: "주식의 '액면가'는 무엇인가요?", options: ["주식의 실제 시장 가격", "기업이 처음 주식을 발행할 때 정한 가격", "주식의 평균 가격"], answer: "기업이 처음 주식을 발행할 때 정한 가격" }
        ],
        technical: [
            { question: "기술적 지표 중 '이동평균선'은 무엇을 나타내나요?", options: ["주가의 평균", "거래량의 평균", "시가총액의 평균"], answer: "주가의 평균" },
            { question: "RSI 지표가 70 이상일 때, 일반적으로 어떤 상태를 의미하나요?", options: ["과매수", "과매도", "정상 범위"], answer: "과매수" },
            { question: "볼린저 밴드의 상단선은 무엇을 의미하나요?", options: ["주가가 고평가된 상태", "주가가 저평가된 상태", "주가의 변동성이 낮은 상태"], answer: "주가가 고평가된 상태" }
        ],
        financial: [
            { question: "재무제표 중 '손익계산서'는 무엇을 보여주나요?", options: ["기업의 자산, 부채, 자본", "기업의 일정 기간 동안의 경영 성과", "기업의 현금 흐름"], answer: "기업의 일정 기간 동안의 경영 성과" },
            { question: "'부채비율'은 무엇을 나타내는 지표인가요?", options: ["기업이 자본에 비해 부채가 얼마나 많은지", "기업이 현금 흐름을 얼마나 잘 관리하는지", "기업의 수익성"], answer: "기업이 자본에 비해 부채가 얼마나 많은지" },
            { question: "'영업이익'은 무엇을 의미하나요?", options: ["총수익에서 모든 비용을 뺀 금액", "총수익에서 판매비와 관리비를 뺀 금액", "모든 비용을 제외한 순수 이익"], answer: "총수익에서 판매비와 관리비를 뺀 금액" }
        ]
    };

    // 퀴즈 박스 선택 로직
    quizBoxes.forEach(box => {
        box.addEventListener('click', () => {
            quizBoxes.forEach(item => {
                item.classList.remove('checked');
            });
            box.classList.add('checked');

            // 선택된 퀴즈 타입 저장
            selectedQuizType = box.getAttribute('data-quiz-type');
            console.log('선택된 퀴즈 타입:', selectedQuizType); // 디버깅용
        });
    });

    // 퀴즈 페이지 렌더링 함수
    function renderQuiz(quiz) {
        mainContentContainer.innerHTML = `
            <div class="quiz-page">
                <h1 class="main-title">${currentQuestionIndex + 1}번째 퀴즈</h1>
                <p class="subtitle">총 3문제 중 ${currentQuestionIndex + 1}번째 문제입니다.</p>
                <div class="question-box">
                    <p class="question-text">${quiz.question}</p>
                    <div class="answer-options">
                        ${quiz.options.map(option => `<button class="answer-option">${option}</button>`).join('')}
                    </div>
                </div>
                <button class="next-quiz-button" style="display:none;">다음 문제</button>
            </div>
        `;

        // 답변 선택 이벤트 리스너 추가
        const answerButtons = document.querySelectorAll('.answer-option');
        const nextButton = document.querySelector('.next-quiz-button');

        answerButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                const selectedAnswer = event.target.textContent;
                const isCorrect = (selectedAnswer === quiz.answer);

                // 모든 버튼의 선택 스타일 제거 및 비활성화
                answerButtons.forEach(btn => {
                    btn.classList.remove('selected');
                    btn.disabled = true; // 중복 클릭 방지
                });

                // 정답/오답에 따라 스타일 변경
                if (isCorrect) {
                    event.target.classList.add('correct');
                    correctAnswersCount++;
                } else {
                    event.target.classList.add('wrong');
                    // 정답 버튼 표시
                    const correctAnswerBtn = Array.from(answerButtons).find(btn => btn.textContent === quiz.answer);
                    if (correctAnswerBtn) {
                        correctAnswerBtn.classList.add('correct');
                    }
                }

                // '다음 문제' 버튼 표시
                nextButton.style.display = 'block';
            });
        });

        // '다음 문제' 버튼 클릭 이벤트
        nextButton.addEventListener('click', () => {
            currentQuestionIndex++;
            if (currentQuestionIndex < 3) {
                renderQuiz(quizData[selectedQuizType][currentQuestionIndex]);
            } else {
                renderResultPage();
            }
        });
    }

    // 결과 페이지 렌더링 함수
    function renderResultPage() {
        mainContentContainer.innerHTML = `
            <div class="result-page">
                <h1 class="main-title">퀴즈 완료!</h1>
                <p class="subtitle">총 3문제 중 **${correctAnswersCount}문제**를 맞혔습니다.</p>
                <button class="restart-quiz-button">다시 시작하기</button>
            </div>
        `;

        const restartButton = document.querySelector('.restart-quiz-button');
        restartButton.addEventListener('click', () => {
            location.reload(); // 페이지 새로고침하여 초기 상태로 복귀
        });
    }

    // '퀴즈 시작하기' 버튼 클릭 이벤트
    startQuizButton.addEventListener('click', () => {
        const selectedBox = document.querySelector('.quiz-box.checked');
        if (selectedBox) {
            selectedQuizType = selectedBox.getAttribute('data-quiz-type');
            console.log('퀴즈 시작 - 선택된 타입:', selectedQuizType); // 디버깅용
            console.log('퀴즈 데이터:', quizData[selectedQuizType]); // 디버깅용

            if (quizData[selectedQuizType] && quizData[selectedQuizType].length > 0) {
                currentQuestionIndex = 0;
                correctAnswersCount = 0;
                renderQuiz(quizData[selectedQuizType][currentQuestionIndex]);
            } else {
                alert('해당 주제의 퀴즈 데이터가 없습니다.');
            }
        } else {
            alert('먼저 공부할 주제를 선택해주세요.');
        }
    });
});