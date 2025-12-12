from application.models import db, Guardians, NivelSeguranca, Insignia, GuardianInsignia, HistoricoAcao, QuizAttempt, Question, QuizCategory
from sqlalchemy import not_
from datetime import date, timedelta
import re

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

##BONUS DE VIGILANTE
def apply_streak_bonus(guardian, base_points):
    """
    Calcula e aplica o bônus de ofensiva à pontuação base.
    Retorna a pontuação final e a pontuação bônus.
    """
    if base_points <= 0: # Bônus não se aplica a penalidades
        return base_points, 0

    streak = guardian.current_streak or 0
    bonus_percentage = min(streak, 20) # Limita o bônus a 10%
    
    if bonus_percentage > 0:
        bonus_points = round(base_points * (bonus_percentage / 100.0))
        total_points = base_points + bonus_points
        return total_points, bonus_points
        
    return base_points, 0

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

def check_and_award_achievements(guardian, quiz_context=None):
    """
    Verifica e concede conquistas automáticas a um guardião.
    Retorna uma lista de nomes das novas conquistas ganhas.
    """
    try:
        owned_insignia_ids = {gi.insignia_id for gi in guardian.insignias_conquistadas}
        unearned_insignias = Insignia.query.filter(not_(Insignia.id.in_(owned_insignia_ids))).all()
        newly_awarded = []
        
        # Cache de dados para evitar múltiplas buscas
        report_count = None
        quiz_count = None
        patrol_count = None


        for insignia in unearned_insignias:
            awarded = False
            code = insignia.achievement_code

            
            # --- TRILHA 1: CONQUISTAS BASEADAS EM SCORE ---
            if code == 'SCORE_150' and guardian.score_atual >= 150: awarded = True
            elif code == 'SCORE_400' and guardian.score_atual >= 400: awarded = True
            elif code == 'SCORE_700' and guardian.score_atual >= 700: awarded = True
            elif code == 'SCORE_1100' and guardian.score_atual >= 1100: awarded = True
            elif code == 'SCORE_1900' and guardian.score_atual >= 1900: awarded = True

            
            # --- TRILHA 2: CONQUISTAS BASEADAS EM NIVEL ---
            elif code == 'LEVEL_2' and guardian.nivel and guardian.nivel.id >= 2: awarded = True
            elif code == 'LEVEL_3' and guardian.nivel and guardian.nivel.id >= 3: awarded = True
            elif code == 'LEVEL_4' and guardian.nivel and guardian.nivel.id >= 4: awarded = True
            elif code == 'LEVEL_5' and guardian.nivel and guardian.nivel.id >= 5: awarded = True
            elif code == 'LEVEL_6' and guardian.nivel and guardian.nivel.id >= 6: awarded = True

            
            # --- TRILHA 3: CONQUISTAS BASEADAS QTDE QUIZ---
            elif code.startswith('QUIZ_COUNT_'):
                if quiz_count is None: # Busca no banco apenas uma vez
                    quiz_count = guardian.quiz_attempts.filter(QuizAttempt.score > 0).count()
                
                if code == 'QUIZ_COUNT_1' and quiz_count >= 1: awarded = True
                elif code == 'QUIZ_COUNT_15' and quiz_count >= 15: awarded = True
                elif code == 'QUIZ_COUNT_30' and quiz_count >= 30: awarded = True
                elif code == 'QUIZ_COUNT_60' and quiz_count >= 60: awarded = True
                elif code == 'QUIZ_COUNT_90' and quiz_count >= 90: awarded = True
            
            # --- TRILHA 4: CONQUISTAS ACERTOS DE QUIZ---
          
            elif code.startswith('QUIZ_STREAK_'):
                streak = guardian.perfect_quiz_streak or 0
                if code == 'QUIZ_STREAK_1' and streak >= 1: awarded = True
                elif code == 'QUIZ_STREAK_15' and streak >= 15: awarded = True
                elif code == 'QUIZ_STREAK_30' and streak >= 30: awarded = True
                elif code == 'QUIZ_STREAK_50' and streak >= 50: awarded = True
                elif code == 'QUIZ_STREAK_80' and streak >= 80: awarded = True

            
            # --- TRILHA 5: CONQUISTAS BASEADAS EM OFENSIVA---
            elif code.startswith('STREAK_'):
                streak = guardian.current_streak or 0
                if code == 'STREAK_7' and streak >= 7: awarded = True
                elif code == 'STREAK_14' and streak >= 14: awarded = True
                elif code == 'STREAK_21' and streak >= 21: awarded = True
                elif code == 'STREAK_30' and streak >= 30: awarded = True
                elif code == 'STREAK_60' and streak >= 60: awarded = True
            
            
            # --- TRILHA 6: CONQUISTAS BASEADAS EM PATRULHA---
            elif code.startswith('PATROL_COUNT_'):
                if patrol_count is None: # Busca no banco apenas uma vez
                    patrol_count = guardian.historico_acoes.filter(HistoricoAcao.descricao.like('Patrulha Diária%')).count()
                
                if code == 'PATROL_COUNT_5' and patrol_count >= 5: awarded = True
                elif code == 'PATROL_COUNT_15' and patrol_count >= 15: awarded = True
                elif code == 'PATROL_COUNT_25' and patrol_count >= 25: awarded = True
                elif code == 'PATROL_COUNT_50' and patrol_count >= 50: awarded = True
                elif code == 'PATROL_COUNT_75' and patrol_count >= 75: awarded = True
                
                
            # --- TRILHA 7: CONQUISTAS BASEADAS EM REPORTS DE PHISH---
            elif code.startswith('PHISHING_SIMULATED_'):
                if simulated_report_count is None: # Busca no banco apenas uma vez
                    simulated_report_count = guardian.historico_acoes.filter(HistoricoAcao.descricao.like('%Reporte de Phishing Simulado%')).count()
                
                if code == 'PHISHING_1' and simulated_report_count >= 1: awarded = True
                elif code == 'PHISHING_3' and simulated_report_count >= 3: awarded = True
                elif code == 'PHISHING_5' and simulated_report_count >= 5: awarded = True
                elif code == 'PHISHING_10' and simulated_report_count >= 10: awarded = True
                elif code == 'PHISHING_15' and simulated_report_count >= 15: awarded = True
            
            elif code == 'PHISHING_REAL_1':
                if real_report_count is None: # Busca no banco apenas uma vez
                    real_report_count = guardian.historico_acoes.filter(HistoricoAcao.descricao.like('%Reporte de Phishing Real%')).count()
                
                if real_report_count >= 1:
                    awarded = True
            
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

def atualizar_nivel_usuario(guardian, quiz_context=None):
    """
    Verifica se o usuário subiu de nível e ATIVA O GATILHO de verificação de conquistas.
    Retorna uma tupla: (bool se subiu de nível, lista de novas conquistas).
    """
    level_up_occurred = False
    nivel_atual = guardian.nivel
    if not nivel_atual:
        return False, [] # Sai se o usuário não tiver um nível inicial

    proximo_nivel = NivelSeguranca.query.filter(NivelSeguranca.score_minimo > nivel_atual.score_minimo).order_by(NivelSeguranca.score_minimo.asc()).first()
    
    if proximo_nivel and guardian.score_atual >= proximo_nivel.score_minimo:
        guardian.nivel = proximo_nivel
        level_up_occurred = True
    
    # --- GATILHO UNIVERSAL DE CONQUISTAS ---
    # Sempre que o nível é verificado (após uma mudança de pontos), checamos as conquistas.
    novas_conquistas = check_and_award_achievements(guardian, quiz_context=quiz_context)
    
    return level_up_occurred, novas_conquistas


