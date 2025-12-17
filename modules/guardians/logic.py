import re, random
from sqlalchemy import not_, func
from datetime import date, timedelta, datetime
from flask import flash, g
from application.models import (db, Guardians, NivelSeguranca, Insignia, GuardianInsignia, 
                                HistoricoAcao, SpecializationPerkLevel, Perk, GlobalGameSettings,
                                TermoAttempt, AnagramAttempt, GuardianPurchase, ShopItem, GuardianShopState)

# Definição Global de Tipos de Bônus (Usado em Loja, Conquistas e Specs)
BONUS_TYPES = {
    # --- Ganhos de XP Específicos ---
    'QUIZ_BONUS_PCT': 'Bônus de % em Quizzes',
    'TERMO_BONUS_PCT': 'Bônus de % no Termo (Carderno DNS)',
    'ANAGRAM_BONUS_PCT': 'Bônus de % no Anagrama (Certificado)',
    'PATROL_BONUS_PCT': 'Bônus de % na Patrulha (Farejo)',
    'PW_BONUS_PCT': 'Bônus de % no Segredo (Cofre)',
    
    # --- Mecânicas de Jogo ---
    'SPEED_BONUS_PCT': 'Bônus de Velocidade (Sincronizador)',   
    'PERFECTION_BONUS_PCT': 'Bônus de Perfeição (Engrenagem)',   
    'STREAK_BONUS_PCT': 'Bônus na Ofensiva Diária',
    
    # --- Economia e Global ---
    'GCOIN_BONUS_PCT': 'Multiplicador de G-Coins (Mineradora)',
    'GLOBAL_SCORE_PCT': 'Bônus Global de XP (Firewall)',
    
    # --- Consumíveis (Instantâneos) ---
    'ADD_QUIZ_TOKEN': 'Consumível: +1 Token de Quiz',
    'ADD_MINIGAME_TOKEN': 'Consumível: +1 Token de Minigame'
}
##
##

##CACHE DE CONFIGS GLOBAIS (magic numbers)
def get_game_setting(key, default_value, type_cast=str):
    """
    Busca uma configuração global.
    :param key: A chave da configuração (ex: 'SPEED_LIMIT_QUIZ')
    :param default_value: Valor retornado caso a chave não exista no banco.
    :param type_cast: A função para converter o tipo (int, float, bool). Padrão str.
    """
    setting = GlobalGameSettings.query.filter_by(setting_key=key).first()
    
    if setting:
        try:
            return type_cast(setting.setting_value)
        except (ValueError, TypeError):
            # Se falhar a conversão (ex: texto num campo int), retorna o default
            return default_value
            
    return default_value


##CALCULA PONTUAÇÃO FINAL APÓS TODOS OS BONUS E GARANTE O BONUS DE OFENSIVA AO FINAL (CASO NÃO TENHA)
def calculate_final_score(guardian: Guardians, current_total_score: int, raw_base_score: int, perk_code: str = None):
    """
    Calcula pontuação final e aplica Streak.
    Versão com DEBUG detalhado no console.
    """

    score_with_bonuses = current_total_score
    bonus_breakdown = {
        'conquista_bonus': 0,
        'loja_bonus': 0,
        'streak_total_bonus': 0,
        'streak_base_bonus': 0,
        'streak_spec_bonus': 0
    }

    if perk_code:
        # 1. BÔNUS DE CONQUISTA
        if guardian.featured_insignia:
            bonus_type = guardian.featured_insignia.bonus_type
            bonus_val_pct = guardian.featured_insignia.bonus_value
            is_applicable = (bonus_type == perk_code) or (bonus_type == 'GLOBAL_SCORE_PCT')

            if is_applicable and bonus_val_pct:
                bonus_val = int(round(raw_base_score * (bonus_val_pct / 100.0)))
                bonus_breakdown['conquista_bonus'] = bonus_val
                score_with_bonuses += bonus_val

        # 2. BÔNUS DE LOJA (Específico)
        shop_bonus_pct = _get_shop_bonus(guardian, perk_code)
        if shop_bonus_pct > 0:
            shop_val = int(round(raw_base_score * (shop_bonus_pct / 100.0)))
            bonus_breakdown['loja_bonus'] = shop_val
            score_with_bonuses += shop_val


    # --- 3. BÔNUS DE OFENSIVA (Streak) ---

    effective_percent = get_effective_streak_percentage(guardian)

    # Cálculo base do streak
    base_bonus = int(round(score_with_bonuses * (effective_percent / 100.0)))
    
    # Bônus extra de streak (Caminho Cinza/Gestor)
    spec_streak_pct = get_total_bonus(guardian, 'STREAK_BONUS_PCT', default=0)
    spec_bonus = 0
    if spec_streak_pct > 0:
        spec_bonus = int(round(base_bonus * (spec_streak_pct / 100.0))) # Ou sobre o total, dependendo da regra
    
    total_streak_bonus = base_bonus + spec_bonus
    
    bonus_breakdown['streak_total_bonus'] = total_streak_bonus
    bonus_breakdown['streak_base_bonus'] = base_bonus
    bonus_breakdown['streak_spec_bonus'] = spec_bonus

    final_score = score_with_bonuses + total_streak_bonus
    
    return {
        'base_score': raw_base_score,
        'final_score': int(final_score),
        'breakdown': bonus_breakdown
    }

