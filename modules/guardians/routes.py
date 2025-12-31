# modules/guardians/routes.py
import traceback
import os, uuid, random
<<<<<<< HEAD
from flask_login import current_user
from werkzeug.utils import secure_filename
from collections import defaultdict
=======
from werkzeug.utils import secure_filename
>>>>>>> origin/guardians
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, not_, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified
<<<<<<< HEAD
from flask import Blueprint, abort, render_template, redirect, url_for, request, flash, session, jsonify, current_app, json
from modules.guardians.missions_logic import update_mission_progress, get_or_create_active_quest_set
from modules.login.decorators import login_required
from modules.login.session_manager import SessionManager
from modules.guardians.password_game_rules import generate_rules_sequence, get_rules_details, validate_password_backend, PASSWORD_RULES_DB, get_game_config
from application.models import (MissionCodeEnum, db, TermoGame, Guardians, HistoricoAcao, NivelSeguranca, Insignia, 
                                EventoPontuacao, Quiz, AnswerOption, QuizAttempt, UserAnswer, Specialization, 
                                TermoAttempt, AnagramGame, AnagramAttempt, SpecializationPerkLevel, GuardianInsignia, 
                                Perk, FeedbackReport, GameSeason, WeeklyQuestSet, ShopItem, GuardianPurchase, PasswordAttempt, PasswordGameConfig)
from .logic import (
    update_user_streak, atualizar_nivel_usuario, get_achievement_sort_key, get_active_perk_value, 
    get_global_setting, calculate_week_days_status, get_effective_streak_percentage, calculate_weekly_coin_reward,
    get_insignia_category, calculate_final_score, calculate_performance_bonuses, calculate_reroll_cost, get_game_setting,
    check_shop_slots_available, _get_shop_bonus, _get_insignia_bonus, get_or_create_shop_state, select_unique_daily_items)
=======
from flask import abort, render_template, redirect, url_for, request, flash, session, jsonify, current_app, json
from modules.guardians.missions_logic import update_mission_progress, get_or_create_active_quest_set
from modules.login.decorators import login_required
from modules.login.session_manager import SessionManager
from modules.guardians.password_game_rules import generate_rules_sequence, get_rules_details, validate_password_backend, get_game_config
from application.models import (MissionCodeEnum, db, TermoGame, Guardians, HistoricoAcao, NivelSeguranca, Insignia, GuardianFeatured,
                                EventoPontuacao, Quiz, QuizAttempt, UserAnswer, TermoAttempt, AnagramGame, AnagramAttempt, FeedbackReport, 
                                GameSeason, WeeklyQuestSet, ShopItem, GuardianPurchase, PasswordAttempt, PasswordGameConfig)
from .logic import (
    update_user_streak, atualizar_nivel_usuario, get_achievement_sort_key, get_active_perk_value, get_total_bonus,
    get_global_setting, calculate_weekly_coin_reward,
    calculate_final_score, calculate_performance_bonuses, calculate_reroll_cost, get_game_setting,
    check_shop_slots_available, _get_shop_bonus, _get_insignia_bonus, get_or_create_shop_state, select_unique_daily_items)
from .utils_assistant import get_assistant_data
>>>>>>> origin/guardians
from . import guardians_bp

