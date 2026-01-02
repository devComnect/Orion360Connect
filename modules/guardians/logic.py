import re, random
from sqlalchemy import not_, func
from datetime import date, timedelta, datetime
from flask import flash, g
from application.models import (db, Guardians, NivelSeguranca, Insignia, GuardianInsignia, 
                                HistoricoAcao, SpecializationPerkLevel, Perk, GlobalGameSettings, QuizAttempt,
                                TermoAttempt, AnagramAttempt, GuardianPurchase, ShopItem, GuardianShopState, PasswordAttempt)

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
            return default_value
            
    return default_value

def get_global_setting(key, default=None, setting_type=int):
    """
    Busca uma configuração global do jogo de forma eficiente, usando um cache por requisição.
    
    :param key: A chave da configuração (ex: 'PATROL_MIN_POINTS').
    :param default: O valor a ser retornado se a chave não for encontrada.
    :param setting_type: O tipo de dado para o qual o valor deve ser convertido (int, float, str).
    """
    if 'game_settings' not in g:
        settings = GlobalGameSettings.query.all()
        g.game_settings = {s.setting_key: s.setting_value for s in settings}

    value = g.game_settings.get(key, default)

    try:
        return setting_type(value)
    except (ValueError, TypeError):
        return default

##CALCULA PONTUAÇÃO FINAL APÓS TODOS OS BONUS E GARANTE O BONUS DE OFENSIVA AO FINAL (CASO NÃO TENHA)
def calculate_final_score(guardian: Guardians, current_total_score: int, raw_base_score: int, perk_code: str = None):
    """
    [FUNÇÃO MESTRA DE PONTUAÇÃO]
    Calcula pontuação final somando: Spec + Conquistas (Múltiplas) + Loja + Streak.
    """

    score_with_bonuses = current_total_score
    
    bonus_breakdown = {
        'spec_bonus': 0,    
        'conquista_bonus': 0,
        'loja_bonus': 0,
        'streak_total_bonus': 0,
        'streak_base_bonus': 0,
        'streak_spec_bonus': 0
    }

    if perk_code:
        # --- 1. BÔNUS DE ESPECIALIZAÇÃO (SPEC) ---
        spec_pct = get_active_perk_value(guardian, perk_code, default=0)
        
        if spec_pct > 0:
            spec_val = int(round(raw_base_score * (spec_pct / 100.0)))
            bonus_breakdown['spec_bonus'] = spec_val
            score_with_bonuses += spec_val

        # --- 2. BÔNUS DE CONQUISTA (MÚLTIPLAS) ---
        total_badge_bonus = 0

        if guardian.featured_associations:
            for assoc in guardian.featured_associations:
                insignia = assoc.insignia
                
                if insignia and insignia.bonus_value:
                    b_type = insignia.bonus_type
                    b_val_pct = float(insignia.bonus_value)
                    
                    is_exact_match = (b_type == perk_code)
                    is_global = (b_type == 'GLOBAL_SCORE_PCT' and not perk_code.startswith('GCOIN'))
                    
                    if is_exact_match or is_global:
                        badge_val = int(round(raw_base_score * (b_val_pct / 100.0)))
                        total_badge_bonus += badge_val

        bonus_breakdown['conquista_bonus'] = total_badge_bonus
        score_with_bonuses += total_badge_bonus

        # --- 3. BÔNUS DE LOJA ---
        shop_bonus_pct = _get_shop_bonus(guardian, perk_code)
        if shop_bonus_pct > 0:
            shop_val = int(round(raw_base_score * (shop_bonus_pct / 100.0)))
            bonus_breakdown['loja_bonus'] = shop_val
            score_with_bonuses += shop_val


    # --- 4. BÔNUS DE OFENSIVA (STREAK) ---
    effective_percent = get_effective_streak_percentage(guardian)
    base_streak_val = int(round(score_with_bonuses * (effective_percent / 100.0)))
    spec_streak_pct = get_active_perk_value(guardian, 'STREAK_BONUS_PCT', default=0)
    
    spec_streak_val = 0
    if spec_streak_pct > 0:
        spec_streak_val = int(round(base_streak_val * (spec_streak_pct / 100.0)))
    
    total_streak_bonus = base_streak_val + spec_streak_val
    
    bonus_breakdown['streak_total_bonus'] = total_streak_bonus
    bonus_breakdown['streak_base_bonus'] = base_streak_val
    bonus_breakdown['streak_spec_bonus'] = spec_streak_val

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
    Calcula bônus de performance (Tempo e Perfeição).
    
    ATUALIZAÇÕES:
    - Tempo: Lógica de Threshold (Menor que X segundos = ganha fixo).
    - Perfeição: Minigame de Senha/Cofre conta para estatística/token, mas NÃO dá pontos extras de perfeição.
    """
    
    time_bonus = 0
    perfection_bonus = 0

    total_possible = context.get('total_possible_points', 0)
    score_check = context.get('raw_score_before_perks', 0)
    is_perfect = (score_check == total_possible and total_possible > 0)
    minigame_type = context.get('minigame_type')

    # ====================================================
    # 1. CÁLCULO DO BÔNUS DE VELOCIDADE (Threshold Logic)
    # ====================================================
    duration = context.get('duration_seconds')
    speed_limit_key = None

    if event_type == 'quiz':
        speed_limit_key = 'SPEED_LIMIT_QUIZ'
    elif event_type == 'minigame':
        if minigame_type == 'termo':
            speed_limit_key = 'SPEED_LIMIT_TERMO'
        elif minigame_type == 'anagram':
            speed_limit_key = 'SPEED_LIMIT_ANAGRAM'
        elif minigame_type == 'password':
            speed_limit_key = 'SPEED_LIMIT_PASSWORD'
    
    if speed_limit_key and duration is not None:
        limit_seconds = get_global_setting(speed_limit_key, default=0, setting_type=int)
        
        # Se bateu o tempo limite
        if limit_seconds > 0 and duration <= limit_seconds:
            base_time_bonus = get_global_setting('TIME_BONUS_DIVISOR', default=20, setting_type=int)
            
            # Aplica Buffs de Velocidade
            speed_mult_pct = get_total_bonus(guardian, 'SPEED_BONUS_PCT') 
            if speed_mult_pct > 0:
                boost_val = int(base_time_bonus * (speed_mult_pct / 100.0))
                time_bonus = base_time_bonus + boost_val
            else:
                time_bonus = base_time_bonus
    
    # ====================================================
    # 2. CÁLCULO DO BÔNUS DE PERFEIÇÃO
    # ====================================================
    
    streak_threshold = get_global_setting('PERFECT_STREAK_THRESHOLD', default=3, setting_type=int)
    
    if is_perfect:
        base_perf_bonus = 0
        
        if event_type == 'quiz':
            guardian.perfect_quiz_streak = (guardian.perfect_quiz_streak or 0) + 1
            guardian.perfect_quiz_cumulative_count = (guardian.perfect_quiz_cumulative_count or 0) + 1
            
            try:
                check_and_award_retake_token(guardian) 
            except Exception as e:
                print(f"Erro ao dar token quiz: {e}")
            
            bonus_val = get_global_setting('PERFECT_QUIZ_STREAK_BONUS', default=10, setting_type=int)
            
            if guardian.perfect_quiz_streak > 0 and guardian.perfect_quiz_streak % streak_threshold == 0:
                base_perf_bonus = bonus_val
        
        elif event_type == 'minigame':

            try:
                check_and_award_minigame_token(guardian)
            except Exception as e:
                print(f"Erro ao dar token minigame: {e}")
            
            if minigame_type in ['password', 'secret', 'senha']:
                base_perf_bonus = 0
            else:
                guardian.perfect_minigame_streak = (guardian.perfect_minigame_streak or 0) + 1
                
                bonus_val = get_global_setting('PERFECT_MINIGAME_BONUS', default=10, setting_type=int)
                
                if guardian.perfect_minigame_streak > 0 and guardian.perfect_minigame_streak % streak_threshold == 0:
                    base_perf_bonus = bonus_val

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
            
        elif event_type == 'minigame':
             guardian.perfect_minigame_streak = 0

    return {
        'time_bonus': int(time_bonus),
        'perfection_bonus': int(perfection_bonus),
        'is_perfect': is_perfect
    }

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

#CALCULA STREAK DE OFENSIVA
def get_streak_cap(guardian):
    """
    Calcula o TETO MÁXIMO da ofensiva (Cap).
    Base (ex: 10%) + Bônus específicos de itens/conquistas (STREAK_BONUS_PCT).
    """
    base_cap = int(get_global_setting('STREAK_BONUS_CAP_PERCENT', default=10))
    extra_cap = 0.0

    extra_cap += db.session.query(func.sum(ShopItem.bonus_value))\
        .join(GuardianPurchase, GuardianPurchase.item_id == ShopItem.id)\
        .filter(
            GuardianPurchase.guardian_id == guardian.id,
            ShopItem.bonus_type == 'STREAK_BONUS_PCT',
            (GuardianPurchase.expires_at == None) | (GuardianPurchase.expires_at > datetime.utcnow())
        ).scalar() or 0.0

    extra_cap += db.session.query(func.sum(Insignia.bonus_value))\
        .join(GuardianInsignia, GuardianInsignia.insignia_id == Insignia.id)\
        .filter(
            GuardianInsignia.guardian_id == guardian.id,
            Insignia.bonus_type == 'STREAK_BONUS_PCT' 
        ).scalar() or 0.0

    return base_cap + int(extra_cap)

def get_effective_streak_percentage(guardian):
    """
    Calcula a % atual da ofensiva.
    Regra: 1% por dia, limitado pelo Teto Dinâmico.
    """
    streak_days = guardian.current_streak or 0
    
    if streak_days <= 0:
        return 0 

    raw_percentage = float(streak_days)
    user_cap = get_streak_cap(guardian)
    final_percentage = min(raw_percentage, user_cap)

    return round(final_percentage, 2)

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

##ATUALIZA OS DIAS DE VIGILANTE E REMOVE STREAK##
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
def atualizar_nivel_usuario(guardian):
    """
    Sincroniza o progresso do guardião:
    1. Verifica se o XP atual permite subir de nível.
    2. Verifica se alguma nova conquista foi desbloqueada (Score, Quiz, Minigame, Patrulha, Loja).
    
    Retorna:
        (level_up_occurred: bool, novas_conquistas: list)
    """
    level_up_occurred = False
    
    # --- 1. LÓGICA DE NÍVEL (Level Up) ---
    if guardian.specialization_id:

        trilha_de_niveis = NivelSeguranca.query.filter_by(
            specialization_id=guardian.specialization_id
        ).order_by(NivelSeguranca.score_minimo.desc()).all()

        nivel_alvo = None
        
        for nivel in trilha_de_niveis:
            if guardian.score_atual >= nivel.score_minimo:
                nivel_alvo = nivel
                break 
        
        if nivel_alvo and nivel_alvo.id != guardian.nivel_id:
            guardian.nivel = nivel_alvo
            level_up_occurred = True
            log = HistoricoAcao(guardian_id=guardian.id, descricao=f"Promovido para {nivel_alvo.nome}", pontuacao=0)
            db.session.add(log)

    # --- 2. GATILHO DE CONQUISTAS (Achievements) ---
    novas_conquistas = check_and_award_achievements(guardian)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao sincronizar nível/conquistas: {e}")

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
def check_and_award_achievements(guardian):
    
    # 1. Carrega estatísticas DIRETAMENTE das novas colunas
    # (O 'or 0' garante que não quebre se for None por algum motivo legado)
    current_score = guardian.score_atual or 0
    quiz_count = guardian.stat_quiz_count or 0
    patrol_count = guardian.stat_patrol_count or 0
    minigame_count = guardian.stat_minigame_count or 0
    shop_count = guardian.stat_shop_count or 0


    # 2. Prepara listas
    # Pega IDs que eu já tenho (usando .all() se for lazy dynamic)
    if hasattr(guardian.insignias_conquistadas, 'all'):
        my_insignia_ids = [gi.insignia_id for gi in guardian.insignias_conquistadas.all()]
    else:
        my_insignia_ids = [gi.insignia_id for gi in guardian.insignias_conquistadas]

    all_insignias = Insignia.query.all()
    unearned = [ins for ins in all_insignias if ins.id not in my_insignia_ids]
    
    newly_awarded = []

    # 3. Avaliação
    for insignia in unearned:
        code = insignia.achievement_code
        awarded = False

        try:
            parts = code.split('_')
            level = int(parts[-1]) 
        except:
            continue

        # --- TRILHAS ---
        if code.startswith('SCORE_'):
            reqs = {1: 500, 2: 2500, 3: 5000, 4: 10000, 5: 20000}
            if current_score >= reqs.get(level, 999999): awarded = True

        elif code.startswith('QUIZ_COUNT_'): 
            reqs = {1: 1, 2: 10, 3: 25, 4: 50, 5: 100}
            if quiz_count >= reqs.get(level, 9999): awarded = True

        elif code.startswith('PATROL_'):
            reqs = {1: 1, 2: 7, 3: 14, 4: 30, 5: 60}
            if patrol_count >= reqs.get(level, 9999): awarded = True

        elif code.startswith('MINIGAME_'):
            reqs = {1: 1, 2: 10, 3: 25, 4: 50, 5: 100}
            if minigame_count >= reqs.get(level, 9999): awarded = True

        elif code.startswith('SHOP_'):
            reqs = {1: 1, 2: 5, 3: 10, 4: 20, 5: 50}
            if shop_count >= reqs.get(level, 9999): awarded = True

        # --- CONCESSÃO ---
        if awarded:
            new_grant = GuardianInsignia(
                guardian_id=guardian.id,
                insignia_id=insignia.id,
                data_conquista=datetime.utcnow()
            )
            db.session.add(new_grant)
            newly_awarded.append(insignia)

    # 4. Commit apenas se houve ganho
    if newly_awarded:
        try:
            db.session.commit()
            return newly_awarded
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar conquistas: {e}")
            return []
    
    return []
    
##ORDERNAR CONQUSITAS EM MEU PERFIL###
def get_insignia_category(insignia):
    """ 
    Determina a categoria de uma insígnia com base no prefixo do seu código. 
    Retorna a string exata da categoria para exibição no template.
    """
    code = insignia.achievement_code.upper() 

    if code.startswith('QUIZ_'):
        return "Por Quiz"

    elif code.startswith('MINIGAME_'):
        return "Por Minigame"

    elif code.startswith('PATROL_'):
        return "Por Patrulha"

    elif code.startswith('STREAK_'):
        return "Por Ofensiva"

    elif code.startswith('ITEM_') or code.startswith('SHOP_'):
        return "Por Items comprados"

    elif code.startswith('LEVEL_') or code.startswith('SCORE_') or code.startswith('PERFORMANCE_'):
        return "Por Desempenho"

    elif code.startswith('PHISH_') or code.startswith('REPORT_'):
        return "Por Report de Phish"

    elif code.startswith('PODIUM_') or code.startswith('TOP_'):
        return "Por Pódio"

    else:
        return "Outras"

def get_achievement_sort_key(insignia):
    """
    Extrai um valor numérico do achievement_code para permitir a ordenação correta.
    Ex: 'LEVEL_10' -> 10, 'SCORE_500' -> 500.
    """
    if insignia.achievement_code:
        numeros = re.findall(r'\d+', insignia.achievement_code)
        if numeros:
            return int(numeros[0])
    
    return insignia.requisito_score if insignia.requisito_score is not None else insignia.id




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
            current_items_ids=new_items, 
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

##LIMITA OS SLOTS DO INVETÁRIO
def check_shop_slots_available(guardian_id: int) -> bool:
    """
    Verifica se o jogador tem espaço para ativar mais um item passivo.
    """
    max_slots = get_game_setting('ITEMS_MODULES_SET_AMOUNT', 4, int)
    now = datetime.utcnow()
    active_items_count = 0
    purchases = GuardianPurchase.query.filter_by(guardian_id=guardian_id).all()
    
    for p in purchases:
        if p.item.category == 'Consumíveis':
            continue
            
        if p.item.duration_days:
            expiration = p.purchased_at + timedelta(days=p.item.duration_days)
            if now < expiration:
                active_items_count += 1
        else:
            active_items_count += 1
            
    return active_items_count < max_slots


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
    (Interno) Calcula o bônus TOTAL acumulado de TODAS as Insígnias em Destaque ativas.
    """
    total_bonus = 0.0
    
    if not guardian.featured_associations:
        return 0.0
        
    try:
        for assoc in guardian.featured_associations:
            insignia = assoc.insignia 
            
            if insignia and insignia.bonus_value:
                b_type = insignia.bonus_type
                valor_atual = float(insignia.bonus_value)
                

                if b_type == perk_code:
                    total_bonus += valor_atual
                

                elif b_type == 'GLOBAL_SCORE_PCT' and not perk_code.startswith('GCOIN'):
                    total_bonus += valor_atual
            
        return total_bonus

    except Exception as e:
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