#BUSCA O VALOR DO PERK ATUAL PARA O GUARDIAO DE ACORDO COM O NIVEL
def get_active_perk_value(guardian: Guardians, perk_code: str, default=0):
    """
    Busca o valor de um perk ativo para o guardião, considerando seu nível atual.
    Retorna o valor do nível mais alto caso o mesmo perk exista em múltiplos níveis (upgrades).
    """
    if not guardian or not guardian.specialization_id or not guardian.nivel_id:
        return default

    try:
        current_level_number = guardian.nivel.level_number
    except AttributeError:
        current_nivel = NivelSeguranca.query.get(guardian.nivel_id)
        if not current_nivel: return default
        current_level_number = current_nivel.level_number

    perk_entry = db.session.query(SpecializationPerkLevel).join(Perk).filter(
        SpecializationPerkLevel.specialization_id == guardian.specialization_id,
        Perk.perk_code == perk_code,
        SpecializationPerkLevel.level <= current_level_number
    ).order_by(
        SpecializationPerkLevel.level.desc()
    ).first()

    if perk_entry:
        return perk_entry.bonus_value
    else:
        return default

#CALCULA BONUS DE VELOCIDADE E PERFEIÇÃO PARA DESAFIOS
def calculate_performance_bonuses(guardian: Guardians, event_type: str, raw_score: int, context: dict):
    """
    Calcula bônus de performance (Tempo e Perfeição) para um evento.
    Aplica multiplicadores de itens ativos (Sincronizador/Engrenagem).
    """
    
    time_bonus = 0
    perfection_bonus = 0
    
    # Validação de Perfeição
    total_possible = context.get('total_possible_points', 0)
    score_check = context.get('raw_score_before_perks', 0)
    is_perfect = (score_check == total_possible and total_possible > 0)
    
    # ====================================================
    # 1. CÁLCULO DO BÔNUS DE VELOCIDADE
    # ====================================================
    time_limit = context.get('time_limit_seconds')
    duration = context.get('duration_seconds')
    
    if time_limit and time_limit > 0 and duration is not None:
        # A. Cálculo Base (Mecânica do Jogo)
        time_remaining_percent = max(0, (time_limit - duration) / time_limit)
        divisor = get_global_setting('TIME_BONUS_DIVISOR', default=5.0, setting_type=float)
        
        base_time_bonus = 0
        if divisor > 0:
            base_time_bonus = int(round(raw_score * (time_remaining_percent / divisor)))
        
        # B. Aplicação de Buffs (Sincronizador - SPEED_BONUS_PCT)
        # Busca bônus de Loja + Spec + Insígnia
        speed_mult_pct = get_total_bonus(guardian, 'SPEED_BONUS_PCT') 
        
        if speed_mult_pct > 0:
            boost_val = int(base_time_bonus * (speed_mult_pct / 100.0))
            time_bonus = base_time_bonus + boost_val
        else:
            time_bonus = base_time_bonus
            

    # ====================================================
    # 2. CÁLCULO DO BÔNUS DE PERFEIÇÃO
    # ====================================================
    if is_perfect:
        base_perf_bonus = 0
        
        if event_type == 'quiz':
            # Atualiza Streak
            guardian.perfect_quiz_streak = (guardian.perfect_quiz_streak or 0) + 1
            guardian.perfect_quiz_cumulative_count = (guardian.perfect_quiz_cumulative_count or 0) + 1
            
            # Token de Retake
            try:
                check_and_award_retake_token(guardian) 
            except Exception as e:
                print(f"Erro ao dar token quiz: {e}")
            
            # A. Cálculo Base (Streak Threshold)
            threshold = get_global_setting('PERFECT_QUIZ_STREAK_THRESHOLD', default=1, setting_type=int)
            bonus_val = get_global_setting('PERFECT_QUIZ_STREAK_BONUS', default=10, setting_type=int)
            
            if guardian.perfect_quiz_streak > 0 and guardian.perfect_quiz_streak % threshold == 0:
                base_perf_bonus = bonus_val
        
        elif event_type == 'minigame':
            # Token de Retake Minigame
            try:
                check_and_award_minigame_token(guardian)
            except Exception as e:
                print(f"Erro ao dar token minigame: {e}")
            
            # A. Cálculo Base (Fixo)
            base_perf_bonus = get_global_setting('PERFECT_MINIGAME_BONUS', default=10, setting_type=int)

        # B. Aplicação de Buffs (Engrenagem - PERFECTION_BONUS_PCT)
        # Se o jogador ganhou algum bônus base, o item multiplica esse bônus
        if base_perf_bonus > 0:
            perf_mult_pct = get_total_bonus(guardian, 'PERFECTION_BONUS_PCT')
            
            if perf_mult_pct > 0:
                boost_val = int(base_perf_bonus * (perf_mult_pct / 100.0))
                perfection_bonus = base_perf_bonus + boost_val
            else:
                perfection_bonus = base_perf_bonus

    else:
        if event_type == 'quiz':
            guardian.perfect_quiz_streak = 0

    return {
        'time_bonus': int(time_bonus),
        'perfection_bonus': int(perfection_bonus),
        'is_perfect': is_perfect
    }

