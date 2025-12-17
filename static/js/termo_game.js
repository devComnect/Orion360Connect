document.addEventListener('DOMContentLoaded', function () {

    // --- 1. SETUP & CONSTANTES ---
    const container = document.getElementById('termo-game-container');
    const GAME_ID = container.dataset.gameId;
    
    // Captura o ID da tentativa atual para validar cache vs banco
    const CURRENT_ATTEMPT_ID = parseInt(container.dataset.attemptId); 
    
    const WORD_LENGTH = parseInt(container.dataset.wordLength);
    const MAX_ATTEMPTS = parseInt(container.dataset.maxAttempts);
    const MAX_SCORE = parseInt(container.dataset.pointsReward);
    
    // Timer handling
    const timerElement = document.getElementById('timer-countdown');
    const INITIAL_TIME = timerElement ? parseFloat(timerElement.textContent) : 0;

    // Elementos UI
    const board = document.getElementById('game-board');
    const input = document.getElementById('word-input');
    const botMsg = document.getElementById('bot-message');
    const submitBtn = document.getElementById('submit-btn');
    const hintBtn = document.getElementById('hint-btn');
    const exitBtn = document.getElementById('exit-game-btn');
    
    // --- CORREÇÃO AQUI: Aponta para o novo ID do HTML ---
    const scoreValueEl = document.getElementById('score-display-value');

    // Estado do Jogo
    let currentRow = 0;
    let isGameOver = false;
    
    // --- LÓGICA DE PERSISTÊNCIA INTELIGENTE ---
    const stateKey = `termo_state_${GAME_ID}`;
    let savedState = JSON.parse(sessionStorage.getItem(stateKey)) || {};

    // VERIFICAÇÃO DE INTEGRIDADE (FIX DO RESET)
    // Se o cache existir, mas o attempt_id salvo for diferente do atual (resetou banco), limpa o cache.
    if (savedState.attemptId && savedState.attemptId !== CURRENT_ATTEMPT_ID) {
        console.log("Detectado reset de sessão. Limpando cache local.");
        sessionStorage.removeItem(stateKey);
        savedState = {}; // Reseta variável local
    }

    // --- LÓGICA DE PONTUAÇÃO VISUAL ---
    function updateScoreDisplay() {
        if (!scoreValueEl) {
            console.error("CRÍTICO: Elemento 'score-display-value' não encontrado no DOM.");
            return;
        }

        // currentRow começa em 0.
        const currentAttempt = currentRow + 1;
        let potentialScore = 0;

        // Regra: 1 a 4 = 100% / Mais de 4 = 50%
        if (currentAttempt <= 4) {
            potentialScore = MAX_SCORE;
            scoreValueEl.style.color = "var(--neon-blue)";
        } else {
            potentialScore = Math.round(MAX_SCORE * 0.5);
            scoreValueEl.style.color = "var(--neon-red)";
        }

        scoreValueEl.textContent = potentialScore;
    }

    // --- 2. CONSTRUÇÃO DO GRID ---
    function initBoard() {
        board.style.gridTemplateRows = `repeat(${MAX_ATTEMPTS}, 1fr)`;
        board.innerHTML = '';

        for (let i = 0; i < MAX_ATTEMPTS; i++) {
            const row = document.createElement('div');
            row.className = 'letter-row';
            row.style.gridTemplateColumns = `repeat(${WORD_LENGTH}, 1fr)`;

            for (let j = 0; j < WORD_LENGTH; j++) {
                const box = document.createElement('div');
                box.className = 'letter-box';
                row.appendChild(box);
            }
            board.appendChild(row);
        }
    }

    // --- 3. INPUT HANDLER ---
    input.addEventListener('input', (e) => {
        if (isGameOver) return;
        let val = input.value.toUpperCase().replace(/[^A-ZÇ]/g, '');
        if (val.length > WORD_LENGTH) val = val.slice(0, WORD_LENGTH);
        input.value = val;
        updateGridFromInput(val);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSubmission();
        }
    });

    function updateGridFromInput(text) {
        const row = board.children[currentRow];
        const letters = text.split('');

        for (let i = 0; i < WORD_LENGTH; i++) {
            const box = row.children[i];
            const letter = letters[i] || '';
            box.textContent = letter;
            if (letter) {
                box.classList.add('filled');
                box.style.borderColor = "var(--neon-blue)";
            } else {
                box.classList.remove('filled');
                box.style.borderColor = "var(--neon-grey)";
            }
        }
    }

    function restoreState() {
        if (savedState && savedState.guesses) {
            currentRow = savedState.guesses.length;
            savedState.guesses.forEach((guess, rowIndex) => {
                const feedback = savedState.feedbackHistory[rowIndex];
                const row = board.children[rowIndex];
                for (let i = 0; i < WORD_LENGTH; i++) {
                    const box = row.children[i];
                    box.textContent = guess[i];
                    box.classList.add(feedback[i], 'flip');
                }
            });
        }
        
        if (savedState && savedState.isGameOver) {
            freezeGame("Protocolo encerrado.");
        } else {
            input.disabled = false;
            input.focus();
        }
    }

    function freezeGame(msg) {
        isGameOver = true;
        input.disabled = true;
        input.value = "---";
        botMsg.innerHTML = `<span style="color: var(--neon-red)">${msg}</span>`;
        submitBtn.disabled = true;
        hintBtn.disabled = true;
    }

    // --- 4. AÇÕES ---
    if (hintBtn) {
        hintBtn.addEventListener('click', () => {
            const hint = hintBtn.dataset.hint;
            botMsg.innerHTML = `<i class="bi bi-lightbulb-fill text-warning"></i> <span style="color: #fff">${hint}</span>`;
            input.focus();
        });
    }

    submitBtn.addEventListener('click', handleSubmission);

    exitBtn.addEventListener('click', () => {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'Abortar Protocolo?',
                text: "Isso contará como falha na missão.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sim, abortar',
                background: '#1b1e24',
                color: '#fff'
            }).then((result) => {
                if (result.isConfirmed) submitGuess(false, true);
            });
        } else if (confirm("Abortar missão?")) {
            submitGuess(false, true);
        }
    });

    function handleSubmission() {
        if (isGameOver) return;
        const guess = input.value.toUpperCase();
        if (guess.length !== WORD_LENGTH) {
            const row = board.children[currentRow];
            row.classList.add('shake');
            setTimeout(() => row.classList.remove('shake'), 500);
            botMsg.innerHTML = `<span style="color: var(--neon-yellow)">Erro: Input deve ter ${WORD_LENGTH} caracteres.</span>`;
            input.focus();
            return;
        }
        submitGuess(false, false, guess);
    }

    // --- 5. SERVIDOR (AJAX) ---
    async function submitGuess(timedOut = false, abandoned = false, currentGuessStr = "") {
        if (isGameOver && !abandoned) return;

        input.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
        const guessPayload = abandoned ? "" : currentGuessStr;

        try {
            const res = await fetch('/termo/check_guess', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    game_id: GAME_ID,
                    guess: guessPayload,
                    timed_out: timedOut,
                    abandoned: abandoned
                })
            });

            const data = await res.json();

            if (!res.ok) {
                input.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-terminal"></i> EXECUTAR (ENTER)';
                input.focus();
                botMsg.textContent = "Erro: " + (data.message || "Tente novamente.");
                return;
            }

            if (abandoned || timedOut) {
                window.location.href = `/termo/resultado/${data.attempt_id}?from_submit=true`;
                return;
            }

            animateFeedback(data.feedback, data.is_winner, data.attempt_id, data.game_over, currentGuessStr);

        } catch (e) {
            console.error(e);
            input.disabled = false;
            botMsg.textContent = "Erro de conexão.";
        }
    }

    function animateFeedback(feedback, isWinner, attemptId, isGameReallyOver, guessStr) {
        const row = board.children[currentRow];
        
        // Garante a existência do savedState
        if (!savedState || !Array.isArray(savedState.guesses)) {
            savedState = { guesses: [], feedbackHistory: [] };
        }
        
        const state = savedState;
        
        // Salva attemptId
        state.attemptId = CURRENT_ATTEMPT_ID;
        state.guesses.push(guessStr);
        state.feedbackHistory.push(feedback);
        state.isGameOver = isGameReallyOver;
        sessionStorage.setItem(stateKey, JSON.stringify(state));

        feedback.forEach((status, i) => {
            setTimeout(() => {
                const box = row.children[i];
                box.classList.add(status, 'flip');
                if (status === 'correct') box.style.borderColor = "var(--neon-green)";
                else if (status === 'present') box.style.borderColor = "var(--neon-yellow)";
                else box.style.borderColor = "transparent";
            }, i * 250);
        });

        setTimeout(() => {
            if (isWinner) {
                botMsg.innerHTML = `<span class="text-success" style="color: var(--neon-blue) !important">ACESSO LIBERADO! Redirecionando...</span>`;
                setTimeout(() => window.location.href = `/termo/resultado/${attemptId}?from_submit=true`, 1000);
            } else if (isGameReallyOver) {
                botMsg.innerHTML = `<span class="text-danger">FALHA: TENTATIVAS ESGOTADAS.</span>`;
                setTimeout(() => window.location.href = `/termo/resultado/${attemptId}?from_submit=true`, 1500);
            } else {
                currentRow++;
                
                // --- ATUALIZA O SCORE VISUALMENTE ---
                updateScoreDisplay();
                
                input.value = '';
                input.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-terminal"></i> EXECUTAR (ENTER)';
                botMsg.textContent = `Tentativa ${currentRow + 1}/${MAX_ATTEMPTS}. Insira comando.`;
                input.focus();
            }
        }, (WORD_LENGTH * 250) + 500);
    }

    // --- 6. TIMER ---
    if (INITIAL_TIME > 0 && timerElement) {
        let time = INITIAL_TIME;
        const interval = setInterval(() => {
            if (isGameOver) { clearInterval(interval); return; }
            time--;
            
            const m = Math.floor(time / 60).toString().padStart(2, '0');
            const s = (time % 60).toString().padStart(2, '0');
            timerElement.textContent = `${m}:${s}`;
            
            if (time < 10) timerElement.style.color = "var(--neon-red)";
            
            if (time <= 0) {
                clearInterval(interval);
                freezeGame("TEMPO ESGOTADO.");
                submitGuess(true); 
            }
        }, 1000);
    }

    // Inicialização
    initBoard();
    restoreState();
    
    // IMPORTANTE: Atualiza o score após restaurar o estado
    updateScoreDisplay();
});