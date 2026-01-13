document.addEventListener('DOMContentLoaded', function () {

    // --- 1. SETUP INICIAL ---
    const container = document.getElementById('anagram-game-container');
    if (!container) return;

    // Dados do Backend
    const GAME_ID = container.dataset.gameId;
    const WORDS_DATA = JSON.parse(document.getElementById('game-data').textContent);
    const REMAINING_TIME_JSON = document.getElementById('game-timer-data').textContent;
    const INITIAL_TIME = REMAINING_TIME_JSON ? parseFloat(REMAINING_TIME_JSON) : 0;
    const MAX_LIVES = 3;

    // Elementos UI
    const timerEl = document.getElementById('timer-countdown');
    const livesContainer = document.getElementById('game-lives');
    const scoreCounterEl = document.getElementById('score-counter');
    const filesDotsContainer = document.getElementById('files-dots');
    
    const shuffledDisplay = document.getElementById('shuffled-display');
    const answerGrid = document.getElementById('answer-grid');
    const consoleOutput = document.getElementById('console-output');
    
    const input = document.getElementById('word-input');
    const submitBtn = document.getElementById('submit-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const exitBtn = document.getElementById('exit-btn');

    // Estado do Jogo
    let currentIndex = 0;
    let correctCount = 0;
    let lives = MAX_LIVES;
    let isGameOver = false;
    
    // Status por palavra: 'locked', 'solved', 'failed' (se quisermos bloquear)
    // Inicialmente, trackeamos se foi resolvido ou não.
    let wordsStatus = new Array(WORDS_DATA.length).fill(false); // true = solved

    // --- 2. FUNÇÕES AUXILIARES ---

    // Algoritmo de Shuffle com Validação (Bonus da Tarefa)
    function getSafeShuffle(originalWord) {
        if (!originalWord) return "";
        let wordArr = originalWord.split('');
        
        // Se todas as letras forem iguais (ex: "AAA"), não tem como embaralhar diferente.
        const uniqueChars = new Set(wordArr);
        if (uniqueChars.size === 1) return originalWord; 

        let shuffled;
        let attempts = 0;
        
        do {
            // Fisher-Yates shuffle
            shuffled = [...wordArr];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            attempts++;
            // Evita loop infinito em casos muito raros
        } while (shuffled.join('') === originalWord && attempts < 50);

        return shuffled.join('');
    }

    function updateLivesUI() {
        const icons = livesContainer.querySelectorAll('.life-icon');
        icons.forEach((icon, i) => {
            if (i < lives) icon.classList.remove('lost');
            else icon.classList.add('lost');
        });
    }

    function updateDotsUI() {
        filesDotsContainer.innerHTML = '';
        WORDS_DATA.forEach((_, i) => {
            const dot = document.createElement('div');
            dot.className = 'file-dot';
            if (i === currentIndex) dot.classList.add('active');
            if (wordsStatus[i]) dot.classList.add('solved');
            filesDotsContainer.appendChild(dot);
        });
        
        // Atualiza contador de texto
        scoreCounterEl.textContent = `${correctCount}/${WORDS_DATA.length}`;
    }

    // --- 3. LÓGICA PRINCIPAL DA RODADA ---

    function loadWord(index) {
        if (isGameOver) return;
        
        // Validação de índice
        if (index < 0) index = WORDS_DATA.length - 1;
        if (index >= WORDS_DATA.length) index = 0;
        
        currentIndex = index;
        const currentData = WORDS_DATA[currentIndex];
        const isSolved = wordsStatus[currentIndex];

        // 1. Renderiza Palavra Embaralhada
        // Se já resolveu, não precisa mostrar embaralhada, ou mostra limpa. 
        // Vamos optar por mostrar "---" se já resolveu para limpar visualmente.
        shuffledDisplay.innerHTML = '';
        if (!isSolved) {
            const safeShuffled = getSafeShuffle(currentData.shuffled); // Usa o shuffled do banco ou re-embaralha aqui?
            // O banco já manda 'shuffled', mas a requirement pediu validação.
            // Vamos re-embaralhar o 'correct' para garantir a regra "diferente do original"
            // ou validar o que veio do banco. Para segurança, re-embaralhamos o correct aqui.
            const displayChars = getSafeShuffle(currentData.correct).split('');
            
            displayChars.forEach(char => {
                const span = document.createElement('span');
                span.className = 'source-letter';
                span.textContent = char;
                // Animação com delay aleatório
                span.style.animationDelay = `${Math.random() * 2}s`;
                shuffledDisplay.appendChild(span);
            });
        } else {
             const msg = document.createElement('span');
             msg.className = 'hud-label';
             msg.style.color = 'var(--neon-green)';
             msg.textContent = "[ DADOS RECUPERADOS ]";
             shuffledDisplay.appendChild(msg);
        }

        // 2. Renderiza Grid de Resposta
        answerGrid.innerHTML = '';
        const len = currentData.correct.length;
        for (let i = 0; i < len; i++) {
            const box = document.createElement('div');
            box.className = 'answer-box';
            if (isSolved) {
                box.textContent = currentData.correct[i];
                box.classList.add('correct');
            }
            answerGrid.appendChild(box);
        }

        // 3. Prepara Input
        input.value = '';
        input.maxLength = len;
        input.disabled = isSolved; // Trava se já resolveu
        
        if (isSolved) {
            input.placeholder = "ARQUIVO DECRIPTADO";
            consoleOutput.textContent = `Arquivo ${currentIndex + 1} recuperado com sucesso.`;
        } else {
            input.placeholder = `DIGITE ${len} CARACTERES...`;
            consoleOutput.textContent = "Aguardando chave de decriptação...";
            input.focus();
        }

        // 4. Botões Nav
        prevBtn.disabled = false;
        nextBtn.disabled = false;
        
        updateDotsUI();
    }

    // --- 4. INPUT HANDLER ---

    input.addEventListener('input', () => {
        // Filtra caracteres não alfabéticos
        input.value = input.value.toUpperCase().replace(/[^A-ZÇ]/g, '');
        
        // Sincroniza visualmente com o grid
        const val = input.value.split('');
        const boxes = answerGrid.querySelectorAll('.answer-box');
        
        boxes.forEach((box, i) => {
            if (val[i]) {
                box.textContent = val[i];
                box.classList.add('filled');
            } else {
                box.textContent = '';
                box.classList.remove('filled');
            }
        });
    });

    // Enter para enviar
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') checkAnswer();
    });

    submitBtn.addEventListener('click', checkAnswer);

    // --- 5. VALIDAÇÃO DA RESPOSTA ---

    function checkAnswer() {
        if (isGameOver || wordsStatus[currentIndex]) return;

        const attempt = input.value.toUpperCase();
        const correct = WORDS_DATA[currentIndex].correct.toUpperCase();

        if (attempt.length !== correct.length) {
            consoleOutput.innerHTML = `<span style="color:var(--neon-yellow)">Erro: Tamanho inválido. Necessário ${correct.length} chars.</span>`;
            shakeGrid();
            return;
        }

        if (attempt === correct) {
            // SUCESSO
            handleSuccess();
        } else {
            // FALHA
            handleFail();
        }
    }

    function handleSuccess() {
        consoleOutput.innerHTML = `<span style="color:var(--neon-green)">SUCESSO: Chave aceita.</span>`;
        wordsStatus[currentIndex] = true;
        correctCount++;
        
        // Atualiza visual boxes para verde
        const boxes = answerGrid.querySelectorAll('.answer-box');
        boxes.forEach(box => box.classList.add('correct'));
        
        updateDotsUI();

        // Verifica vitória total
        if (correctCount === WORDS_DATA.length) {
            endGame(false, false); // Ganhou tudo
        } else {
            // Auto-navigate para a próxima não resolvida após breve delay
            setTimeout(() => {
                let nextIndex = -1;
                // Procura a próxima livre
                for (let i = 1; i < WORDS_DATA.length; i++) {
                    let idx = (currentIndex + i) % WORDS_DATA.length;
                    if (!wordsStatus[idx]) {
                        nextIndex = idx;
                        break;
                    }
                }
                if (nextIndex !== -1) loadWord(nextIndex);
            }, 800);
        }
    }

    function handleFail() {
        lives--;
        updateLivesUI();
        consoleOutput.innerHTML = `<span style="color:var(--neon-red)">ERRO: Chave incorreta. Tentativas restantes: ${lives}</span>`;
        shakeGrid();

        if (lives <= 0) {
            endGame(false, false); // Perdeu por vidas
        } else {
            input.value = ''; // Limpa input
            // Limpa visual grid
            setTimeout(() => {
                const boxes = answerGrid.querySelectorAll('.answer-box');
                boxes.forEach(box => {
                    box.textContent = '';
                    box.classList.remove('filled');
                });
            }, 400);
        }
    }

    function shakeGrid() {
        const boxes = answerGrid.querySelectorAll('.answer-box');
        boxes.forEach(box => box.classList.add('shake'));
        setTimeout(() => boxes.forEach(box => box.classList.remove('shake')), 400);
    }

    // --- 6. NAVEGAÇÃO ---
    prevBtn.addEventListener('click', () => loadWord(currentIndex - 1));
    nextBtn.addEventListener('click', () => loadWord(currentIndex + 1));

    // --- 7. FINALIZAÇÃO ---

    exitBtn.addEventListener('click', () => {
        if (confirm("Abortar missão? O progresso atual será salvo.")) {
            endGame(false, true); // Abandoned
        }
    });

    async function endGame(timedOut = false, abandoned = false) {
        if (isGameOver) return;
        isGameOver = true;
        
        input.disabled = true;
        submitBtn.disabled = true;
        consoleOutput.innerHTML = "Enviando relatório de missão...";

        const payload = {
            game_id: GAME_ID,
            correct_count: correctCount // Manda quantos acertou, independente do motivo do fim
        };

        try {
            const res = await fetch('/anagrama/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            
            if (res.ok && data.status === 'success') {
                window.location.href = `/anagrama/resultado/${data.attempt_id}`;
            } else {
                alert("Erro ao salvar: " + (data.message || "Erro desconhecido"));
                window.location.href = '/salão-de-jogos';
            }

        } catch (e) {
            console.error(e);
            alert("Erro de conexão.");
        }
    }

    // --- 8. TIMER ---
    if (INITIAL_TIME > 0) {
        let time = INITIAL_TIME;
        const interval = setInterval(() => {
            if (isGameOver) { clearInterval(interval); return; }
            time--;
            
            const m = Math.floor(time / 60).toString().padStart(2, '0');
            const s = Math.floor(time % 60).toString().padStart(2, '0');
            timerEl.textContent = `${m}:${s}`;
            
            if (time <= 0) {
                clearInterval(interval);
                endGame(true, false); // Timeout
            }
        }, 1000);
    }

    // START
    loadWord(0);
});