##CACHE DE CONFIGS GLOBAIS##
def get_global_setting(key, default=None, setting_type=int):
    """
    Busca uma configuração global do jogo de forma eficiente, usando um cache por requisição.
    
    :param key: A chave da configuração (ex: 'PATROL_MIN_POINTS').
    :param default: O valor a ser retornado se a chave não for encontrada.
    :param setting_type: O tipo de dado para o qual o valor deve ser convertido (int, float, str).
    """
    # Verifica se o cache de configurações já foi criado para esta requisição
    if 'game_settings' not in g:
        # Se não, busca todas as configurações do banco UMA VEZ e as armazena em 'g'
        settings = GlobalGameSettings.query.all()
        # Transforma a lista de objetos em um dicionário simples: {'chave': 'valor'}
        g.game_settings = {s.setting_key: s.setting_value for s in settings}

    # Busca o valor no cache. Se não encontrar, usa o valor 'default'.
    value = g.game_settings.get(key, default)

    # Tenta converter o valor para o tipo desejado (int por padrão)
    try:
        return setting_type(value)
    except (ValueError, TypeError):
        # Se a conversão falhar, retorna o valor default
        return default

def get_bonus_for_perk(guardian, perk_code):
    """
    Função genérica que busca o valor de um bônus para um guardião no banco de dados,
    baseado na sua especialização.
    """
    # Se o guardião não tiver especialização ou nível, não há bônus.
    if not guardian or not guardian.specialization_id or not guardian.nivel:
        return 0.0

    current_level_number = guardian.nivel.level_number

    bonus_value = db.session.query(SpecializationPerkLevel.bonus_value).join(Perk).filter(
        SpecializationPerkLevel.specialization_id == guardian.specialization_id,
        SpecializationPerkLevel.level == current_level_number,
        Perk.perk_code == perk_code
    ).scalar()
    
    return bonus_value or 0.0

def get_effective_streak_percentage(guardian):
    """
    Calcula o percentual de streak a ser aplicado.
    Atualizado para somar bônus de Especialização + Conquista + Loja.
    """
    streak_days = guardian.current_streak or 0
    if streak_days <= 0:
        return 0 

    gain_modifier_pct = get_total_bonus(guardian, 'STREAK_GAIN_PCT', default=0)
    
    base_percent_per_day = 1.0 
    effective_percent_per_day = base_percent_per_day * (1 + gain_modifier_pct / 100.0)
    
    raw_effective_percentage = streak_days * effective_percent_per_day

    base_cap_percent = get_global_setting('STREAK_BONUS_CAP_PERCENT', default=20)

    cap_increase_percent = get_total_bonus(guardian, 'STREAK_MAX_PCT', default=0)

    effective_cap = base_cap_percent + cap_increase_percent

    final_effective_percentage = min(raw_effective_percentage, effective_cap)

    return round(final_effective_percentage, 2)

##CALCULA DIAS DA SEMANA PRA CARD EM MEU PERFIL
def calculate_week_days_status(guardian):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) # Segunda-feira
    start_of_week_dt = datetime.combine(start_of_week, datetime.min.time())
    end_of_today_dt = datetime.combine(today, datetime.max.time())

    recent_activity_dates = db.session.query(
        func.date(HistoricoAcao.data_evento)
    ).filter(
        HistoricoAcao.guardian_id == guardian.id,
        HistoricoAcao.data_evento.between(start_of_week_dt, end_of_today_dt)
    ).distinct().all()
    completed_dates = {result[0] for result in recent_activity_dates}

    week_days_status = []
    day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        status = 'pending'
        if current_day < today:
            if current_day in completed_dates:
                status = 'completed'
            elif current_day.weekday() < 5: # Só marca 'lost' em dias úteis
                 status = 'lost'
            else: # Fim de semana inativo
                status = 'weekend'
        elif current_day == today and current_day in completed_dates: # Marca hoje como completed se já houve ação
            status = 'completed'


        week_days_status.append({
            'date': current_day,
            'status': status,
            'is_today': current_day == today,
            'day_name': day_names[i]
        })
    return week_days_status

