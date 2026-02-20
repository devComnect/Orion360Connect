# modules/guardians/missions_logic.py

import random
from datetime import datetime
from application.models import (db, Guardians, MissionTemplate, WeeklyQuestSet, 
                       ActiveMission, MissionCodeEnum, HistoricoAcao, MissionDifficultyEnum, MissionTypeEnum)

# --- FUNÇÃO 1: O GERADOR DE MISSÕES ---

def get_or_create_active_quest_set(guardian: Guardians) -> dict:
    """
    Verifica se existe um pacote de missões ATIVO e NÃO RESGATADO.
    Se não existir (ou se o último já foi resgatado 'is_claimed=True'), 
    cria um novo pacote imediatamente.
    """
    
    # 1. Busca o último pacote criado para este guardião
    last_set = guardian.weekly_quest_sets.order_by(
        WeeklyQuestSet.id.desc()
    ).first()

    # 2. Verifica se o último pacote existe e se AINDA ESTÁ VALENDO
    # (Ou seja, não foi completado OU foi completado mas não resgatado)
    if last_set and not last_set.is_claimed:
        # Atualiza passivas (Streak) e retorna o set atual
        _update_passive_missions(guardian, last_set)
        return {
            'set': last_set,
            'missions': last_set.missions.all()
        }

    # 3. Se não existe nenhum OU o último já foi resgatado (is_claimed=True):
    # CRIA UM NOVO PACOTE AGORA.
    
    # Busca templates ativos
    all_templates = MissionTemplate.query.filter_by(is_active=True).all()
    
    # Garante 3 missões
    num_to_draw = min(len(all_templates), 3) 
    if num_to_draw == 0:
        return {'set': None, 'missions': []} 

    if last_set:
        new_week = last_set.week_number + 1
        new_year = last_set.year
        
        # Vira o ano se passar de 52 semanas (apenas para manter coerência visual)
        if new_week > 52:
            new_week = 1
            new_year += 1
    else:
        # Se é o primeiro de todos, pega a data real
        new_year, new_week, _ = datetime.now().isocalendar()
    
    new_quest_set = WeeklyQuestSet(
        guardian_id=guardian.id,
        week_number=new_week, # Mantemos apenas como "data de criação"
        year=new_year,
        bonus_reward_placeholder=0, 
        is_completed=False,
        is_claimed=False
    )
    try:
        db.session.add(new_quest_set)
        db.session.flush() 

        # --- NOVA LÓGICA DE SORTEIO BALANCEADO ---
        
        # 1. Carrega templates ativos agrupados por dificuldade
        templates_easy = MissionTemplate.query.filter_by(is_active=True, difficulty=MissionDifficultyEnum.EASY).all()
        templates_medium = MissionTemplate.query.filter_by(is_active=True, difficulty=MissionDifficultyEnum.MEDIUM).all()
        templates_hard = MissionTemplate.query.filter_by(is_active=True, difficulty=MissionDifficultyEnum.HARD).all()
        
        selected_templates = []
        used_types = set() # Para evitar repetição de categoria (ex: 2 quizzes)

        # Função auxiliar para escolher sem repetir tipo
        def pick_template(pool, current_used_types):
            if not pool: return None
            # Tenta filtrar os que tem tipo diferente
            candidates = [t for t in pool if t.mission_type not in current_used_types]
            
            # Se não tiver candidatos únicos (ex: só tem missões de quiz na pool), pega qualquer um da pool
            if not candidates:
                choice = random.choice(pool)
            else:
                choice = random.choice(candidates)
            
            return choice

        # Slot 1: Fácil
        t_easy = pick_template(templates_easy, used_types)
        if t_easy:
            selected_templates.append(t_easy)
            used_types.add(t_easy.mission_type)

        # Slot 2: Médio
        t_medium = pick_template(templates_medium, used_types)
        if t_medium:
            selected_templates.append(t_medium)
            used_types.add(t_medium.mission_type)
            
        # Slot 3: Difícil
        t_hard = pick_template(templates_hard, used_types)
        if t_hard:
            selected_templates.append(t_hard)
            used_types.add(t_hard.mission_type)

        # Fallback: Se não conseguiu 3 missões (falta de templates no banco), completa com aleatórios gerais
        if len(selected_templates) < 3:
            all_active = MissionTemplate.query.filter_by(is_active=True).all()
            remaining = 3 - len(selected_templates)
            # Remove os já selecionados da pool
            pool_rest = [t for t in all_active if t not in selected_templates]
            if pool_rest:
                selected_templates.extend(random.sample(pool_rest, min(len(pool_rest), remaining)))

        # Criação das ActiveMissions no Banco
        new_active_missions = []
        for template in selected_templates:
            target_value = random.randint(template.min_target, template.max_target)
            title_generated = template.description_template.format(target=target_value)
            
            new_mission = ActiveMission(
                quest_set_id=new_quest_set.id,
                mission_template_id=template.id,
                title_generated=title_generated,
                mission_code=template.mission_code,
                target_value=target_value,
                current_progress=0,
                is_completed=False
            )
            db.session.add(new_mission)
            new_active_missions.append(new_mission)

        db.session.commit()
        _update_passive_missions(guardian, new_quest_set)
        
        return {
            'set': new_quest_set,
            'missions': new_active_missions
        }
    
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar set de missões: {e}")
        # Retorna vazio para não quebrar a página
        return {'set': None, 'missions': []}