#UPLOAD DE PRINTS PARA REPORT DE BUGS#
UPLOAD_FOLDER_FEEDBACK = 'static/uploads/feedback'
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file_img(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG

<<<<<<< HEAD
=======
#UPLOAD DE PRINTS PARA REPORT DE BUGS#
UPLOAD_FOLDER_FEEDBACK = 'static/uploads/feedback'
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file_img(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG

>>>>>>> origin/guardians
# Definição Global de Tipos de Bônus (Usado em Loja, Conquistas e Specs)
BONUS_TYPES = {
    # --- Ganhos de XP Específicos ---
    'QUIZ_BONUS_PCT': 'Bônus de % em Quizzes',
    'TERMO_BONUS_PCT': 'Bônus de % no Código (Carderno DNS)',
    'ANAGRAM_BONUS_PCT': 'Bônus de % no Decriptar (Certificado)',
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
<<<<<<< HEAD

@guardians_bp.route('/meu-perfil', defaults={'perfil_id': None})
@guardians_bp.route('/meu-perfil/<int:perfil_id>')
@login_required
def meu_perfil(perfil_id):

    logged_in_user_id = SessionManager.get("user_id")
    profile_guardian_id = None 
    is_own_profile = False
    logged_in_guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if perfil_id is None:
        profile_guardian_id = logged_in_user_id 
        is_own_profile = True
        query_filter = Guardians.user_id == profile_guardian_id
    else:
        profile_guardian_id = perfil_id # 
        query_filter = Guardians.id == profile_guardian_id
        temp_guardian = Guardians.query.get(profile_guardian_id) 
        if temp_guardian and temp_guardian.user_id == logged_in_user_id:
             is_own_profile = True

    perfil = Guardians.query.options(
        joinedload(Guardians.nivel),
        joinedload(Guardians.specialization),
        joinedload(Guardians.featured_insignia) if hasattr(Guardians, 'featured_insignia') else None,
    ).filter(query_filter).first()

    if not perfil:
        flash("Perfil de Guardião não encontrado.", "danger")
        return redirect(url_for("home_bp.render_home")) 

    if not is_own_profile and perfil.is_anonymous:
        flash('Este guardião optou por manter o perfil privado.', 'info')
        return redirect(url_for('guardians_bp.rankings'))

    guardian_insignias_entries = GuardianInsignia.query.filter_by(
        guardian_id=perfil.id
    ).options(
        joinedload(GuardianInsignia.insignia) 
    ).all()
    insignias_ganhas = [gi.insignia for gi in guardian_insignias_entries if gi.insignia]
    grouped_insignias = defaultdict(list)
    for insignia in insignias_ganhas:
        category = get_insignia_category(insignia)
        grouped_insignias[category].append(insignia)

    CATEGORY_ORDER = ["Nível", "Pontuação", "Ofensiva", "Quizzes Perfeitos", "Quizzes", "Patrulha", "Anagramas", "Termo", "Outras"]
    categorized_achievements_list = []
    for category_name in CATEGORY_ORDER:
        if category_name in grouped_insignias:
            categorized_achievements_list.append({
                'category': category_name,
                'insignias': grouped_insignias[category_name]
            })

    effective_streak_percent = get_effective_streak_percentage(perfil)
    week_days_data = calculate_week_days_status(perfil)
    active_perks_list = []

    # 0. BÔNUS DE OFENSIVA (DIARIO)
    if effective_streak_percent > 0:
        desc_streak = f"+{effective_streak_percent}% de Pontos Globais"
        active_perks_list.append(f"<strong class='text-danger'><i class='bi bi-fire'></i> Ofensiva:</strong> Bônus global de +{perfil.current_streak}%")

    # 1. BÔNUS DE ESPECIALIZAÇÃO (CAMINHO)
    if perfil.specialization_id and perfil.nivel_id:
        current_level_number = perfil.nivel.level_number
        perk_entries = db.session.query(SpecializationPerkLevel).join(Perk).filter(
            SpecializationPerkLevel.specialization_id == perfil.specialization_id,
            SpecializationPerkLevel.level == current_level_number
        ).options(
            joinedload(SpecializationPerkLevel.perk) 
        ).order_by(
            SpecializationPerkLevel.level, Perk.name
        ).all()

        for entry in perk_entries:
            value_display = int(entry.bonus_value) if entry.bonus_value == int(entry.bonus_value) else entry.bonus_value
            description = entry.perk.description_template.format(value=value_display)
            active_perks_list.append(f"<strong>{entry.perk.name} (Nv.{entry.level}):</strong> {description}")

    # 2. BÔNUS DE CONQUISTA EM DESTAQUE
    if perfil.featured_insignia and perfil.featured_insignia.bonus_value:
        ins = perfil.featured_insignia
        desc_bonus = f"Bônus de {ins.bonus_value}%" 
        
        # Formatação amigável
        if ins.bonus_type == 'QUIZ_BONUS_PCT': desc_bonus = f"+{ins.bonus_value}% pts em Quizzes"
        elif ins.bonus_type == 'PATROL_BONUS_PCT': desc_bonus = f"+{ins.bonus_value}% pts em Patrulhas"
        elif ins.bonus_type == 'CODEGAME_BONUS_PCT': desc_bonus = f"+{ins.bonus_value}% pts em Minigames"
        elif ins.bonus_type == 'STREAK_BONUS_PCT': desc_bonus = f"+{ins.bonus_value}% pts de Ofensiva"
        elif ins.bonus_type == 'GLOBAL_SCORE_PCT': desc_bonus = f"+{ins.bonus_value}% pts Globais"
        
        active_perks_list.append(f"<strong class='text-warning'><i class='bi bi-trophy-fill'></i> {ins.nome}:</strong> {desc_bonus}")

    try:
        shop_bonuses = db.session.query(ShopItem)\
            .join(GuardianPurchase, ShopItem.id == GuardianPurchase.item_id)\
            .filter(
                GuardianPurchase.guardian_id == perfil.id,
                ShopItem.bonus_value > 0,
                ShopItem.bonus_type.isnot(None),
                ShopItem.is_active == True 
            ).all()

        for item in shop_bonuses:
            desc_bonus = f"+{item.bonus_value}"
            
            if desc_bonus.endswith('.0'):
                desc_bonus = desc_bonus[:-2]

            if '_PCT' in item.bonus_type:
                desc_bonus += "%"
            
            # Formatação amigável
            if item.bonus_type == 'QUIZ_BONUS_PCT': desc_bonus += " em Quizzes"
            elif item.bonus_type == 'PATROL_BONUS_PCT': desc_bonus += " em Patrulhas"
            elif item.bonus_type == 'CODEGAME_BONUS_PCT': desc_bonus += " em Minigames"
            elif item.bonus_type == 'STREAK_BONUS_PCT': desc_bonus += " na Ofensiva"
            
            active_perks_list.append(f"<strong class='text-info'><i class='bi bi-cart4'></i> {item.name}:</strong> {desc_bonus}")
            
    except Exception as e:
        print(f"Erro ao buscar bônus de upgrade: {e}")

    # --- MONTAGEM FINAL DO HTML ---
    if active_perks_list:
        active_perks_html = "<ul class='mb-0 ps-3'><li>" + "</li><li>".join(active_perks_list) + "</li></ul>"
    else:
        active_perks_html = "<p class='mb-0'>Nenhum bônus ativo no momento.</p>"


    historico = perfil.historico_acoes.order_by(desc(HistoricoAcao.data_evento)).limit(50)

    numero_conquistas = len(insignias_ganhas)

    nivel_atual = perfil.nivel 
    proximo_nivel = None
    progresso_percentual = 0
    if nivel_atual and perfil.specialization_id:
        proximo_nivel = NivelSeguranca.query.filter(
            NivelSeguranca.specialization_id == perfil.specialization_id, 
            NivelSeguranca.level_number > nivel_atual.level_number 
        ).order_by(NivelSeguranca.level_number.asc()).first() 
        if proximo_nivel:
            score_para_o_nivel = proximo_nivel.score_minimo - nivel_atual.score_minimo
            score_atual_no_nivel = (perfil.score_atual or 0) - nivel_atual.score_minimo
            progresso_percentual = max(0, min(100, int((score_atual_no_nivel / score_para_o_nivel) * 100))) if score_para_o_nivel > 0 else 100
        else: # Já está no nível máximo
            progresso_percentual = 100
    elif not perfil.specialization_id:
        progresso_percentual = 0 # Sem caminho, sem progresso
        nivel_atual = None 

    todos_os_perfis = Guardians.query.order_by(Guardians.score_atual.desc()).with_entities(Guardians.id).all()
    ranking_atual = "N/A"
    try:
        ranking_atual = [p.id for p in todos_os_perfis].index(perfil.id) + 1
    except ValueError:
        pass 

    # --- LÓGICA DE INVENTÁRIO (LOJA) ---
    # Busca compras que NÃO expiraram ainda (ou que são permanentes)
    active_purchases = GuardianPurchase.query.options(
        joinedload(GuardianPurchase.item)
    ).filter(
        GuardianPurchase.guardian_id == perfil.id,
        (GuardianPurchase.expires_at == None) | (GuardianPurchase.expires_at > datetime.utcnow())
    ).all()

    # Agrupamento (Stacking) estilo RPG:
    # Transforma uma lista de 5 linhas de compra em: {'id_item': {dados_item, quantidade: 5}}
    inventory_bag = {}
    
    for purchase in active_purchases:
        item = purchase.item
        if item.id not in inventory_bag:
            
            # Formatação amigável do Bônus para o Card
            bonus_display = "Item Raro"
            if item.bonus_value:
                val = int(item.bonus_value) if item.bonus_value.is_integer() else item.bonus_value
                if 'PCT' in (item.bonus_type or ''):
                    bonus_display = f"+{val}% Bônus"
                else:
                    bonus_display = f"+{val} Pontos"
            elif item.category == 'Cosméticos':
                bonus_display = "Visual"
            elif item.category == 'Consumíveis':
                bonus_display = "Uso Único"

            inventory_bag[item.id] = {
                'name': item.name,
                'icon': item.image_path or 'bi-box-seam', # Fallback
                'category': item.category,
                'bonus_display': bonus_display,
                'description': item.description,
                'count': 0
            }
        
        inventory_bag[item.id]['count'] += 1

    # --- LÓGICA DE COOLDOWN DO CAMINHO (NOVA) ---
    spec_is_locked = False
    spec_days_remaining = 0
    COOLDOWN_DAYS = 14
    
    if perfil.last_spec_change_at:
        # Use datetime.utcnow() ou datetime.now() conforme seu padrão de banco
        time_since_change = datetime.utcnow() - perfil.last_spec_change_at
        if time_since_change < timedelta(days=COOLDOWN_DAYS):
            spec_is_locked = True
            spec_days_remaining = COOLDOWN_DAYS - time_since_change.days

    # --- LÓGICA DE CONTAGEM DE MINIGAMES ---
    termo_count = TermoAttempt.query.filter_by(guardian_id=perfil.id, is_won=True).count()
    password_count = PasswordAttempt.query.filter_by(guardian_id=perfil.id, is_won=True).count()
    anagram_count = AnagramAttempt.query.filter(AnagramAttempt.guardian_id == perfil.id,AnagramAttempt.completed_at.isnot(None)).count()
    minigames_count = termo_count + password_count + anagram_count

    quizzes_respondidos_count = QuizAttempt.query.filter_by(guardian_id=perfil.id).count()
    patrols_completed_count = HistoricoAcao.query.filter(
         HistoricoAcao.guardian_id == perfil.id,
         HistoricoAcao.descricao.like('Realizou Patrulha Diária:%')
     ).count()
    
    patrol_completed_today = (perfil.last_patrol_date == date.today())
    quizzes_needed_for_token = get_global_setting('QUIZZES_FOR_TOKEN', default=5)
    completed_perfect_quizzes = perfil.perfect_quiz_cumulative_count or 0
    quizzes_remaining_for_token = quizzes_needed_for_token - (completed_perfect_quizzes % quizzes_needed_for_token) if quizzes_needed_for_token > 0 else 0
    minigames_needed_for_token = get_global_setting('MINIGAMES_FOR_TOKEN', default=5, setting_type=int)
    completed_perfect_minigames = perfil.perfect_minigame_cumulative_count or 0
    minigames_remaining = minigames_needed_for_token - (completed_perfect_minigames % minigames_needed_for_token) if minigames_needed_for_token > 0 else 0

    quest_set = None
    active_missions = []
    
    # SÓ executa se for o perfil do próprio usuário E o guardião foi encontrado
    if is_own_profile and logged_in_guardian:
        try:
            quest_data = get_or_create_active_quest_set(logged_in_guardian) 
            quest_set = quest_data.get('set')
            active_missions = quest_data.get('missions') # Esta é uma lista

            if quest_set:
                total_count = len(active_missions)
                completed_count = sum(1 for m in active_missions if m.is_completed)
                
                quest_set.total_missions_count = total_count
                quest_set.completed_missions_count = completed_count
                
                for m in active_missions:
                    m.description_display = m.title_generated 

        except Exception as e:
            print(f"Erro ao buscar/criar missões semanais: {e}")
            flash("Não foi possível carregar suas missões semanais.", "danger")

    return render_template(
        'guardians/page_meu_perfil.html',
        perfil=perfil,
        is_own_profile=is_own_profile,
        historico=historico,
        categorized_achievements_list=categorized_achievements_list,
        nivel_atual=nivel_atual,
        proximo_nivel=proximo_nivel,
        progresso_percentual=progresso_percentual,
        inventory_bag=inventory_bag,
        ranking_atual=ranking_atual,
        numero_conquistas=numero_conquistas,
        quizzes_respondidos_count=quizzes_respondidos_count,
        minigames_count=minigames_count,
        quizzes_needed_for_token=quizzes_needed_for_token,
        minigames_needed_for_token=minigames_needed_for_token,
        patrol_completed_today=patrol_completed_today,
        patrols_completed_count=patrols_completed_count,
        quizzes_remaining=quizzes_remaining_for_token,
        effective_streak_percent=effective_streak_percent,
        week_days_data=week_days_data,
        active_perks_html=active_perks_html,
        quest_set=quest_set,
        active_missions=active_missions,
        spec_is_locked=spec_is_locked,       
        spec_days_remaining=spec_days_remaining,
        minigames_remaining=minigames_remaining
    )


##ROTA PRA EDITAR PERFIL
@guardians_bp.route('/meu-perfil/editar', methods=['GET', 'POST'])
@login_required
def edit_profile():
    logged_in_user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if not guardian:
        flash("Perfil de Guardião não pôde ser carregado para edição.", "danger")
        return redirect(url_for('guardians_bp.meu_perfil'))

    minhas_insignias = GuardianInsignia.query.filter_by(
        guardian_id=guardian.id
    ).options(
        joinedload(GuardianInsignia.insignia)
    ).all()
    available_colors = {
        'Padrão (Branco)': None, 'Dourado': '#FFD700', 'Vermelho': '#BB2D3B', 'Azul Escuro': '#006EC7', 'Cinza': '#C0C0C0',
        'Bronze': '#CD7F32', 'Azul': '#00BFFF', 'Verde': '#39FF14',
        'Magenta': '#FF00FF', 
    }

    if request.method == 'POST':
        
        # 1. Salva 
        guardian.nickname = request.form.get('nickname')
        guardian.is_anonymous = 'is_anonymous' in request.form
        guardian.opt_in_real_name_ranking = 'opt_in_real_name_ranking' in request.form
        
        featured_id = request.form.get('featured_insignia_id')
        guardian.featured_insignia_id = int(featured_id) if featured_id else None
        
        selected_color = request.form.get('name_color')
        if selected_color in available_colors.values():
            guardian.name_color = selected_color if selected_color else None
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('guardians_bp.meu_perfil'))

    return render_template('guardians/page_edit_profile.html', 
                           guardian=guardian,
                           perfil=guardian,
                           minhas_insignias=minhas_insignias,
                           available_colors=available_colors)
    
=======

>>>>>>> origin/guardians
##ROTA DA PAGINA DE RANKINGS
@guardians_bp.route('/rankings')
@login_required 
def rankings():
    
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    current_guardian_id = guardian.id if guardian else -1

    ranking_global = Guardians.query.order_by(desc(Guardians.score_atual)).all()

    ranking_streak = Guardians.query.order_by(
        Guardians.current_streak.is_(None), 
        desc(Guardians.current_streak)
    ).all()

    active_season = GameSeason.query.filter_by(is_active=True).first()
    assistant_payload = get_assistant_data(guardian, 'rankings')

    active_season = GameSeason.query.filter_by(is_active=True).first()

    ranking_departamento = db.session.query(
        Guardians.departamento_nome, 
        func.sum(Guardians.score_atual).label('score_total')
    ).group_by(Guardians.departamento_nome).order_by(desc('score_total')).all()

    return render_template('guardians/page_rankings.html', 
                           ranking_global=ranking_global,
                           ranking_streak=ranking_streak,
                           ranking_departamento=ranking_departamento,
                           current_user_id=current_guardian_id,
<<<<<<< HEAD
                           active_season=active_season
=======
                           active_season=active_season,
                           assistant_data=assistant_payload
>>>>>>> origin/guardians
                           )

##ROTA DA PAGINA DE REGRAS
@guardians_bp.route('/regras-do-programa')
@login_required
def sobre_o_programa():
    # Dicionário para guardar as conquistas categorizadas
    categorized_achievements = {
        "Conquistas Baseadas em Score": [],
        "Conquistas Baseadas em Nível": [],
        "Conquistas por Quantidade de Quizzes": [],
        "Conquistas por Acerto em Quizzes": [],
        "Conquistas por Dias de Vigilante (Streak)": [],
        "Conquistas por Patrulhas Diárias": [],
        "Conquistas por Campanhas de Phishing": [],
        "Conquistas de Ranking (Fim de Temporada)": [],
        "Conquistas Manuais": []
    }
    
    # Busca todas as insígnias
    todas_as_insignias = Insignia.query.all()

    # Organiza cada insígnia na sua respectiva categoria
    for insignia in todas_as_insignias:
        code = insignia.achievement_code
        if code.startswith('SCORE_'):
            categorized_achievements["Conquistas Baseadas em Score"].append(insignia)
        elif code.startswith('LEVEL_'):
            categorized_achievements["Conquistas Baseadas em Nível"].append(insignia)
        elif code.startswith('QUIZ_COUNT_'):
            categorized_achievements["Conquistas por Quantidade de Quizzes"].append(insignia)
        elif code.startswith('QUIZ_STREAK_') or code.startswith('QUIZ_HARDCORE_'):
            categorized_achievements["Conquistas por Acerto em Quizzes"].append(insignia)
        elif code.startswith('STREAK_'):
            categorized_achievements["Conquistas por Dias de Vigilante (Streak)"].append(insignia)
        elif code.startswith('PATROL_COUNT_'):
            categorized_achievements["Conquistas por Patrulhas Diárias"].append(insignia)
        elif code.startswith('PHISHING_'):
            categorized_achievements["Conquistas por Campanhas de Phishing"].append(insignia)
        elif code in ['TOP_1', 'TOP_3', 'DEPARTMENT_WIN']: # Exemplo de códigos
            categorized_achievements["Conquistas de Ranking (Fim de Temporada)"].append(insignia)
        else: # Se não se encaixar em nenhuma regra automática, é manual
            categorized_achievements["Conquistas Manuais"].append(insignia)
            
    for key in categorized_achievements:
        categorized_achievements[key].sort(key=get_achievement_sort_key)
        
    eventos = EventoPontuacao.query.order_by(EventoPontuacao.nome).all()
    niveis = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo.asc()).all()

    return render_template(
        'guardians/page_regras.html', 
        categorized_achievements=categorized_achievements,
        eventos=eventos,     
        niveis=niveis        
    )
    

##ROTAS DA CENTRAL DE MISSÕES
def calculate_expiry_info(item):
    """
    Calcula a data de expiração e o texto para um item (Quiz, Termo, Anagrama).
    Retorna (expiry_datetime, expiry_text).
    """
    now = datetime.now(timezone.utc) # Usa UTC para comparação
    
    # Converte activation_date (Date) para datetime (DateTime) no início do dia
    start_datetime_utc = datetime.combine(item.activation_date, datetime.min.time(), tzinfo=timezone.utc)
    
    # Calcula a data/hora exata de expiração
    expiry_datetime_utc = start_datetime_utc + timedelta(days=item.duration_days)

    if now >= expiry_datetime_utc:
        # Já expirou
        return (expiry_datetime_utc, "Expirado")

    time_left = expiry_datetime_utc - now
    days_left = time_left.days
    hours_left = time_left.seconds // 3600

    expiry_text = "Expira em breve!"
    if days_left >= 2:
        expiry_text = f"Expira em {days_left} dias"
    elif days_left == 1:
        expiry_text = "Expira em 1 dia"
    elif hours_left >= 1:
        expiry_text = f"Expira em {hours_left} horas"
    
    return (expiry_datetime_utc, expiry_text)

@guardians_bp.route('/salão-de-jogos')
@login_required
def central():
    """
    Busca TODAS as atividades disponíveis (Quizzes, Termo, Anagrama)
    que o usuário ainda não completou e que estão dentro do período de ativação.
    """
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    logged_in_user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if not guardian:
        flash("Perfil de Guardião não encontrado.", "warning")
        return redirect(url_for("home_bp.render_home"))

    all_activities = []

    attempted_quiz_ids = db.session.query(QuizAttempt.quiz_id).filter(QuizAttempt.guardian_id == guardian.id)
    
    available_quizzes = Quiz.query.filter(
        Quiz.is_active == True,
        Quiz.activation_date <= today, 
        not_(Quiz.id.in_(attempted_quiz_ids)) 
    ).order_by(Quiz.created_at.desc()).all()

    for quiz in available_quizzes:
        expiry_datetime, expiry_text = calculate_expiry_info(quiz)
        
        if now_utc < expiry_datetime:
            all_activities.append({
                'type': 'quiz',
                'item': quiz,
                'title': quiz.title,
                'description': quiz.description,
                'expiry_text': expiry_text,
                'expiry_iso': expiry_datetime.isoformat(), 
                'created_at': quiz.created_at 
            })

    attempted_termo_ids = db.session.query(TermoAttempt.game_id).filter(TermoAttempt.guardian_id == guardian.id)
    
    available_termos = TermoGame.query.filter(
        TermoGame.is_active == True,
        TermoGame.activation_date <= today, 
        not_(TermoGame.id.in_(attempted_termo_ids))
    ).order_by(TermoGame.created_at.desc()).all()

    for game in available_termos:
        expiry_datetime, expiry_text = calculate_expiry_info(game)
        
        if now_utc < expiry_datetime:
            all_activities.append({
                'type': 'termo',
                'item': game,
                'title': f"Código #{game.id}: {len(game.correct_word)} letras",
                'description': f"Adivinhe a palavra em {game.max_attempts} tentativas.",
                'expiry_text': expiry_text,
                'expiry_iso': expiry_datetime.isoformat(),
                'created_at': game.created_at
            })

    attempted_anagram_ids = db.session.query(AnagramAttempt.game_id).filter(AnagramAttempt.guardian_id == guardian.id)
    
    available_anagrams = AnagramGame.query.filter(
        AnagramGame.is_active == True,
        AnagramGame.activation_date <= today, 
        not_(AnagramGame.id.in_(attempted_anagram_ids))
    ).order_by(AnagramGame.created_at.desc()).all()

    for game in available_anagrams:
        expiry_datetime, expiry_text = calculate_expiry_info(game)

        if now_utc < expiry_datetime:
            all_activities.append({
                'type': 'anagram',
                'item': game,
                'title': game.title,
                'description': game.description or f"Desembaralhe {len(game.words)} palavras.",
                'expiry_text': expiry_text,
                'expiry_iso': expiry_datetime.isoformat(),
                'created_at': game.created_at
            })

    password_config = PasswordGameConfig.query.first()

    if password_config and password_config.is_active:
        today_weekday = str(now_utc.weekday())
        allowed_days = password_config.active_days.split(',') if password_config.active_days else []

        if today_weekday not in allowed_days:
            password_config = None
        
        else:
            has_completed_today = PasswordAttempt.query.filter(
                PasswordAttempt.guardian_id == guardian.id,
                PasswordAttempt.completed_at >= datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            ).first()

            if has_completed_today:
                password_config = None

    else:
        password_config = None    
    
    all_activities.sort(key=lambda x: x['created_at'], reverse=True)
<<<<<<< HEAD
=======
    assistant_payload = get_assistant_data(guardian, 'central')
>>>>>>> origin/guardians

    return render_template(
        'guardians/page_central.html', 
        available_activities=all_activities,
<<<<<<< HEAD
        password_config=password_config
=======
        password_config=password_config,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

##ROTAS DE QUIZZES
@guardians_bp.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if not guardian:
        abort(404)

    attempt = QuizAttempt.query.filter_by(
        guardian_id=guardian.id, 
        quiz_id=quiz_id
    ).order_by(QuizAttempt.started_at.desc()).first_or_404()

    if attempt.completed_at:
        flash("Este quiz já foi finalizado.", "info")
        return redirect(url_for('guardians_bp.central'))

    remaining_time = 0

<<<<<<< HEAD

=======
>>>>>>> origin/guardians
    if quiz.time_limit_seconds and quiz.time_limit_seconds > 0:
        
        start_time = attempt.started_at

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
            
        now_time = datetime.now(timezone.utc)
        ts_start = start_time.timestamp()
        ts_now = now_time.timestamp()
<<<<<<< HEAD
        
        elapsed_seconds = ts_now - ts_start
        raw_remaining = quiz.time_limit_seconds - elapsed_seconds
        remaining_time = int(max(0, raw_remaining))
=======
        elapsed_seconds = ts_now - ts_start
        raw_remaining = quiz.time_limit_seconds - elapsed_seconds
        remaining_time = int(max(0, raw_remaining))
        assistant_payload = get_assistant_data(guardian, 'play_quiz')
>>>>>>> origin/guardians

    return render_template(
        'guardians/play_minigame_quiz.html', 
        quiz=quiz, 
        remaining_time=remaining_time,
        assistant_data=assistant_payload
    )

<<<<<<< HEAD
    return render_template(
        'guardians/play_minigame_quiz.html', 
        quiz=quiz, 
        remaining_time=remaining_time
    )

=======
>>>>>>> origin/guardians
# Esta rota corrige o erro 'BuildError' e permite o uso no Terminal/Cards
@guardians_bp.route('/quiz/start-link/<int:quiz_id>', methods=['GET'])
@login_required
def start_quiz_get_method(quiz_id):
    """
    Inicia um quiz via requisição GET.
    Lógica: Cria/Retoma a tentativa e REDIRECIONA para a sala de jogo.
    """
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not guardian:
        flash("Guardião não encontrado.", "danger")
        return redirect(url_for('guardians_bp.central'))

    if not quiz.is_active:
        flash("Este protocolo (Quiz) está desativado ou expirado.", "warning")
        return redirect(url_for('guardians_bp.central'))

    existing_attempt = QuizAttempt.query.filter_by(
        guardian_id=guardian.id, 
        quiz_id=quiz.id, 
        completed_at=None
    ).first()

    if existing_attempt:
        return redirect(url_for('guardians_bp.take_quiz', quiz_id=quiz.id))

    # 3. CRIA NOVA TENTATIVA
    new_attempt = QuizAttempt(
        guardian_id=guardian.id,
        quiz_id=quiz.id,
        started_at=datetime.now(timezone.utc),
        score=0
    )
    db.session.add(new_attempt)
    db.session.commit()

    return redirect(url_for('guardians_bp.take_quiz', quiz_id=quiz.id))

@guardians_bp.route('/quiz/start/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    """
    Cria uma nova tentativa de quiz com um timestamp de início em UTC.
    """
    guardian = Guardians.query.filter_by(user_id=SessionManager.get("user_id")).first()
    if not guardian:
        abort(404)

    existing_attempt = QuizAttempt.query.filter_by(guardian_id=guardian.id, quiz_id=quiz_id).first()
    if existing_attempt:
        flash("Você já respondeu este quiz.", "warning")
        return redirect(url_for('guardians_bp.central'))
    
    new_attempt = QuizAttempt(
        guardian_id=guardian.id, 
        quiz_id=quiz_id, 
        score=0,
        started_at=datetime.now(timezone.utc) # Horário universal
    )
    db.session.add(new_attempt)
    db.session.commit()
    
    return redirect(url_for('guardians_bp.take_quiz', quiz_id=quiz_id))
    
@guardians_bp.route('/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    """
    Recebe as respostas, calcula a pontuação usando a lógica centralizada,
    salva o resultado e redireciona. (Versão Refatorada)
    """
    try:
        quiz_id = request.form.get('quiz_id')
        quiz = Quiz.query.get(quiz_id)
        
        logged_in_user_id = SessionManager.get("user_id")
        guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()
        
        if not guardian:
            flash("Perfil de Guardião não encontrado.", "danger")
            return redirect(url_for('guardians_bp.central'))
        
        attempt = QuizAttempt.query.filter_by(guardian_id=guardian.id, quiz_id=quiz_id).first()
        if not attempt:
            flash("Tentativa de quiz não encontrada. Por favor, comece novamente.", "danger")
            return redirect(url_for('guardians_bp.central'))

        # --- Lógica de Abandono / Tempo Esgotado ---
        is_timer_expired = request.form.get('timer_expired') == 'true'
<<<<<<< HEAD
        is_abandoned = request.form.get('abandoned') == 'true'
=======
>>>>>>> origin/guardians
        if request.form.get('timer_expired') == 'true' or request.form.get('abandoned') == 'true':
            message = "Tempo esgotado! Tentativa zerada." if is_timer_expired else "Quiz abandonado! Tentativa zerada."
            attempt.score = 0
            attempt.completed_at = datetime.now(timezone.utc)
            history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=f"Tentativa zerada no quiz '{quiz.title}'.", pontuacao=0)
            db.session.add(history_entry)
            db.session.commit()
            flash(message, 'warning')
            return redirect(url_for('guardians_bp.central'))
        
        # --- Cálculo de Score Base ---
        raw_score_questions = 0
        total_possible_points = 0

        for question in quiz.questions:
            total_possible_points += question.points
            question_key = f'question_{question.id}'
            submitted_option_ids_str = request.form.getlist(question_key)
            submitted_ids = [int(opt_id) for opt_id in submitted_option_ids_str]
            
            for selected_id in submitted_ids:
<<<<<<< HEAD
                # Salva a resposta do usuário
=======
>>>>>>> origin/guardians
                user_answer = UserAnswer(
                    quiz_attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_id=selected_id
                )    
                db.session.add(user_answer)
                
<<<<<<< HEAD
                # Verifica se está correta
=======
>>>>>>> origin/guardians
            correct_options = [opt for opt in question.options if opt.is_correct]
            correct_ids = [opt.id for opt in correct_options]
            if set(submitted_ids) == set(correct_ids):
                raw_score_questions += question.points
            else:
                pass

        # --- 1. CÁLCULO DETALHADO DOS BÔNUS DE BASE ---
        
        # A. Recupera as porcentagens individuais
        spec_pct = get_active_perk_value(guardian, 'QUIZ_BONUS_PCT', default=0)
        shop_pct = _get_shop_bonus(guardian, 'QUIZ_BONUS_PCT')
        insignia_pct = _get_insignia_bonus(guardian, 'QUIZ_BONUS_PCT')

        # B. Calcula os valores absolutos (Pontos)
        val_spec = int(raw_score_questions * (spec_pct / 100.0))
        val_shop = int(raw_score_questions * (shop_pct / 100.0))
        val_insignia = int(raw_score_questions * (insignia_pct / 100.0))

        # C. Define o Score "Base Boosted" (Base + Bônus Passivos)
        base_score_boosted = raw_score_questions + val_spec + val_shop + val_insignia

        # --- 2. CÁLCULO DE PERFORMANCE (Sobre a nova base) ---
        duration_seconds = (datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        
        bonus_context = {
            'raw_score_before_perks': raw_score_questions, 
            'total_possible_points': total_possible_points,
            'duration_seconds': duration_seconds,
            'time_limit_seconds': quiz.time_limit_seconds
        }
        
        performance_bonuses = calculate_performance_bonuses(guardian, 'quiz', base_score_boosted, bonus_context)
        
        time_bonus_points = performance_bonuses['time_bonus']
        perfection_bonus_points = performance_bonuses['perfection_bonus']
        is_perfect_score = performance_bonuses['is_perfect']

        # --- 3. CÁLCULO FINAL (Streak e Globais) ---
        score_acumulado = base_score_boosted + time_bonus_points + perfection_bonus_points
        score_data = calculate_final_score(guardian, score_acumulado, base_score_boosted, perk_code=None)
        final_score = score_data['final_score']
        global_bonuses = score_data['breakdown']

        # --- 3.1 Atualização e Salvamento ---
        guardian.score_atual = (guardian.score_atual or 0) + final_score
<<<<<<< HEAD
        update_user_streak(guardian) 
        quiz_context = {'quiz': quiz, 'is_perfect_score': is_perfect_score}
        level_up, novas_conquistas = atualizar_nivel_usuario(guardian, quiz_context=quiz_context)
=======
        update_user_streak(guardian)
        guardian.stat_quiz_count += 1 
        level_up, novas_conquistas = atualizar_nivel_usuario(guardian)
>>>>>>> origin/guardians

        # --- 4. SALVAMENTO NA TENTATIVA (ATTEMPT) ---
        attempt.completed_at = datetime.now(timezone.utc)
        
        # Salva o Score "Boosted" (Base + Spec + Loja + Insígnia)
        attempt.score = base_score_boosted
        attempt.final_score = int(final_score)
        
        # Salva os componentes individuais para o breakdown
        attempt.time_bonus = int(time_bonus_points)
        attempt.perfection_bonus = int(perfection_bonus_points)
        attempt.shop_bonus = val_shop
        attempt.conquista_bonus = val_insignia
        
        # Bônus Globais (Streak)
        attempt.streak_total_bonus = int(global_bonuses.get('streak_total_bonus', 0))

<<<<<<< HEAD
        # (Futuramente, adicione colunas para 'conquista_bonus' e 'loja_bonus' aqui)
=======
>>>>>>> origin/guardians

        # --- Cria o Histórico ---
        total_bonus_value = final_score - raw_score_questions
        descricao = f"Completou Quiz '{quiz.title}': +{final_score} pts"
        if total_bonus_value > 0:
            descricao += f" (Bônus: +{total_bonus_value})"

        history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=descricao, pontuacao=final_score)
        db.session.add(history_entry)
        
        # --- Feedback (Flash) para o usuário ---
        if level_up and guardian.nivel:
            flash(f"Parabéns! Você subiu para o nível {guardian.nivel.nome}!", 'info')
        for conquista_nome in novas_conquistas:
<<<<<<< HEAD
            flash(f"Nova Conquista Desbloqueada: {conquista_nome}!", "success")
=======
            flash(f"Conquista de Quiz Desbloqueada!", "success")
>>>>>>> origin/guardians
        
        db.session.commit() # Salva tudo

        # --- Gancho das Missões ---
        try:
            update_mission_progress(guardian, MissionCodeEnum.QUIZ_COUNT)
            update_mission_progress(guardian, MissionCodeEnum.QUIZ_SCORE_SUM, amount=attempt.final_score)
            update_mission_progress(guardian, MissionCodeEnum.ANY_CHALLENGE_COUNT)
            if is_perfect_score:
                update_mission_progress(guardian, MissionCodeEnum.QUIZ_PERFECT_COUNT)
                update_mission_progress(guardian, MissionCodeEnum.ANY_PERFECT_COUNT)
            limit_seconds = get_game_setting('SPEED_LIMIT_QUIZ', default_value=60, type_cast=int)
            if duration_seconds <= limit_seconds and final_score > 0:
                update_mission_progress(guardian, MissionCodeEnum.QUIZ_SPEEDRUN)

        except Exception as e:
            print(f"Erro ao atualizar missões de quiz: {e}")

        return redirect(url_for('guardians_bp.quiz_result', quiz_id=quiz.id, from_submit='true'))

    except Exception as e:
        db.session.rollback()
        print(f"ERRO GERAL AO PROCESSAR O QUIZ: {e}")
        traceback.print_exc()
        flash('Ocorreu um erro crítico ao processar seu quiz.', 'danger')
        return redirect(url_for('guardians_bp.central'))

@guardians_bp.route('/quiz/<int:quiz_id>/resultado')
@login_required
def quiz_result(quiz_id):
    """
    Exibe a página de resultados corrigida para lidar com Múltipla Escolha.
    """
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    quiz = Quiz.query.get_or_404(quiz_id)

    attempt = QuizAttempt.query.filter_by(
        guardian_id=guardian.id,
        quiz_id=quiz_id
    ).order_by(QuizAttempt.completed_at.desc()).first()

    if not attempt or not attempt.completed_at:
        flash("Nenhuma tentativa concluída encontrada.", "warning")
        return redirect(url_for('guardians_bp.central'))

    # --- 1. DURAÇÃO ---
    duration_seconds = None
    if attempt.completed_at and attempt.started_at:
        duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()

    # --- 2. CÁLCULO DE ACERTOS (Recálculo para validação visual) ---
    user_answers = UserAnswer.query.filter_by(quiz_attempt_id=attempt.id).all()
    
    user_map = {}
    for ua in user_answers:
        if ua.question_id not in user_map:
            user_map[ua.question_id] = []
        user_map[ua.question_id].append(ua.selected_option_id)
        
    correct_questions_count = 0
    raw_score_recalc = 0
    total_possible_points = 0
    
    for question in quiz.questions:
        total_possible_points += question.points
        user_selected_ids = user_map.get(question.id, [])
        correct_ids = [opt.id for opt in question.options if opt.is_correct]
        
        # Lógica de Conjunto (Set)
        if set(user_selected_ids) == set(correct_ids):
            correct_questions_count += 1
            raw_score_recalc += question.points

    # --- 3. MONTAGEM DE DADOS E BREAKDOWN ---
    total_questions = len(quiz.questions)
    accuracy_percentage = round((correct_questions_count / total_questions * 100)) if total_questions > 0 else 0

    # Recupera valores salvos no banco
    # attempt.score agora é o "Base Boosted" (Base + Spec + Loja + Insígnia)
    score_com_boosts = attempt.score if attempt.score is not None else raw_score_recalc
    
    # Recupera os bônus específicos salvos
    shop_val = attempt.shop_bonus or 0
    insignia_val = attempt.conquista_bonus or 0
    
    # Dedução do Bônus de Caminho (Spec)
    # Spec = Total Boosted - Base Pura - Loja - Insígnia
    spec_bonus_value = score_com_boosts - raw_score_recalc - shop_val - insignia_val
    
    if spec_bonus_value < 0: spec_bonus_value = 0

    is_perfect = (raw_score_recalc == total_possible_points and total_possible_points > 0)

    score_breakdown = [
        {'label': 'Pontos Base (Quiz)', 'value': raw_score_recalc, 'icon': 'bi-lightning-fill', 'is_bonus': False},
        {'label': 'Especialização', 'value': spec_bonus_value, 'icon': 'bi-key-fill', 'is_bonus': True},
        {'label': 'Upgrades', 'value': shop_val, 'icon': 'bi-battery-charging', 'is_bonus': True},
        {'label': 'Conquista', 'value': insignia_val, 'icon': 'bi-trophy-fill', 'is_bonus': True},
        {'label': 'Velocidade', 'value': attempt.time_bonus or 0, 'icon': 'bi-stopwatch', 'is_bonus': True},
        {'label': 'Perfeição', 'value': attempt.perfection_bonus or 0, 'icon': 'bi-check2-square', 'is_bonus': True},
        {'label': 'Ofensiva', 'value': attempt.streak_total_bonus or 0, 'icon': 'bi-fire', 'is_bonus': True},
    ]
    # Filtra zeros
    score_breakdown = [b for b in score_breakdown if b['value'] != 0 or not b['is_bonus']]

<<<<<<< HEAD
=======
    is_victory = accuracy_percentage >= 50
    assist_context = {
        'is_win': is_victory,
        'score': attempt.final_score
    }
    assistant_payload = get_assistant_data(guardian, 'results', context_data=assist_context)

>>>>>>> origin/guardians
    results_data = {
        'game_type': 'quiz',
        'game_title': quiz.title,
        'attempt_id': attempt.id,
        'quiz_id': quiz.id,
        'final_score': attempt.final_score,
        'duration_seconds': round(duration_seconds, 2) if duration_seconds is not None else None,
        'is_winner': True, 
        'is_perfect': is_perfect,
        'score_breakdown': score_breakdown,
        'accuracy_info': {
            'label': 'Perguntas Corretas',
            'correct': correct_questions_count,
            'total': total_questions,
            'percentage': accuracy_percentage
        }
    }

    show_confetti = request.args.get('from_submit') == 'true' and correct_questions_count > 0

    return render_template(
        'guardians/page_resultados_unificado.html', 
        results_data=results_data,
        guardian=guardian,
        attempt=attempt,
<<<<<<< HEAD
        show_confetti=show_confetti
=======
        show_confetti=show_confetti,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

@guardians_bp.route('/quiz/retake/<int:quiz_id>', methods=['POST'])
@login_required
def retake_quiz(quiz_id):
    guardian = Guardians.query.filter_by(user_id=SessionManager.get("user_id")).first()
    
    if guardian and guardian.retake_tokens > 0:
        old_attempt = QuizAttempt.query.filter_by(guardian_id=guardian.id, quiz_id=quiz_id).order_by(QuizAttempt.completed_at.desc()).first()
        
        if old_attempt:
            try:

                score_to_remove = old_attempt.final_score or 0
                quiz_title = old_attempt.quiz.title if old_attempt.quiz else 'Quiz Antigo'
                
                guardian.retake_tokens -= 1
                guardian.score_atual = (guardian.score_atual or 0) - score_to_remove
                
                reversal_desc = f"Token de Retake (Quiz) usado. Pontuação de '{quiz_title}' (-{score_to_remove} pts) estornada."
                reversal_history = HistoricoAcao(
                    guardian_id=guardian.id,
                    descricao=reversal_desc,
                    pontuacao=-score_to_remove 
                )
                db.session.add(reversal_history)
                
                UserAnswer.query.filter_by(quiz_attempt_id=old_attempt.id).delete()
                db.session.delete(old_attempt)
                db.session.add(guardian)
                db.session.commit()
                
                flash(f"Token de Quiz usado! Você tem {guardian.retake_tokens} restantes.", "info")
                return redirect(url_for('guardians_bp.start_quiz', quiz_id=quiz_id))
            
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao usar o token: {e}", "danger")
                return redirect(url_for('guardians_bp.central'))
                
    flash("Você não tem tokens de retake ou a ação é inválida.", "danger")
    return redirect(url_for('guardians_bp.central'))

##PATRULHA DIARIA
@guardians_bp.route('/patrol/start', methods=['POST'])
@login_required
def start_patrol_game():
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()

    if not guardian:
        return jsonify({'status': 'error', 'message': 'Guardião não encontrado'}), 404

    today_str = date.today().isoformat()

    # 1. Verifica no BANCO se já completou (Segurança Principal)
    if guardian.last_patrol_date == date.today():
        # Se já ganhou hoje, limpa a sessão por precaução
        session.pop('patrol_secret', None)
        session.pop('patrol_history', None)
        return jsonify({'status': 'error', 'message': 'Patrulha diária já realizada hoje!'}), 400

    # 2. Verifica na SESSÃO se há um jogo em andamento HOJE
    if session.get('patrol_date') == today_str and session.get('patrol_secret'):
        # JOGO EM ANDAMENTO: Retorna o estado atual (RESUME)
        return jsonify({
            'status': 'resume',
            'message': 'Retomando sessão de patrulha...',
            'history': session.get('patrol_history', []),
            'attempts': session.get('patrol_attempts', 0)
        })

    # 3. NOVO JOGO (Se não houver sessão ativa para hoje)
    secret_code = "".join([str(random.randint(0, 9)) for _ in range(4)])
    
    session['patrol_secret'] = secret_code
    session['patrol_attempts'] = 0
    session['patrol_history'] = [] # Lista vazia para guardar os chutes
    session['patrol_date'] = today_str # Marca o dia de hoje
    

    return jsonify({'status': 'success', 'message': 'Sistema de segurança iniciado.'})


@guardians_bp.route('/patrol/check', methods=['POST'])
@login_required
def check_patrol_guess():
    data = request.get_json()
    guess = data.get('guess', '')

<<<<<<< HEAD
    # Validação básica
=======
>>>>>>> origin/guardians
    if not guess or len(guess) != 4 or not guess.isdigit():
        return jsonify({'status': 'error', 'message': 'Inválido. Digite 4 números.'}), 400

    secret = session.get('patrol_secret')
    if not secret or session.get('patrol_date') != date.today().isoformat():
        return jsonify({'status': 'error', 'message': 'Sessão expirada ou inválida. Reinicie a patrulha.'}), 400

    session['patrol_attempts'] += 1
    attempts_count = session['patrol_attempts']
<<<<<<< HEAD
    
    # --- LÓGICA DO MASTERMIND (CODEBREAKER) ---
    # Feedback: 'correct' (Verde), 'present' (Amarelo), 'absent' (Vermelho)
=======
>>>>>>> origin/guardians
    feedback = ['absent'] * 4
    secret_list = list(secret)
    guess_list = list(guess)
    
<<<<<<< HEAD
    # Passada 1: Verifica posições exatas (Verde)
=======
>>>>>>> origin/guardians
    for i in range(4):
        if guess_list[i] == secret_list[i]:
            current_digit = guess_list[i]
            
<<<<<<< HEAD
            # Verifica se esse número que eu acertei aparece mais de 1x na senha
            if secret.count(current_digit) > 1:
                feedback[i] = 'correct_multi' # Verde Especial (Certo + Repetido)
            else:
                feedback[i] = 'correct'       # Verde Normal (Certo + Único)
=======
            if secret.count(current_digit) > 1:
                feedback[i] = 'correct_multi' 
            else:
                feedback[i] = 'correct'      
>>>>>>> origin/guardians
                
            secret_list[i] = None
            guess_list[i] = None

<<<<<<< HEAD
    # Passada 2: Verifica números certos em posições erradas (Amarelo)
    for i in range(4):
        if guess_list[i] is not None: # Se não foi marcado como exato
=======
    for i in range(4):
        if guess_list[i] is not None: 
>>>>>>> origin/guardians
            current_digit = guess_list[i]
            if current_digit in secret_list:
                frequency_in_secret = secret.count(current_digit)
                if frequency_in_secret > 1:
<<<<<<< HEAD
                    feedback[i] = 'multi'   # É repetido (Azul)
                else:
                    feedback[i] = 'present' # É único (Amarelo)
                
                # Remove a primeira ocorrência para não contar duplicado
=======
                    feedback[i] = 'multi'  
                else:
                    feedback[i] = 'present' 
                
>>>>>>> origin/guardians
                secret_list[secret_list.index(current_digit)] = None


    is_winner = all(f in ['correct', 'correct_multi'] for f in feedback)
    is_game_over = (attempts_count >= 10) and not is_winner
    history_item = {'guess': guess, 'feedback': feedback}
    current_history = session.get('patrol_history', [])
    current_history.append(history_item)
    session['patrol_history'] = current_history

    response_data = {
        'status': 'playing',
        'feedback': feedback,
        'attempts': attempts_count,
        'guess': guess
    }

<<<<<<< HEAD
    # --- CENÁRIO DE VITÓRIA (Aplica os Prêmios) ---
    if is_winner:
        user_id = SessionManager.get("user_id")
        guardian = Guardians.query.filter_by(user_id=user_id).first()
        
        # 1. Base
        base_min_pts = get_global_setting('PATROL_MIN_POINTS', default=1)
        base_max_pts = get_global_setting('PATROL_MAX_POINTS', default=3)
        base_xp = random.randint(base_min_pts, base_max_pts)  
        
        # 2. Spec + Loja
        spec_pct = get_active_perk_value(guardian, 'PATROL_BONUS_PCT', default=0)
        shop_pct = _get_shop_bonus(guardian, 'PATROL_BONUS_PCT')
    
        base_boosted = round(base_xp * (1 + (spec_pct + shop_pct) / 100.0))
        
        # 3. Soma Streak
        score_data = calculate_final_score(guardian, base_boosted, base_boosted, perk_code=None)
        final_score = score_data['final_score']

        # 4. Salvar
        guardian.score_atual = (guardian.score_atual or 0) + final_score
        guardian.last_patrol_date = date.today()
        update_user_streak(guardian)

        # 6. Histórico
        total_bonus = final_score - base_xp
        desc = f"Codebreaker (Patrulha) concluído: +{final_score} pts"
        if total_bonus > 0: desc += f" (Bônus: +{total_bonus})"
        
        db.session.add(HistoricoAcao(guardian_id=guardian.id, descricao=desc, pontuacao=final_score))
        
        # 7. Level Up e Missões
        atualizar_nivel_usuario(guardian)
=======
    if is_winner:
        user_id = SessionManager.get("user_id")
        guardian = Guardians.query.options(
            joinedload(Guardians.featured_associations).joinedload(GuardianFeatured.insignia)
        ).filter_by(user_id=user_id).first()
        
        base_xp_setting = int(get_global_setting('PATROL_EXP_POINTS', default=100))
        safe_attempts = max(1, attempts_count) 
        
        raw_xp_calculated = int(base_xp_setting / safe_attempts)
        
        score_data = calculate_final_score(guardian, raw_xp_calculated, raw_xp_calculated, perk_code='PATROL_BONUS_PCT')
        final_score = score_data['final_score']

        coin_min = int(get_global_setting('PATROL_COIN_MIN', default=1))
        coin_max = int(get_global_setting('PATROL_COIN_MAX', default=3))
        
        base_coins = random.randint(coin_min, coin_max)
        
        coin_bonus_pct = get_total_bonus(guardian, 'GCOIN_BONUS_PCT')
        bonus_coins_val = 0
        if coin_bonus_pct > 0:
            bonus_coins_val = int(base_coins * (coin_bonus_pct / 100.0))
        
        total_coins = base_coins + bonus_coins_val

        guardian.score_atual = (guardian.score_atual or 0) + final_score
        guardian.guardian_coins = (guardian.guardian_coins or 0) + total_coins
        guardian.last_patrol_date = date.today()
        update_user_streak(guardian)

        total_xp_bonus = final_score - raw_xp_calculated
        desc = f"Codebreaker (Patrulha): +{final_score} XP"
        if total_xp_bonus > 0: 
            desc += f" (Bônus XP: +{total_xp_bonus})"
        
        if total_coins > 0:
            desc += f" | +{total_coins} GC"
            if bonus_coins_val > 0:
                desc += f" (Bônus GC: +{bonus_coins_val})"

        db.session.add(HistoricoAcao(guardian_id=guardian.id, descricao=desc, pontuacao=final_score))
        guardian.stat_patrol_count += 1
        _, conquistas_ganhas = atualizar_nivel_usuario(guardian)
        if conquistas_ganhas:
            flash(f"Conquista de Patrulha Desbloqueada!", "success")
        
>>>>>>> origin/guardians
        try:
            update_mission_progress(guardian, MissionCodeEnum.PATROL_COUNT)
            update_mission_progress(guardian, MissionCodeEnum.ANY_CHALLENGE_COUNT)
        except: pass
        
        db.session.commit()
        
<<<<<<< HEAD
        # Limpa a sessão
=======
>>>>>>> origin/guardians
        session.pop('patrol_secret', None)
        session.pop('patrol_attempts', None)
        
        response_data['status'] = 'win'
        response_data['total_score'] = final_score
<<<<<<< HEAD
        response_data['message'] = f"Acesso concedido! Código quebrado. (+{final_score} XP)"

    # --- CENÁRIO DE DERROTA ---
=======
        response_data['total_coins'] = total_coins 
        
        msg_coins = f" e +{total_coins} Moedas" if total_coins > 0 else ""
        response_data['message'] = f"Acesso concedido! Código quebrado em {safe_attempts} tentativa(s). (+{final_score} XP{msg_coins})"

>>>>>>> origin/guardians
    elif is_game_over:
        session.pop('patrol_secret', None)
        session.pop('patrol_history', None)
        response_data['status'] = 'lose'
        response_data['secret'] = secret
        response_data['message'] = "Falha na decriptação. Um novo código será gerado."

    return jsonify(response_data)
    
<<<<<<< HEAD
# == ROTA PARA ESCOLHA DE ESPECIALIZAÇÃO                  ==
@guardians_bp.route('/escolher-caminho', methods=['GET', 'POST'])
@login_required
def choose_specialization():
    user_id = session.get('user_id')
    guardian = Guardians.query.filter_by(user_id=user_id).first()

    # --- LÓGICA DE COOLDOWN (14 DIAS) ---
    COOLDOWN_DAYS = 14
    is_locked = False
    days_remaining = 0
    
    if guardian.last_spec_change_at:
        # Calcula quanto tempo passou desde a última troca
        # Se usar datetime.utcnow() no banco, use aqui também. Se usar local, use datetime.now()
        now = datetime.utcnow() 
        time_since_change = now - guardian.last_spec_change_at
        
        if time_since_change < timedelta(days=COOLDOWN_DAYS):
            is_locked = True
            days_remaining = COOLDOWN_DAYS - time_since_change.days

    if request.method == 'POST':
        # 1. Bloqueio de Segurança no Backend
        if is_locked:
            flash(f"Protocolo em resfriamento. Aguarde {days_remaining} dias para recalibrar seu caminho.", "danger")
            return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

        choice_id = request.form.get('specialization_id')
        if choice_id:
            # Verifica se ele está escolhendo o MESMO caminho que já tem (opcional, mas bom evitar resetar nivel a toa)
            if guardian.specialization_id == int(choice_id):
                 flash('Você já segue este protocolo.', 'info')
                 return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

            # Atualiza Especialização
            guardian.specialization_id = int(choice_id)
            guardian.nivel_id = None 
            
            # --- ATUALIZA A DATA DA TROCA ---
            guardian.last_spec_change_at = datetime.utcnow() 
            
            db.session.flush()
            level_up, _ = atualizar_nivel_usuario(guardian)
            db.session.commit()
            
            chosen_spec = Specialization.query.get(choice_id)
            flash(f'Protocolo {chosen_spec.name} iniciado! Próxima troca disponível em {COOLDOWN_DAYS} dias.', 'success')
            return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))
        

    all_specializations = Specialization.query.options(
        db.joinedload(Specialization.levels),
        db.joinedload(Specialization.perks).joinedload(SpecializationPerkLevel.perk)
    ).order_by(Specialization.id).all()
    
    specs_data_para_template = []
    
    for spec in all_specializations:
        perks_by_level = defaultdict(list)
        for perk_link in spec.perks:
            perks_by_level[perk_link.level].append(perk_link)

        sorted_levels = sorted(spec.levels, key=lambda x: x.level_number)

        spec_info = {
            "id": spec.id,
            "name": spec.name,
            "description": spec.description,
            "spec_code": spec.spec_code.lower(),
            "main_avatar": sorted_levels[0].avatar_url if sorted_levels else 'img/default.png',
            "color_hex": spec.color_hex or '#0dcaf0',
            "levels": []
        }
        
        for nivel in sorted_levels:
            level_info = {
                "level_number": nivel.level_number,
                "level_name": nivel.nome,
                "avatar_url": nivel.avatar_url,
                "score_minimo": nivel.score_minimo,
                "perks": []
            }
            
            for perk_link in perks_by_level[nivel.level_number]:
                perk_info = {
                    "name": perk_link.perk.name,
                    "description": perk_link.perk.description_template.format(value=int(perk_link.bonus_value))
                }
                level_info["perks"].append(perk_info)
                
            spec_info["levels"].append(level_info)
            
        specs_data_para_template.append(spec_info)

    return render_template(
        'guardians/page_choose_specialization.html', 
        specializations_data=specs_data_para_template,
        is_locked=is_locked, 
        days_remaining=days_remaining
    )
=======
>>>>>>> origin/guardians

# == ROTA PARA TERMOGAME                  ==
@guardians_bp.route('/termo/<int:game_id>')
@login_required
def play_termo(game_id):
    game = TermoGame.query.get_or_404(game_id)
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()

    attempt = TermoAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).first()

    if attempt and attempt.completed_at:
        return redirect(url_for('guardians_bp.termo_result', attempt_id=attempt.id))

    if not attempt:
        attempt = TermoAttempt(guardian_id=guardian.id, game_id=game_id, guesses=[])
        db.session.add(attempt)
        db.session.commit() 

    remaining_time = None
    if game.time_limit_seconds:
        start_time = attempt.started_at.replace(tzinfo=timezone.utc)
        now_time = datetime.now(timezone.utc)
        elapsed_seconds = (now_time - start_time).total_seconds()
        remaining_time = game.time_limit_seconds - elapsed_seconds

        if remaining_time <= 0:
            attempt.score = 0
            attempt.base_points = 0
            if not attempt.completed_at:
                attempt.completed_at = now_time
                db.session.commit()
            return redirect(url_for('guardians_bp.termo_result', attempt_id=attempt.id))
<<<<<<< HEAD
            
=======

    assistant_payload = get_assistant_data(guardian, 'play_termo')        
>>>>>>> origin/guardians
    return render_template(
        'guardians/play_minigame_termo.html', 
        game=game,
        remaining_time=remaining_time,
<<<<<<< HEAD
        attempt_id=attempt.id
=======
        attempt_id=attempt.id,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

@guardians_bp.route('/termo/check_guess', methods=['POST'])
@login_required
def check_termo_guess():
    data = request.get_json()
    game_id = data.get('game_id')
    guess = data.get('guess', '').upper()
    timed_out = data.get('timed_out', False)
    abandoned = data.get('abandoned', False)
    
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    game = TermoGame.query.get(game_id)
    correct_word = game.correct_word

    attempt = TermoAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).first()
    if not attempt or attempt.completed_at:
         return jsonify({'status': 'error', 'message': 'Tentativa inválida ou já completada.'}), 400

    if timed_out or abandoned:
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.score = 0
        attempt.base_points = 0
        attempt.final_score = 0
        attempt.time_bonus = 0
        attempt.perfection_bonus = 0
        attempt.streak_total_bonus = 0
        db.session.commit()
        
<<<<<<< HEAD
        # --- GANCHO DA MISSÃO (QUANDO PERDE/ABANDONA) ---
=======
>>>>>>> origin/guardians
        try:
            update_mission_progress(guardian, MissionCodeEnum.MINIGAME_COUNT)
        except Exception as e:
            print(f"Erro ao atualizar missão de minigame (Cód. Aband.): {e}")
            
        return jsonify({
            'status': 'ok', 
            'game_over': True, 
            'is_winner': False,
            'feedback': [],
            'attempt_id': attempt.id
        })

    if len(guess) != len(correct_word):
        return jsonify({'status': 'error', 'message': 'Palavra de tamanho incorreto!'}), 400

    attempt.guesses.append(guess)
    flag_modified(attempt, 'guesses') 

    feedback = []
    correct_word_copy = list(correct_word) 
    guess_copy = list(guess)
    for i in range(len(correct_word)):
        if guess_copy[i] == correct_word_copy[i]:
            feedback.append('correct')
            correct_word_copy[i] = None
            guess_copy[i] = None
        else:
            feedback.append('')
    for i in range(len(correct_word)):
        if guess_copy[i] is not None:
            if guess_copy[i] in correct_word_copy:
                feedback[i] = 'present'
                correct_word_copy[correct_word_copy.index(guess_copy[i])] = None
            else:
                feedback[i] = 'absent'

    is_winner = all(f == 'correct' for f in feedback)
    game_over = False
    
    final_score = 0
    performance_bonuses = {'time_bonus': 0, 'perfection_bonus': 0}
<<<<<<< HEAD
=======
    is_perfect = False
    duration_seconds = 0
    base_points_raw = 0
    val_spec = 0
    val_shop = 0
    val_insignia = 0
    time_bonus = 0
    perfection_bonus = 0
>>>>>>> origin/guardians

    if is_winner:
        game_over = True
        attempt.is_won = True
        num_guesses = len(attempt.guesses)

        # --- 1. CÁLCULO DA BASE (RAW) ---
        max_score = game.points_reward
        base_points_raw = max_score if num_guesses <= 4 else round(max_score * 0.5)

        # --- 2. CÁLCULO DOS MULTIPLICADORES (Itens, Classe, Insígnia) ---
        spec_pct = get_active_perk_value(guardian, 'TERMO_BONUS_PCT', default=0)
        shop_pct = _get_shop_bonus(guardian, 'TERMO_BONUS_PCT')      
        insignia_pct = _get_insignia_bonus(guardian, 'TERMO_BONUS_PCT')

        # B. Calcula os valores absolutos (Pontos) para salvar no banco
        val_spec = int(base_points_raw * (spec_pct / 100.0))      
        val_shop = int(base_points_raw * (shop_pct / 100.0))
        val_insignia = int(base_points_raw * (insignia_pct / 100.0))

        # C. Score Base Boosted (Base + Passivos)
        base_score_boosted = base_points_raw + val_spec + val_shop + val_insignia

        # --- 3. CÁLCULO DE PERFORMANCE ---
        duration_seconds = (datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()
<<<<<<< HEAD
        is_perfect = (num_guesses <= 2)
=======
        is_perfect = (num_guesses <= 4)
>>>>>>> origin/guardians

        bonus_context = {
            'raw_score_before_perks': base_points_raw,
            'total_possible_points': max_score,
            'duration_seconds': duration_seconds,
            'time_limit_seconds': game.time_limit_seconds,
<<<<<<< HEAD
            'is_perfect': is_perfect
=======
            'is_perfect': is_perfect,
            'minigame_type': 'termo'
>>>>>>> origin/guardians
        }

        performance_bonuses = calculate_performance_bonuses(guardian, 'minigame', base_score_boosted, bonus_context)
        time_bonus = performance_bonuses['time_bonus']
        perfection_bonus = performance_bonuses['perfection_bonus']

        # --- 4. CÁLCULO FINAL (STREAK) ---
        score_acumulado = base_score_boosted + time_bonus + perfection_bonus
        score_data = calculate_final_score(guardian, score_acumulado, base_score_boosted, perk_code=None)
        
        final_score = score_data['final_score']
        global_bonuses = score_data['breakdown']

        # --- 5. ATUALIZAÇÕES DE ESTADO ---
        guardian.score_atual = (guardian.score_atual or 0) + final_score
        update_user_streak(guardian)

        total_bonus_value = final_score - base_points_raw
        descricao = f"Acertou Código '******' ({num_guesses}/{game.max_attempts}): +{final_score} XP"
        if total_bonus_value > 0:
            descricao += f" (Bônus Total: +{total_bonus_value})"

        history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=descricao, pontuacao=final_score)
        db.session.add(history_entry)
        guardian.stat_minigame_count += 1
        _, conquistas_ganhas = atualizar_nivel_usuario(guardian)
        if conquistas_ganhas:
            flash(f"Conquista de Minigame Desbloqueada!", "success")

<<<<<<< HEAD
        atualizar_nivel_usuario(guardian)

    elif len(attempt.guesses) >= game.max_attempts:
        game_over = True 
        final_score = 0

    if game_over:
        attempt.completed_at = datetime.now(timezone.utc)
        
=======
    elif len(attempt.guesses) >= game.max_attempts:
        game_over = True 
        final_score = 0
        duration_seconds = (datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()

    if game_over:
        attempt.completed_at = datetime.now(timezone.utc)
>>>>>>> origin/guardians
        attempt.score = base_score_boosted if is_winner else 0
        attempt.final_score = final_score
        attempt.base_points = base_points_raw if is_winner else 0 
        attempt.streak_spec_bonus = val_spec if is_winner else 0 
        attempt.shop_bonus = val_shop if is_winner else 0
        attempt.conquista_bonus = val_insignia if is_winner else 0
        attempt.time_bonus = int(time_bonus) if is_winner else 0
        attempt.perfection_bonus = int(perfection_bonus) if is_winner else 0
        attempt.streak_total_bonus = int(global_bonuses.get('streak_total_bonus', 0)) if is_winner else 0

        db.session.add(attempt)
        db.session.commit()

        try:
            update_mission_progress(guardian, MissionCodeEnum.MINIGAME_COUNT)
            update_mission_progress(guardian, MissionCodeEnum.ANY_CHALLENGE_COUNT)
            if is_perfect: 
                update_mission_progress(guardian, MissionCodeEnum.ANY_PERFECT_COUNT)
            limit_seconds = get_game_setting('SPEED_LIMIT_TERMO', default_value=180, type_cast=int)
            if duration_seconds <= limit_seconds:
                update_mission_progress(guardian, MissionCodeEnum.MINIGAME_SPEEDRUN)

        except Exception as e:
            print(f"Erro ao atualizar missão de minigame (Código): {e}")

    else:
        db.session.commit()

    return jsonify({
        'status': 'ok',
        'feedback': feedback,
        'is_winner': is_winner,
        'game_over': game_over,
        'attempt_id': attempt.id
    })

@guardians_bp.route('/termo/resultado/<int:attempt_id>')
@login_required
def termo_result(attempt_id):
    attempt = TermoAttempt.query.get_or_404(attempt_id)
    user_id = SessionManager.get("user_id")
    guardian = attempt.guardian

    if guardian.user_id != user_id:
        return redirect(url_for('guardians_bp.central'))

    duration_seconds = None
    if attempt.completed_at and attempt.started_at:
        duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()

    num_guesses = len(attempt.guesses) if attempt.guesses else 0
    max_attempts = attempt.game.max_attempts

<<<<<<< HEAD

=======
>>>>>>> origin/guardians
    max_score = attempt.game.points_reward
    base_points_display = 0
    if attempt.is_won:
        if hasattr(attempt, 'base_points') and attempt.base_points > 0:
             base_points_display = attempt.base_points
        else:
             base_points_display = max_score if num_guesses <= 4 else round(max_score * 0.5)

    spec_val = attempt.streak_spec_bonus or 0      
    shop_val = attempt.shop_bonus or 0
    conquista_val = attempt.conquista_bonus or 0
    streak_val = attempt.streak_total_bonus or 0
    time_val = attempt.time_bonus or 0
    perfection_val = attempt.perfection_bonus or 0

    score_breakdown = [
        {'label': 'Pontos Base', 'value': base_points_display, 'icon': 'bi-lightning-fill', 'is_bonus': False},
        {'label': 'Especialização', 'value': spec_val, 'icon': 'bi-key-fill', 'is_bonus': True},
        {'label': 'Upgrades', 'value': shop_val, 'icon': 'bi-battery-charging', 'is_bonus': True},
        {'label': 'Conquista', 'value': conquista_val, 'icon': 'bi-trophy-fill', 'is_bonus': True},
        {'label': 'Bônus Velocidade', 'value': time_val, 'icon': 'bi-clock', 'is_bonus': True},
        {'label': 'Bônus Perfeição', 'value': perfection_val, 'icon': 'bi-check2-square', 'is_bonus': True},
        {'label': 'Ofensiva', 'value': streak_val, 'icon': 'bi-fire', 'is_bonus': True}
    ]
    
    score_breakdown = [b for b in score_breakdown if b['value'] != 0 or not b['is_bonus']]

<<<<<<< HEAD
=======
    #LOGICA DO ASSISTENTE
    assist_context = {
        'is_win': attempt.is_won, 
        'score': attempt.final_score
    }
    assistant_payload = get_assistant_data(guardian, 'results', context_data=assist_context)
    #
>>>>>>> origin/guardians
    results_data = {
        'game_type': 'termo',
        'game_title': f"Código: *****", 
        'attempt_id': attempt.id,
        'source_id': attempt.game_id,
        'final_score': attempt.final_score,
        'duration_seconds': round(duration_seconds, 2) if duration_seconds is not None else None,
        'is_winner': attempt.is_won,
<<<<<<< HEAD
        'is_perfect': (attempt.is_won and num_guesses <= 2),
=======
        'is_perfect': (attempt.is_won and num_guesses <= 4),
>>>>>>> origin/guardians
        'score_breakdown': score_breakdown,
        'accuracy_info': {
            'label': 'Tentativas',
            'correct': num_guesses if attempt.is_won else max_attempts,
            'total': max_attempts,
            'percentage': round(100 - ( (num_guesses-1) / max_attempts * 100)) if attempt.is_won and max_attempts > 0 else 0
        }
    }

    show_confetti = request.args.get('from_submit') == 'true' and attempt.is_won

    return render_template(
        'guardians/page_resultados_unificado.html',
        results_data=results_data,
        guardian=guardian,
        attempt=attempt,
<<<<<<< HEAD
        show_confetti=show_confetti
=======
        show_confetti=show_confetti,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

# == ROTA PARA JOGO DO ANAGRAMA                  ==
@guardians_bp.route('/anagrama/<int:game_id>')
@login_required
def play_anagram(game_id):
    game = AnagramGame.query.get_or_404(game_id)
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    attempt = AnagramAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).first()

    if attempt and attempt.completed_at:
        flash("Você já completou este desafio. Veja seu resultado.", "info")
        return redirect(url_for('guardians_bp.anagram_result', attempt_id=attempt.id))

    if not attempt:
        attempt = AnagramAttempt(guardian_id=guardian.id, game_id=game_id, score=0)
        db.session.add(attempt)
        db.session.commit() 
    
    remaining_time = None
    if game.time_limit_seconds:
        start_time = attempt.started_at.replace(tzinfo=timezone.utc)
        now_time = datetime.now(timezone.utc)
        elapsed_seconds = (now_time - start_time).total_seconds()
        remaining_time = game.time_limit_seconds - elapsed_seconds

        if remaining_time <= 0:
            attempt.score = 0
            if not attempt.completed_at: 
                attempt.completed_at = now_time
                history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=f"Tempo esgotado no Desafio '{game.title}'.", pontuacao=0)
                db.session.add(history_entry)
                db.session.commit()

            flash("O tempo para este desafio esgotou!", "warning")
            return redirect(url_for('guardians_bp.anagram_result', attempt_id=attempt.id))
            
    words_data = []
    for word in game.words:
        word_list = list(word.correct_word)
        random.shuffle(word_list) 
        shuffled_word = "".join(word_list)
        words_data.append({
            'shuffled': shuffled_word,
            'correct': word.correct_word 
        })
        
<<<<<<< HEAD
=======
    assistant_payload = get_assistant_data(guardian, 'play_anagram')    
>>>>>>> origin/guardians
    return render_template(
        'guardians/play_minigame_anagram.html', 
        game=game, 
        words_data=words_data,
<<<<<<< HEAD
        remaining_time=remaining_time 
=======
        remaining_time=remaining_time,
        assistant_data=assistant_payload 
>>>>>>> origin/guardians
    )

@guardians_bp.route('/anagrama/submit', methods=['POST'])
@login_required
def submit_anagram():
    data = request.get_json()
    try:
        game_id = int(data.get('game_id'))
        correct_count = int(data.get('correct_count'))
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Dados de jogo inválidos.'}), 400

    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    game = AnagramGame.query.get(game_id)
    
    if not guardian or not game:
        return jsonify({'status': 'error', 'message': 'Guardião ou Jogo não encontrado.'}), 404
        
    attempt = AnagramAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).first() 
    if not attempt or attempt.completed_at:
        return jsonify({'status': 'error', 'message': 'Tentativa inválida ou já completada.'}), 400

    duration_seconds = (datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()
    
    if game.time_limit_seconds and duration_seconds > game.time_limit_seconds + 2: 
        attempt.score = 0
        attempt.final_score = 0 
        attempt.correct_answers = 0
        attempt.completed_at = datetime.now(timezone.utc)
        db.session.add(attempt)
        db.session.commit()
        
        try:
            update_mission_progress(guardian, MissionCodeEnum.MINIGAME_COUNT)
        except Exception:
            pass
        return jsonify({'status': 'timeout', 'message': 'Tempo esgotado.', 'attempt_id': attempt.id}), 400
    
    # --- 1. CÁLCULO DETALHADO DOS BÔNUS DE BASE ---
    
    raw_score_words = correct_count * game.points_per_word
    total_possible_words = len(game.words)
    is_perfect = (correct_count == total_possible_words and total_possible_words > 0)
    spec_pct = get_active_perk_value(guardian, 'ANAGRAM_BONUS_PCT', default=0)
    shop_pct = _get_shop_bonus(guardian, 'ANAGRAM_BONUS_PCT')    
    insignia_pct = _get_insignia_bonus(guardian, 'ANAGRAM_BONUS_PCT')
    val_spec = int(raw_score_words * (spec_pct / 100.0))
    val_shop = int(raw_score_words * (shop_pct / 100.0))
    val_insignia = int(raw_score_words * (insignia_pct / 100.0))
    base_score_boosted = raw_score_words + val_spec + val_shop + val_insignia

    # --- 2. CÁLCULO DE PERFORMANCE (Sobre a nova base) ---
    bonus_context = {
        'raw_score_before_perks': raw_score_words,
        'total_possible_points': total_possible_words * game.points_per_word,
        'duration_seconds': duration_seconds,
        'time_limit_seconds': game.time_limit_seconds,
<<<<<<< HEAD
        'is_perfect': (correct_count == total_possible_words and total_possible_words > 0)
=======
        'is_perfect': (correct_count == total_possible_words and total_possible_words > 0),
        'minigame_type': 'anagram'
>>>>>>> origin/guardians
    }
    
    performance_bonuses = calculate_performance_bonuses(guardian, 'minigame', base_score_boosted, bonus_context)
    time_bonus = performance_bonuses['time_bonus']
    perfection_bonus = performance_bonuses['perfection_bonus']

    # --- 3. CÁLCULO FINAL (STREAK) ---
    score_acumulado = base_score_boosted + time_bonus + perfection_bonus
    score_data = calculate_final_score(guardian, score_acumulado, base_score_boosted, perk_code=None)
    final_score = score_data['final_score']
    global_bonuses = score_data['breakdown']
    guardian.score_atual = (guardian.score_atual or 0) + final_score
    update_user_streak(guardian)
<<<<<<< HEAD
    atualizar_nivel_usuario(guardian)
=======
    guardian.stat_minigame_count += 1
    _, conquistas_ganhas = atualizar_nivel_usuario(guardian)
    if conquistas_ganhas:
        flash(f"Conquista de Minigame Desbloqueada!", "success")
>>>>>>> origin/guardians

    # --- 4. SALVAMENTO NO BANCO (ATTEMPT) ---
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.correct_answers = correct_count
    attempt.score = base_score_boosted
    attempt.final_score = int(final_score)
    attempt.time_bonus = int(time_bonus)
    attempt.perfection_bonus = int(perfection_bonus)
    attempt.shop_bonus = val_shop
    attempt.conquista_bonus = val_insignia
    attempt.streak_spec_bonus = val_spec 
    attempt.streak_total_bonus = int(global_bonuses.get('streak_total_bonus', 0))
    total_bonus_value = final_score - raw_score_words
    descricao = f"Completou '{game.title}' ({correct_count}/{total_possible_words}): +{final_score} XP"
    if total_bonus_value > 0:
         descricao += f" (Bônus Total: +{total_bonus_value})"

    history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=descricao, pontuacao=final_score)
    db.session.add(history_entry)
    
    db.session.add(guardian)
    db.session.add(attempt)
    db.session.commit()

    try:
        update_mission_progress(guardian, MissionCodeEnum.MINIGAME_COUNT)
        update_mission_progress(guardian, MissionCodeEnum.ANY_CHALLENGE_COUNT)
        if is_perfect:
            update_mission_progress(guardian, MissionCodeEnum.ANY_PERFECT_COUNT)
        limit_seconds = get_game_setting('SPEED_LIMIT_ANAGRAM', default_value=45, type_cast=int)
        if duration_seconds <= limit_seconds and final_score > 0:
            update_mission_progress(guardian, MissionCodeEnum.MINIGAME_SPEEDRUN)

    except Exception:
        print(f"Erro ao atualizar missões (Anagrama): {e}")
        pass

    return jsonify({'status': 'success', 'attempt_id': attempt.id})

@guardians_bp.route('/anagrama/resultado/<int:attempt_id>')
@login_required
def anagram_result(attempt_id):
    attempt = AnagramAttempt.query.get_or_404(attempt_id)
    user_id = SessionManager.get("user_id")
    guardian = attempt.guardian

    if guardian.user_id != user_id:
        return redirect(url_for('guardians_bp.central'))

<<<<<<< HEAD
    # Dados de tempo e precisão
=======
>>>>>>> origin/guardians
    duration_seconds = None
    if attempt.completed_at and attempt.started_at:
        duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()

    total_words = len(attempt.game.words)
    accuracy_percentage = round((attempt.correct_answers / total_words * 100)) if total_words > 0 else 0
    is_perfect = (attempt.correct_answers == total_words and total_words > 0)

    # 1. Base Pura
    base_points_raw = attempt.correct_answers * attempt.game.points_per_word

    # 2. Leitura Direta dos Bônus (Sem cálculos complexos)
<<<<<<< HEAD
    # Usamos getattr/hasattr por segurança, ou acesso direto se tiver certeza da migration
=======
>>>>>>> origin/guardians
    shop_val = attempt.shop_bonus or 0
    conquista_val = attempt.conquista_bonus or 0
    spec_val = attempt.streak_spec_bonus or 0 
    streak_val = attempt.streak_total_bonus or 0
    time_val = attempt.time_bonus or 0
    perfection_val = attempt.perfection_bonus or 0

    score_breakdown = [
        {'label': 'Pontos Base', 'value': base_points_raw, 'icon': 'bi-lightning-fill', 'is_bonus': False},
        {'label': 'Especialização', 'value': spec_val, 'icon': 'bi-key-fill', 'is_bonus': True},
        {'label': 'Upgrades', 'value': shop_val, 'icon': 'bi-battery-charging', 'is_bonus': True},
        {'label': 'Conquista', 'value': conquista_val, 'icon': 'bi-trophy-fill', 'is_bonus': True},        
        {'label': 'Bônus Velocidade', 'value': time_val, 'icon': 'bi-clock', 'is_bonus': True},
        {'label': 'Bônus Perfeição', 'value': perfection_val, 'icon': 'bi-check2-square', 'is_bonus': True},
        {'label': 'Ofensiva', 'value': streak_val, 'icon': 'bi-fire', 'is_bonus': True}
    ]
    
<<<<<<< HEAD
    # Filtra zerados
    score_breakdown = [b for b in score_breakdown if b['value'] != 0 or not b['is_bonus']]

=======
    score_breakdown = [b for b in score_breakdown if b['value'] != 0 or not b['is_bonus']]

    is_victory = accuracy_percentage >= 50
    assist_context = {
        'is_win': is_victory, 
        'score': attempt.final_score
    }
    assistant_payload = get_assistant_data(guardian, 'results', context_data=assist_context)

>>>>>>> origin/guardians
    results_data = {
        'game_type': 'anagrama',
        'game_title': attempt.game.title,
        'attempt_id': attempt.id,
        'source_id': attempt.game_id,
        'final_score': attempt.final_score,
        'duration_seconds': round(duration_seconds, 2) if duration_seconds is not None else None,
        'is_winner': True,
        'is_perfect': is_perfect,
        'score_breakdown': score_breakdown,
        'accuracy_info': {
            'label': 'Palavras Corretas',
            'correct': attempt.correct_answers,
            'total': total_words,
            'percentage': accuracy_percentage
        }
    }

    show_confetti = request.args.get('from_submit') == 'true' and attempt.correct_answers > 0

    return render_template(
        'guardians/page_resultados_unificado.html',
        results_data=results_data,
        guardian=guardian,
        attempt=attempt,
<<<<<<< HEAD
        show_confetti=show_confetti
=======
        show_confetti=show_confetti,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

## --- ROTA PARA PASSWORD GAME
@guardians_bp.route('/password-game/play')
@login_required
def play_password_game():
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if not guardian:
        return redirect(url_for('guardians_bp.central'))

    # 0. Verifica se já existe uma tentativa feita hoje
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    completed_attempt = PasswordAttempt.query.filter(
        PasswordAttempt.guardian_id == guardian.id,
        PasswordAttempt.completed_at >= today_start
    ).first()
    if completed_attempt:
        flash("Você já realizou esta missão hoje.", "info")
        return redirect(url_for('guardians_bp.password_game_result', attempt_id=completed_attempt.id))
    
    # 1. Busca tentativa aberta
    attempt = PasswordAttempt.query.filter_by(
        guardian_id=guardian.id, 
        completed_at=None
    ).order_by(PasswordAttempt.started_at.desc()).first()

    config = get_game_config()
    today_weekday = datetime.now(timezone.utc).weekday()
    allowed_days = config.active_days.split(',') if config.active_days else []
    if str(today_weekday) not in allowed_days:
        flash("Segredo está fechado hoje. Verifique a escala de operações.", "warning")
        return redirect(url_for('guardians_bp.central'))

<<<<<<< HEAD
    # Se não existir, cria
=======
>>>>>>> origin/guardians
    if not attempt:
        rules_ids = generate_rules_sequence()
        attempt = PasswordAttempt(
            guardian_id=guardian.id,
            rules_sequence=json.dumps(rules_ids),
            started_at=datetime.now(timezone.utc),
            score=0
        )
        db.session.add(attempt)
        db.session.commit()
    
    # 2. Recupera Regras
    try:
        rules_ids = json.loads(attempt.rules_sequence)
    except:
        rules_ids = generate_rules_sequence()
        attempt.rules_sequence = json.dumps(rules_ids)
        db.session.commit()

    rules_data = get_rules_details(rules_ids)

    # 3. Lógica do Timer (CORRIGIDA)
    remaining_time = 0
    has_timer = False
    
    if config.time_limit_seconds and config.time_limit_seconds > 0:
        has_timer = True
        start_time = attempt.started_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        
<<<<<<< HEAD
        # --- CORREÇÃO DE USER EXPERIENCE ---
        if elapsed > config.time_limit_seconds:
            attempt.started_at = datetime.now(timezone.utc) # Reseta o início
            db.session.commit()
            elapsed = 0 # Zera o passado
            
        remaining_time = int(max(0, config.time_limit_seconds - elapsed))

=======
        if elapsed > config.time_limit_seconds:
            attempt.started_at = datetime.now(timezone.utc)
            db.session.commit()
            elapsed = 0
            
        remaining_time = int(max(0, config.time_limit_seconds - elapsed))

    assistant_payload = get_assistant_data(guardian, 'play_password')
>>>>>>> origin/guardians
    return render_template('guardians/play_minigame_password.html', 
                           guardian=guardian, 
                           attempt=attempt, 
                           rules=rules_data,
                           remaining_time=remaining_time,
                           has_timer=has_timer,
<<<<<<< HEAD
                           config=config)
=======
                           config=config,
                           assistant_data=assistant_payload)
>>>>>>> origin/guardians

@guardians_bp.route('/password-game/submit/<int:attempt_id>', methods=['POST'])
@login_required
def submit_password_game(attempt_id):
    attempt = PasswordAttempt.query.get_or_404(attempt_id)
    guardian = attempt.guardian
    
    if guardian.user_id != SessionManager.get("user_id"):
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403
        
    if attempt.completed_at:
        return jsonify({'status': 'error', 'message': 'Jogo já finalizado'}), 400

    data = request.get_json()
    password = data.get('password', '')
    config = get_game_config()
    
    # 1. Validação de Tempo (Backend Authority)
    if config.time_limit_seconds:
        start_time = attempt.started_at.replace(tzinfo=timezone.utc)
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        if duration_seconds > (config.time_limit_seconds + 10):
            attempt.completed_at = datetime.now(timezone.utc)
            attempt.is_won = False
            attempt.score = 0
            attempt.final_score = 0 
            db.session.commit()
            
            return jsonify({
                'status': 'timeout', 
                'message': 'Tempo esgotado no servidor!',
                'redirect': url_for('guardians_bp.password_game_result', attempt_id=attempt.id)
            })

    # 2. Validação das Regras
    try:
        rules_ids = json.loads(attempt.rules_sequence)
    except:
        return jsonify({'status': 'error', 'message': 'Erro de dados na tentativa'}), 500

    is_valid, failed_rules = validate_password_backend(password, rules_ids)
    
    if is_valid:
        attempt.is_won = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.input_password = password

        # --- 1. CÁLCULO DA BASE (RAW) ---
        base_points_raw = config.base_reward_points

        # --- 2. CÁLCULO DOS MULTIPLICADORES (Itens, Classe, Insígnia) ---
        spec_pct = get_active_perk_value(guardian, 'PW_BONUS_PCT' , default=0)
        shop_pct = _get_shop_bonus(guardian, 'PW_BONUS_PCT' )      
        insignia_pct = _get_insignia_bonus(guardian, 'PW_BONUS_PCT' )
        val_spec = int(base_points_raw * (spec_pct / 100.0))     
        val_shop = int(base_points_raw * (shop_pct / 100.0))     
        val_insignia = int(base_points_raw * (insignia_pct / 100.0))
        base_score_boosted = base_points_raw + val_spec + val_shop + val_insignia
        
        # --- 3. CÁLCULO DE PERFORMANCE ---
        duration_seconds = (datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        
        is_perfect = True 
        bonus_context = {
            'raw_score_before_perks': base_points_raw,
            'total_possible_points': base_points_raw,
            'duration_seconds': duration_seconds,
            'time_limit_seconds': config.time_limit_seconds,
<<<<<<< HEAD
            'is_perfect': is_perfect 
=======
            'is_perfect': is_perfect,
            'minigame_type': 'password'
>>>>>>> origin/guardians
        }

        performance_bonuses = calculate_performance_bonuses(guardian, 'minigame', base_score_boosted, bonus_context)
        time_bonus = performance_bonuses['time_bonus']
        perfection_bonus = performance_bonuses['perfection_bonus']

        # --- 4. CÁLCULO FINAL (STREAK) ---
        score_acumulado = base_score_boosted + time_bonus + perfection_bonus
        
        score_data = calculate_final_score(guardian, score_acumulado, base_score_boosted, perk_code=None)
        
        final_score = score_data['final_score']
        global_bonuses = score_data['breakdown']
        
        # --- 5. ATUALIZAÇÕES DE ESTADO ---
        guardian.score_atual = (guardian.score_atual or 0) + final_score
        update_user_streak(guardian)
        
        # --- 6. SALVAMENTO (COMMIT) ---
        attempt.base_points = base_points_raw
        attempt.score = base_score_boosted 
        attempt.final_score = final_score
        attempt.spec_bonus = val_spec          
        attempt.shop_bonus = val_shop
        attempt.conquista_bonus = val_insignia
        
        attempt.time_bonus = int(time_bonus)
        attempt.perfection_bonus = int(perfection_bonus)
        attempt.streak_total_bonus = int(global_bonuses.get('streak_total_bonus', 0))
        
        # Histórico
        desc = f"Venceu Segredo: +{final_score} XP"
        total_bonus_val = final_score - base_points_raw
        if total_bonus_val > 0:
            desc += f" (Bônus: +{total_bonus_val})"

        db.session.add(HistoricoAcao(guardian_id=guardian.id, descricao=desc, pontuacao=final_score))
<<<<<<< HEAD
        
        atualizar_nivel_usuario(guardian)
=======
        guardian.stat_minigame_count += 1
        _, conquistas_ganhas = atualizar_nivel_usuario(guardian)
        if conquistas_ganhas:
            flash(f"Conquista de Minigame Desbloqueada!", "success")
>>>>>>> origin/guardians
        
        try: 
            update_mission_progress(guardian, MissionCodeEnum.MINIGAME_COUNT)
            update_mission_progress(guardian, MissionCodeEnum.ANY_CHALLENGE_COUNT)
            if is_perfect:
                update_mission_progress(guardian, MissionCodeEnum.ANY_PERFECT_COUNT)
            limit_seconds = get_game_setting('SPEED_LIMIT_PASSWORD', default_value=60, type_cast=int)
            if duration_seconds <= limit_seconds and final_score > 0:
                update_mission_progress(guardian, MissionCodeEnum.MINIGAME_SPEEDRUN)
        except: 
            pass
        
        db.session.commit()
        
        return jsonify({
            'status': 'win', 
            'redirect': url_for('guardians_bp.password_game_result', attempt_id=attempt.id)
        })
        
    else:
        return jsonify({
            'status': 'invalid', 
            'message': 'A senha não atende aos requisitos.',
            'failed_rules': failed_rules
        })

@guardians_bp.route('/password-game/resultado/<int:attempt_id>')
@login_required
def password_game_result(attempt_id):
    """
    Exibe a página de resultado unificado para o Password Vault.
    """
    attempt = PasswordAttempt.query.get_or_404(attempt_id)
<<<<<<< HEAD
    
    # Segurança
=======
>>>>>>> origin/guardians
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    if attempt.guardian_id != guardian.id:
        flash("Esta tentativa não pertence a você.", "danger")
        return redirect(url_for('guardians_bp.central'))

<<<<<<< HEAD
    # --- Montagem dos Dados ---
=======
>>>>>>> origin/guardians
    duration_seconds = None
    if attempt.completed_at and attempt.started_at:
        duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
        
    # 1. Base Pura
    base_points = attempt.base_points or 0
    
    # 2. Leitura Direta dos Bônus (Zero matemática, leitura pura do DB)
    spec_val = attempt.spec_bonus or 0
    shop_val = attempt.shop_bonus or 0
    conquista_val = attempt.conquista_bonus or 0
    streak_val = attempt.streak_total_bonus or 0
    time_val = attempt.time_bonus or 0
    perfection_val = attempt.perfection_bonus or 0
    
    score_breakdown = [
        {'label': 'Pontos Base', 'value': base_points, 'icon': 'bi-lightning-fill', 'is_bonus': False},
        {'label': 'Especialização', 'value': spec_val, 'icon': 'bi-key-fill', 'is_bonus': True},
        {'label': 'Upgrades', 'value': shop_val, 'icon': 'bi-battery-charging', 'is_bonus': True},
        {'label': 'Conquista', 'value': conquista_val, 'icon': 'bi-trophy-fill', 'is_bonus': True},
        {'label': 'Bônus Velocidade', 'value': time_val, 'icon': 'bi-clock', 'is_bonus': True},
        {'label': 'Bônus Perfeição', 'value': perfection_val, 'icon': 'bi-check2-square', 'is_bonus': True},
        {'label': 'Ofensiva', 'value': streak_val, 'icon': 'bi-fire', 'is_bonus': True}
    ]
    
    # Filtra zeros
    score_breakdown = [b for b in score_breakdown if b['value'] != 0 or not b['is_bonus']]

<<<<<<< HEAD
    # Estrutura final para o template
=======
    assist_context = {
        'is_win': attempt.is_won, 
        'score': attempt.final_score
    }
    assistant_payload = get_assistant_data(guardian, 'results', context_data=assist_context)

>>>>>>> origin/guardians
    results_data = {
        'game_type': 'password_game',
        'game_title': 'Segredo',
        'attempt_id': attempt.id,
        'source_id': attempt.id,
        'final_score': attempt.final_score,
        'base_score': base_points,
        'duration_seconds': round(duration_seconds, 2) if duration_seconds else None,
        'is_winner': attempt.is_won,
        'is_perfect': attempt.is_won, 
        'score_breakdown': score_breakdown,
        'accuracy_info': {
            'label': 'Status',
            'correct': 1 if attempt.is_won else 0,
            'total': 1,
            'percentage': 100 if attempt.is_won else 0
        }
    }

    return render_template(
        'guardians/page_resultados_unificado.html',
        results_data=results_data,
        guardian=guardian,
        attempt=attempt,
<<<<<<< HEAD
        show_confetti=attempt.is_won 
=======
        show_confetti=attempt.is_won,
        assistant_data=assistant_payload 
>>>>>>> origin/guardians
    )

@guardians_bp.route('/password-game/abandon/<int:attempt_id>', methods=['POST'])
@login_required
def submit_password_game_abandon(attempt_id):
    attempt = PasswordAttempt.query.get_or_404(attempt_id)
    
    # Validação de segurança
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    if attempt.guardian_id != guardian.id:
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    # Marca como completo e falha
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.is_won = False
    attempt.score = 0
    attempt.final_score = 0
    
    db.session.commit()

    return jsonify({
        'status': 'abandoned',
        'redirect': url_for('guardians_bp.password_game_result', attempt_id=attempt.id)
    })

## ROTA DE RETAKE DOS MINIGAMES ##
@guardians_bp.route('/minigame/retake/<string:game_type>/<int:game_id>', methods=['POST'])
@login_required
def retake_minigame(game_type, game_id):
    guardian = Guardians.query.filter_by(user_id=SessionManager.get("user_id")).first()
    
    if not guardian:
        flash("Guardião não encontrado.", "danger")
        return redirect(url_for('guardians_bp.central'))

    if guardian.minigame_retake_tokens > 0:
        attempt_to_delete = None
        redirect_url = None
        game_title = "Minigame"
        
        try:
            # Encontra a tentativa antiga
            if game_type == 'termo':
                attempt_to_delete = TermoAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).order_by(TermoAttempt.completed_at.desc()).first()
                if attempt_to_delete and attempt_to_delete.game:
                    game_title = f"Código: ******"
                redirect_url = url_for('guardians_bp.play_termo', game_id=game_id)
                
            elif game_type == 'anagrama':
                attempt_to_delete = AnagramAttempt.query.filter_by(guardian_id=guardian.id, game_id=game_id).order_by(AnagramAttempt.completed_at.desc()).first()
                if attempt_to_delete and attempt_to_delete.game:
                    game_title = attempt_to_delete.game.title
                redirect_url = url_for('guardians_bp.play_anagram', game_id=game_id)
                
            elif game_type == 'password' or game_type == 'password_game':
                attempt_to_delete = PasswordAttempt.query.get(game_id) 
                if attempt_to_delete:
                    game_title = "Segredo"
                redirect_url = url_for('guardians_bp.play_password_game')

            else:
                flash("Tipo de jogo desconhecido para retake.", "warning")
                return redirect(url_for('guardians_bp.central'))

            if attempt_to_delete:
                # 1. Pega o score da tentativa antiga
                score_to_remove = attempt_to_delete.final_score or 0
                
                # 2. Gasta o token
                guardian.minigame_retake_tokens -= 1
                
                # 3. Subtrai o score antigo
                guardian.score_atual = (guardian.score_atual or 0) - score_to_remove
                
                # 4. Cria um log de reversão
                reversal_desc = f"Token de Retake (Minigame) usado. Pontuação de '{game_title}' (-{score_to_remove} pts) estornada."
                reversal_history = HistoricoAcao(
                    guardian_id=guardian.id,
                    descricao=reversal_desc,
                    pontuacao=-score_to_remove
                )
                db.session.add(reversal_history)
                
                # 5. Apaga a tentativa antiga
                db.session.delete(attempt_to_delete)
                db.session.add(guardian) # Salva o guardião atualizado
                db.session.commit()
                
                flash(f"Token de Minigame usado! Você tem {guardian.minigame_retake_tokens} restantes. Boa sorte!", "info")
                return redirect(redirect_url)
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao tentar usar o token: {e}", "danger")
    
    flash("Você não tem tokens de retake de minigame ou a ação é inválida.", "danger")
    return redirect(url_for('guardians_bp.central'))


##ROTA PARA REPORT DE BUGS E SUGESTOES##
@guardians_bp.route('/guardians/feedback', methods=['GET'])
@login_required
def feedback_form():
    """ Rota para exibir o formulário de feedback. """
<<<<<<< HEAD
    return render_template('guardians/page_report_bug.html')
=======
    
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    assistant_data = get_assistant_data(guardian, 'report_bug')

    return render_template(
        'guardians/page_report_bug.html', 
        assistant_data=assistant_data
    )
>>>>>>> origin/guardians


@guardians_bp.route('/guardians/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """ Rota para processar o formulário de feedback. """
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()

    # 1. Captura os dados do formulário
<<<<<<< HEAD
    raw_type = request.form.get('report_type') # vem: 'bug', 'feedback' ou 'security'
=======
    raw_type = request.form.get('report_type')
>>>>>>> origin/guardians
    title = request.form.get('title')
    description_text = request.form.get('description')
    attachment_file = request.files.get('attachment')

    # Validação Básica
    if not description_text or not title:
        flash('Por favor, preencha o título e a descrição.', 'warning')
        return redirect(url_for('guardians_bp.feedback_form'))

    # 2. Mapeamento Inteligente (Compatibilidade com DB Enum)
<<<<<<< HEAD
    # Seu banco só aceita 'BUG' ou 'SUGGESTION'.
    
    db_report_type = 'BUG' # Valor padrão
    prefix_tag = ""       # Tag visual para ajudar o admin
=======
    db_report_type = 'BUG' 
    prefix_tag = ""       
>>>>>>> origin/guardians

    if raw_type == 'feedback':
        db_report_type = 'SUGGESTION'
    elif raw_type == 'security':
<<<<<<< HEAD
        # Truque: Salva como BUG, mas marca o texto para destaque
        db_report_type = 'BUG'
        prefix_tag = "[!!! VULNERABILIDADE !!!] "
    else:
        # Default para 'bug' ou qualquer outro erro
=======
        db_report_type = 'BUG'
        prefix_tag = "[!!! VULNERABILIDADE !!!] "
    else:
>>>>>>> origin/guardians
        db_report_type = 'BUG'

    attachment_db_path = None 

<<<<<<< HEAD
    # --- Lógica de Upload (Igual à anterior) ---
=======
>>>>>>> origin/guardians
    if attachment_file and attachment_file.filename != '':
        if allowed_file_img(attachment_file.filename):
            try:
                upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER_FEEDBACK)
                os.makedirs(upload_dir, exist_ok=True)

                filename = secure_filename(attachment_file.filename)
                extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{extension}"
                save_path = os.path.join(upload_dir, unique_filename)

                attachment_file.save(save_path)
                attachment_db_path = os.path.join(UPLOAD_FOLDER_FEEDBACK.replace('static/', ''), unique_filename).replace('\\', '/')

            except Exception as e:
                print(f"Erro ao salvar anexo: {e}")
                flash('Erro no upload da imagem. O report foi enviado sem anexo.', 'warning')
        else:
            flash('Arquivo inválido. Apenas imagens (.png, .jpg, .gif).', 'warning')
            return redirect(url_for('guardians_bp.feedback_form'))

    try:
<<<<<<< HEAD
        # 3. Montagem da Descrição Final
=======
>>>>>>> origin/guardians
        final_description = f"{prefix_tag}[ASSUNTO: {title}]\n\n{description_text}"

        new_report = FeedbackReport(
            guardian_id=guardian.id,
<<<<<<< HEAD
            report_type=db_report_type, # Agora garantimos que é BUG ou SUGGESTION
=======
            report_type=db_report_type,
>>>>>>> origin/guardians
            description=final_description,
            attachment_path=attachment_db_path
        )
        db.session.add(new_report)
        db.session.commit()
        
        flash('Protocolo de reporte enviado com sucesso! Agradecemos a colaboração.', 'success')
        return redirect(url_for('guardians_bp.feedback_form'))

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar feedback: {e}")
        flash('Erro de sistema ao salvar reporte.', 'danger')
        return redirect(url_for('guardians_bp.feedback_form'))


# == ROTA PARA RECOMPENSA DE MISSAO             ==
@guardians_bp.route('/claim-weekly-reward', methods=['POST'])
@login_required 
def claim_weekly_reward():
    """
    Processa o resgate do baú semanal com lógica de RNG e Bônus de Loja.
    """
<<<<<<< HEAD
    
    # 1. Identifica o Guardião
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if not guardian:
        flash("Sua sessão expirou ou o guardião não foi encontrado.", "danger")
=======
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if not guardian:
        flash("Sua sessão expirou.", "danger")
>>>>>>> origin/guardians
        return redirect(url_for('auth_bp.login'))

    quest_set = WeeklyQuestSet.query.filter_by(
        guardian_id=guardian.id, 
        is_completed=True, 
        is_claimed=False   
    ).first()

<<<<<<< HEAD
    # 2. Validações
    if not quest_set:
        open_set = WeeklyQuestSet.query.filter_by(guardian_id=guardian.id, is_claimed=False).first()
        if open_set:
            flash("Você ainda não completou todas as missões deste pacote!", "warning")
        else:
            flash("Nenhuma recompensa disponível para resgate no momento.", "info")
            
        return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

    # 3. Processa a Recompensa
    try:
        # A. CÁLCULO BASE (Salário + Sorteio RNG)
        reward_data = calculate_weekly_coin_reward()
        
        raw_coins = reward_data['total'] 
        rarity = reward_data['breakdown']['rarity']
        
        # B. CÁLCULO DE MULTIPLICADORES (Itens de Loja)
        shop_bonus_pct = _get_shop_bonus(guardian, 'GCOIN_BONUS_PCT')
        
        # Aplica o bônus sobre o valor bruto
        final_coins = int(raw_coins * (1 + shop_bonus_pct / 100.0))
=======
    if not quest_set:
        flash("Nenhuma recompensa disponível.", "info")
        return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

    try:
        # A. CÁLCULO BASE
        reward_data = calculate_weekly_coin_reward()
        raw_coins = reward_data['total'] 
        rarity = reward_data['breakdown']['rarity']
        
        # B. CÁLCULO DE MULTIPLICADORES (Itens de Loja e Insígnias)
        shop_bonus_val = _get_shop_bonus(guardian, 'GCOIN_BONUS_PCT')
        insignia_bonus_val = _get_insignia_bonus(guardian, 'GCOIN_BONUS_PCT')
        total_bonus_pct = shop_bonus_val + insignia_bonus_val
        multiplier = 1 + (total_bonus_pct / 100.0)
        
        final_coins = int(raw_coins * multiplier)

        # ===============================

>>>>>>> origin/guardians
        bonus_value_gained = final_coins - raw_coins 
        
        # C. APLICAÇÃO DO RESGATE
        quest_set.is_claimed = True
        guardian.guardian_coins = (guardian.guardian_coins or 0) + final_coins
        
        # D. HISTÓRICO E LOGS
        rarity_label = "Comum"
        if rarity == 'RARE': rarity_label = "RARA"
        elif rarity == 'EPIC': rarity_label = "ÉPICA"
        
        msg_hist = f"Resgatou Recompensa {rarity_label}: +{final_coins} GC"
        
        if bonus_value_gained > 0:
<<<<<<< HEAD
            msg_hist += f" (Inclui bônus de item: +{bonus_value_gained})"
=======
            msg_hist += f" (Bônus: +{bonus_value_gained})"
>>>>>>> origin/guardians

        novo_historico = HistoricoAcao(
            guardian_id=guardian.id,
            descricao=msg_hist,
            pontuacao=0 
        )
        db.session.add(novo_historico)
        
<<<<<<< HEAD
        # E. FINALIZAÇÃO E NOVO CICLO
        db.session.commit() 

        get_or_create_active_quest_set(guardian)
=======
        db.session.commit() 

        get_or_create_active_quest_set(guardian)
        
        # Flash message ajustada
>>>>>>> origin/guardians
        flash_msg = f"Recompensa resgatada! +{final_coins} G-Coins."
        flash_cat = "success"
        
        if rarity == 'EPIC':
            flash_msg = f"SORTE GRANDE! Drop ÉPICO recebido: +{final_coins} G-Coins!"
            flash_cat = "warning" 
            
        flash(flash_msg, flash_cat)

    except Exception as e:
        db.session.rollback()
        print(f"Erro claim reward: {e}")
<<<<<<< HEAD
        flash(f"Ocorreu um erro ao processar o resgate. Tente novamente.", "danger")
=======
        flash(f"Ocorreu um erro ao processar o resgate.", "danger")
>>>>>>> origin/guardians

    return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

# == ROTA PARA LOJA           ==
@guardians_bp.route('/guardians/loja')
@login_required
def loja():
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if not guardian:
        return redirect(url_for('guardians_bp.central'))

    # 1. Obtém o estado da loja (Gacha Diário)
    shop_state = get_or_create_shop_state(guardian)
    
    # 2. Busca os objetos dos itens baseados nos IDs sorteados
    daily_ids = shop_state.current_items_ids or []
    
    if daily_ids:
        daily_items = ShopItem.query.filter(ShopItem.id.in_(daily_ids)).all()
    else:
        daily_items = []

    # 3. Busca compras para controle de limite
    purchases = GuardianPurchase.query.filter_by(guardian_id=guardian.id).all()
    purchase_counts = {} 
    active_modules = []      
    seen_module_ids = set() 

    for p in purchases:
        purchase_counts[p.item_id] = purchase_counts.get(p.item_id, 0) + 1

        if p.item.category != 'Consumíveis':
            if p.item.id not in seen_module_ids:
                active_modules.append(p.item)
                seen_module_ids.add(p.item.id)

<<<<<<< HEAD
    # 4. Calcula custo atual do reroll
    reroll_cost = calculate_reroll_cost(shop_state.reroll_count)
=======
    reroll_cost = calculate_reroll_cost(shop_state.reroll_count)
    max_slots = get_game_setting('ITEMS_MODULES_SET_AMOUNT', 4, int)
    if request.args.get('purchase') == 'success':
        assistant_payload = get_assistant_data(guardian, 'shop_purchase')
    else:
        assistant_payload = get_assistant_data(guardian, 'loja')
>>>>>>> origin/guardians

    return render_template(
        'guardians/page_loja.html',
        guardian=guardian,
        items=daily_items,
        active_modules=active_modules,
        purchase_counts=purchase_counts,
        reroll_cost=reroll_cost, 
        reroll_count=shop_state.reroll_count,
<<<<<<< HEAD
        BONUS_TYPES=BONUS_TYPES
=======
        BONUS_TYPES=BONUS_TYPES,
        max_slots=max_slots,
        assistant_data=assistant_payload
>>>>>>> origin/guardians
    )

@guardians_bp.route('/guardians/loja/reroll', methods=['POST'])
@login_required
def reroll_shop():
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    shop_state = get_or_create_shop_state(guardian)
    
    # 1. Valida Custo
    cost = calculate_reroll_cost(shop_state.reroll_count)
    
    if guardian.guardian_coins < cost:
        flash(f'Saldo insuficiente para atualizar upgrades. Necessário: {cost} GC.', 'danger')
        return redirect(url_for('guardians_bp.loja'))
    
    # 2. Executa Pagamento e Reroll
    guardian.guardian_coins -= cost
    shop_state.reroll_count += 1
    
    # Gera novos IDs únicos
    new_items = select_unique_daily_items(4)
    shop_state.current_items_ids = new_items
    
    # Salva histórico
    db.session.add(HistoricoAcao(guardian_id=guardian.id, descricao=f"Reroll de Upgrades", pontuacao=-cost))

    try:
        update_mission_progress(guardian, MissionCodeEnum.SPEND_GC_REROLL, amount=cost)
    except:
        pass
    
    db.session.commit()
    
    flash('Upgrades atualizados com sucesso! Novos suprimentos disponíveis.', 'success')
    return redirect(url_for('guardians_bp.loja'))

@guardians_bp.route('/guardians/loja/comprar/<int:item_id>', methods=['POST'])
@login_required
def comprar_item(item_id):
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    item = ShopItem.query.get_or_404(item_id)

    if not guardian:
        return redirect(url_for('guardians_bp.central'))

    # 1. Validação: Saldo
    is_consumable = item.category == 'Consumíveis' or 'TOKEN' in item.bonus_type
    
    # Busca compras anteriores deste item
    purchases = GuardianPurchase.query.filter_by(guardian_id=guardian.id, item_id=item.id).all()
    purchased_count = len(purchases)

    # Limite a 4 itens por inventário
<<<<<<< HEAD
    if item.category != 'Consumíveis': # Tokens podem comprar à vontade
=======
    if item.category != 'Consumíveis':
>>>>>>> origin/guardians
        if not check_shop_slots_available(guardian.id):
            flash('Seus slots de memória estão cheios!', 'warning')
            return redirect(url_for('guardians_bp.loja'))

    # Regra A: Limite Hard (definido no admin)
    if item.purchase_limit and purchased_count >= item.purchase_limit:
        flash("Você já atingiu o limite máximo de compras para este item.", "warning")
        return redirect(url_for('guardians_bp.loja'))

    # Regra B: Item Ativo (Não Consumível)
    if not is_consumable:
        now = datetime.utcnow()
        for p in purchases:
<<<<<<< HEAD
            # Se o item é permanente (duration_days é None ou 0), e o cara já comprou, já era.
=======
>>>>>>> origin/guardians
            if not item.duration_days or item.duration_days == 0:
                flash("Você já possui este item permanente.", "warning")
                return redirect(url_for('guardians_bp.loja'))
            
<<<<<<< HEAD
            # Se tem duração, calcula expiração
=======
>>>>>>> origin/guardians
            expiration_date = p.purchased_at + timedelta(days=item.duration_days)
            if now < expiration_date:
                days_left = (expiration_date - now).days
                flash(f"Você já tem este item ativo! Ele expira em {days_left} dias.", "warning")
                return redirect(url_for('guardians_bp.loja'))

    try:
        # 3. Processa o Pagamento
<<<<<<< HEAD
=======
        if guardian.guardian_coins < item.cost:
            flash('Saldo insuficiente de Guardian Coins!', 'danger')
            return redirect(url_for('guardians_bp.loja'))
>>>>>>> origin/guardians
        guardian.guardian_coins -= item.cost
        
        # 4. Entrega o Item
        
        # Caso A: Consumível (Token)
        if item.bonus_type == 'ADD_QUIZ_TOKEN':
            guardian.retake_tokens += 1
            msg = "Compra realizada! +1 Token de Quiz adicionado."

            
        elif item.bonus_type == 'ADD_MINIGAME_TOKEN':
            guardian.minigame_retake_tokens += 1
            msg = "Compra realizada! +1 Token de Minigame adicionado."
            
        # Caso B: Bônus Passivo / Cosmético
        else:
            msg = f"Compra realizada! Item '{item.name}' adquirido."

        # Registra a compra (Histórico da Loja)
        purchase = GuardianPurchase(
            guardian_id=guardian.id,
            item_id=item.id,
            cost_at_purchase=item.cost
        )
        db.session.add(purchase)
        
        # Registra no Histórico de Ações (Log visível no perfil)
        log = HistoricoAcao(
            guardian_id=guardian.id,
            descricao=f"Upgrades: Comprou '{item.name}' por {item.cost} GC",
            pontuacao=0
        )
        db.session.add(log)
        db.session.add(guardian)

        try:
            update_mission_progress(guardian, MissionCodeEnum.SPEND_GC_UPGRADES, amount=item.cost)

        except:
            pass


        db.session.commit()
<<<<<<< HEAD
=======
        guardian.stat_shop_count += 1 #conquista da loja é feita por itens comprados
        _, conquistas_ganhas = atualizar_nivel_usuario(guardian)
        if conquistas_ganhas:
            flash(f"Conquista de Comerciante Desbloqueada!", "success")
>>>>>>> origin/guardians
        
        flash(msg, "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao processar compra: {e}", "danger")

<<<<<<< HEAD
    return redirect(url_for('guardians_bp.loja'))
=======
    return redirect(url_for('guardians_bp.loja', purchase='success'))
>>>>>>> origin/guardians

@guardians_bp.route('/loja/descartar/<int:item_id>', methods=['POST'])
@login_required
def descartar_item(item_id):
    """
    Remove um item passivo do inventário do guardião (libera slot).
    Nota: Isso destrói o item. Se quiser comprar de novo, paga de novo.
    """
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    # Busca a compra específica deste item para este guardião
    purchase = GuardianPurchase.query.filter_by(
        guardian_id=guardian.id, 
        item_id=item_id
    ).first()
    
    if not purchase:
        flash("Item não encontrado no seu inventário.", "danger")
        return redirect(url_for('guardians_bp.loja'))
    
    try:
        item_name = purchase.item.name
        history_entry = HistoricoAcao(
            guardian_id=guardian.id,
            descricao=f"Descartou o módulo '{item_name}' para liberar espaço.",
            pontuacao=0
        )
        db.session.add(history_entry)
        db.session.delete(purchase)
        db.session.commit()
        
        flash(f"Módulo '{item_name}' foi descartado e o slot foi liberado.", "warning")
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao descartar item: {e}")
        flash("Erro ao processar o descarte.", "danger")
        
    return redirect(url_for('guardians_bp.loja'))
<<<<<<< HEAD
=======

# ROTA DO ASSISTENTE DE TUTORIAIS
@guardians_bp.route('/api/mark-tutorial-seen/<tutorial_id>', methods=['POST'])
@login_required
def mark_tutorial_seen(tutorial_id):
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    
    if guardian:
        current_data = dict(guardian.tutorials_seen or {})
        current_data[tutorial_id] = True
        
        guardian.tutorials_seen = current_data

        db.session.commit()
        
        return jsonify({"status": "success", "id": tutorial_id})
    
    return jsonify({"status": "error"}), 400
>>>>>>> origin/guardians