##DIAS DE VIGILANTE##
def update_user_streak(guardian):
    """
    Atualiza a ofensiva "Dias de Vigilante" de um usuário.
    NOVA LÓGICA: A ofensiva só quebra se houver mais de 1 dia útil de inatividade.
    """
    today = date.today()

    # Ignora a lógica se a ação de hoje já foi registrada
    if guardian.last_streak_date == today:
        return

    # Se o usuário nunca teve uma ofensiva, começa com 1
    if guardian.last_streak_date is None:
        guardian.current_streak = 1
    else:
        days_diff = (today - guardian.last_streak_date).days
        
        # Se a ação foi ontem ou hoje, a ofensiva com certeza continua.
        if days_diff <= 1:
            guardian.current_streak += 1
        else:
            # Conta quantos dias úteis (seg-sex) se passaram entre a última ação e hoje.
            weekdays_passed = 0
            for i in range(1, days_diff):
                day_to_check = guardian.last_streak_date + timedelta(days=i)
                if day_to_check.weekday() < 5: # Segunda (0) a Sexta (4)
                    weekdays_passed += 1
            
            # Se passou 1 dia útil ou menos no meio, a ofensiva continua!
            if weekdays_passed <= 1:
                guardian.current_streak += 1
            # Se passaram 2 ou mais dias úteis, a ofensiva quebra.
            else:
                guardian.current_streak = 1
            
    # Atualiza a data da última ação para hoje
    guardian.last_streak_date = today


#FUNÇÃO QUE ATUALIZA NIVEL
def atualizar_nivel_usuario(guardian, quiz_context=None):
    """
    Função robusta que define ou atualiza o nível de um guardião.
    Ela encontra o NÍVEL MAIS ALTO para o qual o score atual do usuário se qualifica.
    """
    level_up_occurred = False
    old_level_id = guardian.nivel_id

    # A verificação de conquistas agora acontece no final, garantindo que sempre rode.
    novas_conquistas = [] 

    # --- LÓGICA DE NÍVEL (Só executa se o guardião tiver um caminho) ---
    if guardian.specialization:
        
        # 1. Busca TODOS os níveis da especialização do usuário, do MAIOR score para o MENOR.
        trilha_de_niveis = NivelSeguranca.query.filter_by(
            specialization_id=guardian.specialization_id
        ).order_by(NivelSeguranca.score_minimo.desc()).all()

        nivel_correto_para_score = None
        # 2. Encontra o primeiro nível (o mais alto) que o usuário já alcançou com seu score.
        for nivel in trilha_de_niveis:
            if guardian.score_atual >= nivel.score_minimo:
                nivel_correto_para_score = nivel
                break # Encontramos o mais alto, podemos parar o loop.
        
        # 3. Se o nível correto encontrado for diferente do nível atual do guardião, atualizamos.
        if nivel_correto_para_score and nivel_correto_para_score.id != guardian.nivel_id:
            guardian.nivel = nivel_correto_para_score
            level_up_occurred = True

    # --- GATILHO UNIVERSAL DE CONQUISTAS (Executa sempre, após qualquer mudança) ---
    novas_conquistas = check_and_award_achievements(guardian, quiz_context=quiz_context)
    
    return level_up_occurred, novas_conquistas

##ATRIBUI TOKENS DE RETAKE
def check_and_award_retake_token(guardian):
    """
    Verifica se o guardião alcançou o marco para ganhar um novo token de retake de quiz.
    """
    # --- Ponto de Extensibilidade ---
    quizzes_needed = get_global_setting('QUIZZES_FOR_TOKEN', default=5)
    # --------------------------------

    count = guardian.perfect_quiz_cumulative_count or 0
    
    # Verifica se o contador é um múltiplo de 'quizzes_needed' e não é zero
    if count > 0 and count % quizzes_needed == 0:
        guardian.retake_tokens = (guardian.retake_tokens or 0) + 1
        
        # Cria um registro no histórico para notificar o usuário
        history_entry = HistoricoAcao(
            guardian_id=guardian.id,
            descricao=f"Ganhou +1 Token de Retake por completar {count} quizzes perfeitos!",
            pontuacao=0
        )
        db.session.add(history_entry)
        flash(f"Parabéns! Você ganhou +1 Token de Retake por sua dedicação!", "success")
        return True
        
    return False 