# --- FUNÇÃO 2: O MOTOR DE PROGRESSO ---

def update_mission_progress(guardian: Guardians, mission_code_to_update: MissionCodeEnum, amount: int = 1):
    """
    Encontra uma missão ativa no pacote ATUAL (não resgatado) e incrementa.
    """
    
    # 1. Busca a missão ativa associada ao pacote NÃO RESGATADO mais recente
    # Join em WeeklyQuestSet para filtrar apenas sets is_claimed=False
    active_mission = ActiveMission.query.join(WeeklyQuestSet).filter(
        WeeklyQuestSet.guardian_id == guardian.id,
        WeeklyQuestSet.is_claimed == False,
        ActiveMission.mission_code == mission_code_to_update,
        ActiveMission.is_completed == False
    ).first()

    if active_mission:
        try:
            active_mission.current_progress += amount
            
            if active_mission.current_progress >= active_mission.target_value:
                active_mission.current_progress = active_mission.target_value 
                active_mission.is_completed = True
                
                _check_quest_set_completion(active_mission.quest_set)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro update progress: {e}")


# --- FUNÇÃO HELPER (USO INTERNO) ---

def _check_quest_set_completion(quest_set: WeeklyQuestSet):
    """Verifica se todas as missões de um baú estão completas."""
    
    # Pega todas as missões do baú
    all_missions = quest_set.missions.all()
    
    # all() retorna True se a lista estiver vazia ou se todos os 'is_completed' forem True
    if all(m.is_completed for m in all_missions):
        quest_set.is_completed = True
        # (O commit será feito pela função 'update_mission_progress' que chamou esta)


def _update_passive_missions(guardian: Guardians, quest_set: WeeklyQuestSet):
    """
    Atualiza missões que dependem de estado (como STREAK), 
    não de um evento (como clicar em patrulha).
    """
    
    # 1. Atualiza a Missão de STREAK
    streak_mission = quest_set.missions.filter_by(
        mission_code=MissionCodeEnum.STREAK_DAYS, 
        is_completed=False
    ).first()
    
    if streak_mission:
        current_streak = guardian.current_streak or 0
        streak_mission.current_progress = current_streak
        
        if current_streak >= streak_mission.target_value:
            streak_mission.is_completed = True
            _check_quest_set_completion(quest_set)
        
        db.session.commit()