def check_and_award_minigame_token(guardian: Guardians):
    """
    Verifica se o guardião atingiu o N de minigames perfeitos
    para ganhar um novo token de retake de minigame.
    """
    try:
        guardian.perfect_minigame_cumulative_count = (guardian.perfect_minigame_cumulative_count or 0) + 1
        threshold = get_global_setting('MINIGAMES_FOR_TOKEN', default=5, setting_type=int)
        
        if threshold > 0 and guardian.perfect_minigame_cumulative_count % threshold == 0:
            guardian.minigame_retake_tokens = (guardian.minigame_retake_tokens or 0) + 1
            db.session.add(guardian)
            
            history_entry = HistoricoAcao(
                guardian_id=guardian.id, 
                descricao=f"Ganhou 1 Token de Retake (Minigame) por completar {threshold} minigames perfeitamente!", 
                pontuacao=0
            )
            db.session.add(history_entry)
        
    except Exception as e:
        print(f"Erro ao checar token de minigame: {e}")


#SISTEMA DE RECOMPENSAS COM BASE EM DROP
def calculate_weekly_coin_reward():
    """
    Calcula a recompensa semanal somando:
    1. Valor Base Garantido (Segurança)
    2. Valor de Sorteio (RNG Ponderado)
    """
    
    # 1. SEGURANÇA: Valor Mínimo Garantido
    base_guaranteed = get_game_setting('WEEKLY_MIN_PASSIVE', 50, int)
    
    # 2. SORTEIO: Busca configurações
    chance_common = get_game_setting('DROP_CHANCE_COMMON', 60, int)
    chance_rare = get_game_setting('DROP_CHANCE_RARE', 30, int)
    chance_epic = get_game_setting('DROP_CHANCE_EPIC', 10, int)
    
    val_common = get_game_setting('DROP_VAL_COMMON', 20, int)
    val_rare = get_game_setting('DROP_VAL_RARE', 50, int)
    val_epic = get_game_setting('DROP_VAL_EPIC', 100, int)
    
    # Define as opções e os pesos
    options = ['COMMON', 'RARE', 'EPIC']
    weights = [chance_common, chance_rare, chance_epic]
    
    # Sorteia baseado nos pesos (k=1 retorna uma lista com 1 item)
    result_type = random.choices(options, weights=weights, k=1)[0]
    
    # Define o valor do sorteio
    rng_value = 0
    if result_type == 'COMMON':
        rng_value = val_common
    elif result_type == 'RARE':
        rng_value = val_rare
    elif result_type == 'EPIC':
        rng_value = val_epic
        
    total_coins = base_guaranteed + rng_value
    
    return {
        'total': total_coins,
        'breakdown': {
            'base': base_guaranteed,
            'rng': rng_value,
            'rarity': result_type # Útil para mostrar animação diferente no front
        }
    }


# ==========================================================
# ============= SISTEMA DE CONQUISTAS ================
# ==========================================================
def check_and_award_achievements(guardian, quiz_context=None):
    """
    Verifica e concede conquistas automáticas a um guardião.
    Refatorado para 6 trilhas principais (Pontos, Quizzes, Minigames, Patrulhas, G-Coins, Reports).
    Retorna uma lista de nomes das novas conquistas ganhas.
    """
    try:
        # 1. Busca todas as conquistas que o guardião AINDA NÃO TEM
        owned_insignia_ids = {gi.insignia_id for gi in guardian.insignias_conquistadas.all()} # .all() é importante aqui
        unearned_insignias = Insignia.query.filter(not_(Insignia.id.in_(owned_insignia_ids))).all()
        
        newly_awarded = []
        
        # 2. Cache de dados para evitar múltiplas buscas
        score = guardian.score_atual
        quiz_count = None
        minigame_count = None
        patrol_count = None
        gcoin_spent_count = None # Usaremos o NÚMERO de compras
        report_count = None

        # 3. Loop apenas nas conquistas não ganhas
        for insignia in unearned_insignias:
            awarded = False
            code = insignia.achievement_code

            # --- TRILHA 1: PONTOS GANHOS (Bônus de Ofensiva) ---
            if code.startswith('SCORE_'):
                # (Ajuste os valores de score como desejar)
                if code == 'SCORE_1' and score >= 100: awarded = True
                elif code == 'SCORE_2' and score >= 1000: awarded = True
                elif code == 'SCORE_3' and score >= 2500: awarded = True
                elif code == 'SCORE_4' and score >= 5000: awarded = True
                elif code == 'SCORE_5' and score >= 10000: awarded = True

            # --- TRILHA 2: QUIZZES FEITOS (Bônus de Quiz) ---
            elif code.startswith('QUIZ_COUNT_'):
                if quiz_count is None: # Busca no banco apenas uma vez
                    quiz_count = guardian.quiz_attempts.count()
                
                if code == 'QUIZ_COUNT_1' and quiz_count >= 1: awarded = True
                elif code == 'QUIZ_COUNT_2' and quiz_count >= 10: awarded = True
                elif code == 'QUIZ_COUNT_3' and quiz_count >= 50: awarded = True
                elif code == 'QUIZ_COUNT_4' and quiz_count >= 100: awarded = True
                elif code == 'QUIZ_COUNT_5' and quiz_count >= 200: awarded = True

            # --- TRILHA 3: MINIGAMES FEITOS (Bônus de Minigame) ---
            elif code.startswith('MINIGAME_'):
                if minigame_count is None: # Busca no banco apenas uma vez
                    termo_count = TermoAttempt.query.filter_by(guardian_id=guardian.id).count()
                    anagram_count = AnagramAttempt.query.filter_by(guardian_id=guardian.id).count()
                    minigame_count = termo_count + anagram_count
                
                if code == 'MINIGAME_1' and minigame_count >= 1: awarded = True
                elif code == 'MINIGAME_2' and minigame_count >= 10: awarded = True
                elif code == 'MINIGAME_3' and minigame_count >= 50: awarded = True
                elif code == 'MINIGAME_4' and minigame_count >= 100: awarded = True
                elif code == 'MINIGAME_5' and minigame_count >= 200: awarded = True

            # --- TRILHA 4: PATRULHAS FEITAS (Bônus de Patrulha) ---
            elif code.startswith('PATROL_'):
                if patrol_count is None: # Busca no banco apenas uma vez
                    patrol_count = guardian.historico_acoes.filter(HistoricoAcao.descricao.like('Realizou Patrulha Diária:%')).count()
                
                if code == 'PATROL_1' and patrol_count >= 1: awarded = True
                elif code == 'PATROL_2' and patrol_count >= 10: awarded = True
                elif code == 'PATROL_3' and patrol_count >= 50: awarded = True
                elif code == 'PATROL_4' and patrol_count >= 100: awarded = True
                elif code == 'PATROL_5' and patrol_count >= 200: awarded = True

            # --- TRILHA 5: G-COINS GASTOS (Bônus de G-Coins) ---
            # (Assumindo que o histórico de compra será 'Comprou %')
            elif code.startswith('GCOIN_'):
                if gcoin_spent_count is None: # Busca no banco apenas uma vez
                    # (Usamos o NÚMERO de compras, não o valor)
                    gcoin_spent_count = guardian.historico_acoes.filter(HistoricoAcao.descricao.like('Comprou %')).count() 
                
                if code == 'GCOIN_1' and gcoin_spent_count >= 1: awarded = True
                elif code == 'GCOIN_2' and gcoin_spent_count >= 3: awarded = True
                elif code == 'GCOIN_3' and gcoin_spent_count >= 5: awarded = True
                elif code == 'GCOIN_4' and gcoin_spent_count >= 10: awarded = True
                elif code == 'GCOIN_5' and gcoin_spent_count >= 20: awarded = True

            # --- TRILHA 6: REPORTS FEITOS (Bônus Indefinido) ---
            
            # --- Lógica de Concessão ---
            if awarded:
                nova_conquista = GuardianInsignia(guardian_id=guardian.id, insignia_id=insignia.id)
                db.session.add(nova_conquista)
                novo_historico = HistoricoAcao(guardian_id=guardian.id, descricao=f"Conquistou a insígnia '{insignia.nome}'!", pontuacao=0)
                db.session.add(novo_historico)
                newly_awarded.append(insignia.nome)
        
        return newly_awarded
    
    except Exception as e:
        print(f"ERRO ao checar conquistas: {e}")
        return []
    
##ORDERNAR CONQUSITAS EM MEU PERFIL###
def get_insignia_category(insignia):
    """ Determina a categoria de uma insígnia com base no seu código. """
    code = insignia.achievement_code.upper() # Usa 'code', ajuste se o campo for outro (ex: 'identificador')

    if code.startswith('LEVEL_'):
        return "Nível"
    elif code.startswith('SCORE_'):
        return "Pontuação"
    elif code.startswith('QUIZ_STREAK_'):
        return "Quizzes Perfeitos"
    elif code.startswith('QUIZ_'):
        return "Quizzes"
    elif code.startswith('STREAK_'):
        return "Ofensiva"
    elif code.startswith('PATROL_'):
        return "Patrulha"
    else:
        return "Outras" # Categoria padrão

def get_achievement_sort_key(insignia):
    """
    Extrai um valor numérico do achievement_code para permitir a ordenação correta.
    Ex: 'LEVEL_10' -> 10, 'SCORE_500' -> 500.
    """
    if insignia.achievement_code:
        # Usa expressão regular para encontrar todos os números no código
        numeros = re.findall(r'\d+', insignia.achievement_code)
        if numeros:
            # Retorna o primeiro número encontrado, convertido para inteiro
            return int(numeros[0])
    
    # Se não encontrar um número no código, usa o requisito_score como fallback
    return insignia.requisito_score if insignia.requisito_score is not None else insignia.id

CATEGORY_ORDER = ["Nível", "Pontuação", "Quizzes Perfeitos", "Quizzes","Ofensiva", "Patrulha", "Outras"]



# ==========================================================
# ============= SISTEMA DA LOJA ================
# ==========================================================
def get_shop_rarity_weights():
    """
    Monta o dicionário de pesos lendo do banco.
    """
    return {
        'COMMON': get_game_setting('SHOP_WEIGHT_COMMON', 60, int),
        'RARE': get_game_setting('SHOP_WEIGHT_RARE', 30, int),
        'EPIC': get_game_setting('SHOP_WEIGHT_EPIC', 8, int),
        'LEGENDARY': get_game_setting('SHOP_WEIGHT_LEGENDARY', 2, int)
    }

def calculate_reroll_cost(current_count):
    """
    Calcula custo dinâmico: Base * (Mult ^ count)
    """
    # Busca configurações no banco
    base_cost = get_game_setting('SHOP_REROLL_BASE_COST', 1, int)
    multiplier = get_game_setting('SHOP_REROLL_MULTIPLIER', 2.0, float)
    
    # Cálculo exponencial
    return int(base_cost * (multiplier ** current_count))

def select_unique_daily_items(amount=4):
    """
    Seleciona 'amount' itens únicos baseados na raridade configurada no banco.
    """
    all_items = ShopItem.query.filter_by(is_active=True).all()
    
    if len(all_items) <= amount:
        return [i.id for i in all_items]

    # 1. Separa itens por raridade
    items_by_rarity = {
        'COMMON': [], 'RARE': [], 'EPIC': [], 'LEGENDARY': []
    }
    
    for item in all_items:
        r = item.rarity if item.rarity in items_by_rarity else 'COMMON'
        items_by_rarity[r].append(item.id)

    # 2. Obtém os pesos dinâmicos do banco
    rarity_weights_dict = get_shop_rarity_weights()
    
    # Prepara listas para o random.choices
    rarities = list(rarity_weights_dict.keys()) # ['COMMON', 'RARE'...]
    weights = list(rarity_weights_dict.values()) # [60, 30, 8, 2]

    selected_ids = set()
    max_attempts = 50 
    attempts = 0
    
    while len(selected_ids) < amount and attempts < max_attempts:
        attempts += 1
        
        # Sorteia a raridade usando os pesos do banco
        chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        pool = items_by_rarity[chosen_rarity]
        
        # Fallback: Se não houver itens dessa raridade, pega de outra pool disponível
        if not pool:
            available_pools = [p for p in items_by_rarity.values() if len(p) > 0]
            if not available_pools:
                break
            pool = random.choice(available_pools)
            
        chosen_id = random.choice(pool)
        selected_ids.add(chosen_id)

    return list(selected_ids)

def get_or_create_shop_state(guardian):
    """Gerencia a persistência diária da loja do jogador."""
    today = date.today()
    state = GuardianShopState.query.filter_by(guardian_id=guardian.id).first()

    # Se não existe, cria
    if not state:
        new_items = select_unique_daily_items(4)
        state = GuardianShopState(
            guardian_id=guardian.id,
            current_items_ids=new_items, # Certifique-se que seu DB suporta JSON ou converta para string
            reroll_count=0,
            last_refresh_date=today
        )
        db.session.add(state)
        db.session.commit()
    
    # Se o dia virou, reseta
    elif state.last_refresh_date < today:
        state.current_items_ids = select_unique_daily_items(4)
        state.reroll_count = 0
        state.last_refresh_date = today
        db.session.add(state)
        db.session.commit()
        
    return state

def perform_shop_reroll(guardian):
    """
    Executa a ação de reroll:
    1. Verifica saldo
    2. Deduz moedas
    3. Gera novos itens
    4. Aumenta contador de reroll
    """
    state = get_or_create_shop_state(guardian)
    cost = calculate_reroll_cost(state.reroll_count)
    
    if guardian.guardian_coins < cost: 
        return {'success': False, 'message': 'Saldo insuficiente.'}
    
    # Deduz saldo
    guardian.guardian_coins -= cost
    
    # Gera novos itens
    state.current_items_ids = select_unique_daily_items(4)
    state.reroll_count += 1

    db.session.commit()
    
    return {
        'success': True, 
        'message': 'Loja atualizada!', 
        'new_items': state.current_items_ids,
        'next_cost': calculate_reroll_cost(state.reroll_count)
    }

##LIMITA OS SLOTS DO INVETÁRIO (3)
def check_shop_slots_available(guardian_id: int) -> bool:
    """
    Verifica se o jogador tem espaço para ativar mais um item passivo.
    Limite: 3 itens ativos simultaneamente.
    """
    MAX_SLOTS = 3
    now = datetime.utcnow()
    active_items_count = 0
    purchases = GuardianPurchase.query.filter_by(guardian_id=guardian_id).all()
    
    for p in purchases:
        # Pula consumíveis (Tokens não ocupam slot de buff)
        if p.item.category == 'Consumíveis':
            continue
            
        # Verifica se ainda está válido
        # (Lógica simplificada, assumindo que duration_days está no item)
        if p.item.duration_days:
            expiration = p.purchased_at + timedelta(days=p.item.duration_days)
            if now < expiration:
                active_items_count += 1
        else:
            # Se for item permanente (duration null), ocupa slot
            active_items_count += 1
            
    return active_items_count < MAX_SLOTS


# ==========================================================
# ============= MOTOR DE BÔNUS (ROGUE-LIKE) ================
# ==========================================================

def _get_spec_bonus(guardian: Guardians, perk_code: str) -> float:
    """
    (Interno) Busca o bônus vindo da Especialização (Caminho).
    """
    if not guardian.specialization_id or not guardian.nivel_id:
        return 0.0
        
    try:
        current_level_number = guardian.nivel.level_number
        
        # Busca o valor do perk para o nível atual (ou inferior mais alto)
        perk_entry = db.session.query(SpecializationPerkLevel)\
            .join(Perk)\
            .filter(
                SpecializationPerkLevel.specialization_id == guardian.specialization_id,
                Perk.perk_code == perk_code,
                SpecializationPerkLevel.level <= current_level_number
            )\
            .order_by(SpecializationPerkLevel.level.desc())\
            .first()
            
        return float(perk_entry.bonus_value) if perk_entry else 0.0
    except Exception:
        return 0.0

def _get_insignia_bonus(guardian: Guardians, perk_code: str) -> float:
    """
    (Interno) Busca o bônus vindo da Insígnia em Destaque.
    """
    if not guardian.featured_insignia_id:
        return 0.0
        
    try:
        insignia = db.session.query(Insignia.bonus_type, Insignia.bonus_value)\
            .filter_by(id=guardian.featured_insignia_id).first()
            
        if insignia and insignia.bonus_value:
            b_type = insignia.bonus_type
            
            # CASO 1: Match Exato (Sempre válido)
            if b_type == perk_code:
                return float(insignia.bonus_value)
            
            # CASO 2: Match Global (Válido APENAS se não for G-Coins)
            if b_type == 'GLOBAL_SCORE_PCT' and not perk_code.startswith('GCOIN'):
                return float(insignia.bonus_value)
                
        return 0.0
    except Exception:
        return 0.0

def _get_shop_bonus(guardian: Guardians, perk_code: str) -> float:
    """
    Calcula o bônus acumulado da loja para um tipo específico.
    """
    try:
        now = datetime.utcnow()
        total_bonus = 0.0
        
        # Otimização: Trazer todas as compras do usuário de uma vez
        purchases = GuardianPurchase.query.filter_by(guardian_id=guardian.id).all()
        
        for p in purchases:
            item = p.item
            
            # 1. Verifica validade (Expiração)
            if item.duration_days:
                expiration = p.purchased_at + timedelta(days=item.duration_days)
                if now >= expiration:
                    continue # Item expirado, ignora
            
            # 2. Verifica se o item fornece o bônus pedido OU é um bônus Global
            # Itens globais (Firewall) somam em quase tudo, exceto moedas e tokens
            is_global_eligible = (item.bonus_type == 'GLOBAL_SCORE_PCT') and \
                     (not perk_code.startswith('GCOIN')) and \
                     ('TOKEN' not in perk_code) and \
                     ('STREAK' not in perk_code)
            
            if item.bonus_type == perk_code or is_global_eligible:
                total_bonus += item.bonus_value

        return float(total_bonus)
    except Exception as e:
        print(f"Erro ao calcular bônus de loja: {e}")
        return 0.0

def get_total_bonus(guardian: Guardians, perk_code: str, default: float = 0.0) -> float:
    """
    [FUNÇÃO MESTRA]
    Calcula o bônus TOTAL acumulado de todas as fontes (Spec + Insígnia + Loja).
    Use esta função em todas as rotas de jogo.
    """
    try:
        spec = _get_spec_bonus(guardian, perk_code)
        insignia = _get_insignia_bonus(guardian, perk_code)
        shop = _get_shop_bonus(guardian, perk_code)
        
        total = spec + insignia + shop
                
        return total if total > 0 else default
        
    except Exception as e:
        print(f"Erro crítico ao calcular bônus total para {perk_code}: {e}")
        return default