from collections import defaultdict
from datetime import datetime, date, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from flask import render_template, redirect, url_for, request, flash, session
from modules.guardians.missions_logic import get_or_create_active_quest_set
from modules.login.decorators import login_required
from modules.login.session_manager import SessionManager
from application.models import (db, Guardians, HistoricoAcao, NivelSeguranca, GuardianFeatured,
                                QuizAttempt, Specialization, AchievementCategory,
                                TermoAttempt, AnagramAttempt, SpecializationPerkLevel, GuardianInsignia, 
                                Perk, ShopItem, GuardianPurchase, PasswordAttempt)
from .logic import (
    get_global_setting, calculate_week_days_status, get_effective_streak_percentage, get_insignia_category, get_streak_cap)
from .utils_assistant import get_assistant_data
from . import guardians_bp


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

#MONTAGEM DO CARD DE BUFF EM MEU PERFIL
def generate_active_buffs_html(perfil, effective_streak_percent):
    """
    Gera HTML estilo JRPG (Painel de Status) para o popover.
    """
    rows = []

    STAT_MAP = {
        'GCOIN_BONUS_PCT':    ('stat-gold', 'bi-coin', 'MOEDAS'),
        'QUIZ_BONUS_PCT':     ('stat-int',  'bi-lightning-charge', 'QUIZ'),
        'PATROL_BONUS_PCT':   ('stat-def',  'bi-shield-check', 'PATRULHA'),
        'CODEGAME_BONUS_PCT': ('stat-dex',  'bi-controller', 'GAMES'),
        'STREAK_BONUS_PCT':   ('stat-str',  'bi-fire', 'TETO OFENSIVA'),
        'GLOBAL_SCORE_PCT':   ('stat-all',  'bi-globe', 'GLOBAL'),
        'DEFAULT':            ('text-muted', 'bi-caret-up', 'GERAL')
    }

    def _create_row(icon, name, target_name, value_str, style_class):
        return f"""
        <div class="buff-row">
            <div class="buff-source">
                <i class="bi {icon} {style_class}"></i> {name}
            </div>
            <div class="buff-target {style_class}">
                {target_name}
            </div>
            <div class="buff-value {style_class}">
                {value_str} <i class="bi bi-caret-up-fill" style="font-size: 0.7em;"></i>
            </div>
        </div>
        """

    # 0. BÔNUS DE OFENSIVA (DIÁRIO)
    if perfil.current_streak > 0:
        style, icon, target = STAT_MAP['STREAK_BONUS_PCT']
        dynamic_cap = get_streak_cap(perfil) 
        val_display = f"+{effective_streak_percent}% <span style='font-size:0.65em; opacity:0.6;'>/ {dynamic_cap}% MAX</span>"
        
        rows.append(_create_row(
            icon="bi-fire", 
            name="Ofensiva Diária", 
            target_name="GLOBAL", 
            value_str=val_display,
            style_class="stat-str" 
        ))

    # 1. BÔNUS DE ESPECIALIZAÇÃO (CAMINHO)
    if perfil.specialization_id and perfil.nivel_id:
        current_level_number = perfil.nivel.level_number
        perk_entries = db.session.query(SpecializationPerkLevel)\
            .join(Perk).filter(
                SpecializationPerkLevel.specialization_id == perfil.specialization_id,
                SpecializationPerkLevel.level == current_level_number
            ).options(joinedload(SpecializationPerkLevel.perk)).all()

        for entry in perk_entries:
            val = int(entry.bonus_value) if entry.bonus_value == int(entry.bonus_value) else entry.bonus_value
            p_code = entry.perk.perk_code
            style, icon, target = STAT_MAP.get(p_code, STAT_MAP['DEFAULT'])
            
            sulfixo = "%" if '_PCT' in p_code else ""
            
            rows.append(_create_row(
                icon="bi-person-badge",
                name=f"{entry.perk.name} (Nv.{entry.level})",
                target_name=target,
                value_str=f"+{val}{sulfixo}",
                style_class=style
            ))

    # 2. BÔNUS DE CONQUISTAS (INSÍGNIAS)
    if perfil.featured_associations:
        for assoc in perfil.featured_associations:
            ins = assoc.insignia
            if ins and ins.bonus_value:
                val = int(ins.bonus_value) if ins.bonus_value == int(ins.bonus_value) else ins.bonus_value
                style, icon, target = STAT_MAP.get(ins.bonus_type, STAT_MAP['DEFAULT'])
                
                rows.append(_create_row(
                    icon="bi-award-fill",
                    name=ins.nome,
                    target_name=target,
                    value_str=f"+{val}%",
                    style_class=style
                ))

    # 3. BÔNUS DE ITENS (LOJA)
    try:
        shop_bonuses = db.session.query(ShopItem)\
            .join(GuardianPurchase, ShopItem.id == GuardianPurchase.item_id)\
            .filter(
                GuardianPurchase.guardian_id == perfil.id,
                ShopItem.bonus_value > 0,
                ShopItem.bonus_type.isnot(None),
                (GuardianPurchase.expires_at == None) | (GuardianPurchase.expires_at > datetime.utcnow())
            ).all()

        for item in shop_bonuses:
            val = int(item.bonus_value) if item.bonus_value == int(item.bonus_value) else item.bonus_value
            sulfixo = "%" if '_PCT' in item.bonus_type else ""
            style, icon, target = STAT_MAP.get(item.bonus_type, STAT_MAP['DEFAULT'])
            
            item_icon = item.image_path if (item.image_path and 'bi-' in item.image_path) else icon

            rows.append(_create_row(
                icon=item_icon,
                name=item.name,
                target_name=target,
                value_str=f"+{val}{sulfixo}",
                style_class=style
            ))
            
    except Exception as e:
        print(f"Erro helper buff shop: {e}")

    if rows:
        return f'<div class="buff-panel">{"".join(rows)}</div>'
    
    return "<div class='p-3 text-center text-muted small font-tech'>NENHUM MODIFICADOR DE SISTEMA ATIVO.</div>"

@guardians_bp.route('/meu-perfil', defaults={'perfil_id': None})
@guardians_bp.route('/meu-perfil/<int:perfil_id>')
@login_required
def meu_perfil(perfil_id):
    logged_in_user_id = SessionManager.get("user_id")
    is_own_profile = False
    
    # --- 1. IDENTIFICAÇÃO DO PERFIL ---
    if perfil_id is None:
        query_filter = Guardians.user_id == logged_in_user_id
        is_own_profile = True
    else:
        query_filter = Guardians.id == perfil_id
        temp_guardian = Guardians.query.filter_by(id=perfil_id, user_id=logged_in_user_id).first()
        if temp_guardian:
            is_own_profile = True

    perfil = Guardians.query.options(
        joinedload(Guardians.nivel),
        joinedload(Guardians.specialization),
        joinedload(Guardians.featured_associations).joinedload(GuardianFeatured.insignia)
    ).filter(query_filter).first()

    if not perfil:
        flash("Perfil não encontrado.", "danger")
        return redirect(url_for("home_bp.render_home")) 

    if not is_own_profile and perfil.is_anonymous:
        flash('Este guardião optou por manter o perfil privado.', 'info')
        return redirect(url_for('guardians_bp.rankings'))

    # --- 2. LÓGICA DE INSÍGNIAS (Agrupamento) ---
    guardian_insignias_entries = GuardianInsignia.query.filter_by(guardian_id=perfil.id)\
        .options(joinedload(GuardianInsignia.insignia)).all()
    
    insignias_ganhas = [gi.insignia for gi in guardian_insignias_entries if gi.insignia]
    
    grouped_insignias = defaultdict(list)
    for insignia in insignias_ganhas:
        category = get_insignia_category(insignia)
        grouped_insignias[category].append(insignia)

    db_categories = AchievementCategory.query.order_by(AchievementCategory.order.asc()).all()
    categorized_achievements_list = []
    processed_categories = set()
    
    for cat_obj in db_categories:
        if cat_obj.name in grouped_insignias:
            categorized_achievements_list.append({
                'category': cat_obj.name,
                'insignias': grouped_insignias[cat_obj.name]
            })
            processed_categories.add(cat_obj.name)
            
    for cat_name, insignias in grouped_insignias.items():
        if cat_name not in processed_categories:
            categorized_achievements_list.append({'category': cat_name, 'insignias': insignias})

    # --- 3. STATUS E BUFFS (REFATORADO) ---
    effective_streak_percent = get_effective_streak_percentage(perfil)
    week_days_data = calculate_week_days_status(perfil)
    active_perks_html = generate_active_buffs_html(perfil, effective_streak_percent)

    # --- 4. HISTÓRICO E PROGRESSO ---
    historico = perfil.historico_acoes.order_by(desc(HistoricoAcao.data_evento)).limit(50)
    nivel_atual = perfil.nivel 
    proximo_nivel = None
    progresso_percentual = 0
    
    if nivel_atual and perfil.specialization_id:
        proximo_nivel = NivelSeguranca.query.filter(
            NivelSeguranca.specialization_id == perfil.specialization_id, 
            NivelSeguranca.level_number > nivel_atual.level_number 
        ).order_by(NivelSeguranca.level_number.asc()).first() 
        
        if proximo_nivel:
            delta = proximo_nivel.score_minimo - nivel_atual.score_minimo
            current_delta = (perfil.score_atual or 0) - nivel_atual.score_minimo
            progresso_percentual = max(0, min(100, int((current_delta / delta) * 100))) if delta > 0 else 100
        else: 
            progresso_percentual = 100
    
    # Ranking Simples
    # (Nota: Em produção com muitos usuários, isso deve ser cacheado ou feito via SQL direto rank())
    todos_ids = [p.id for p in Guardians.query.order_by(Guardians.score_atual.desc()).with_entities(Guardians.id).all()]
    try:
        ranking_atual = todos_ids.index(perfil.id) + 1
    except ValueError:
        ranking_atual = "N/A"

    # --- 5. INVENTÁRIO ---
    active_purchases = GuardianPurchase.query.filter(
        GuardianPurchase.guardian_id == perfil.id,
        (GuardianPurchase.expires_at == None) | (GuardianPurchase.expires_at > datetime.utcnow())
    ).options(joinedload(GuardianPurchase.item)).all()

    inventory_bag = {}
    for purchase in active_purchases:
        item = purchase.item
        if item.id not in inventory_bag:
            bonus_display = "Item Raro"
            if item.bonus_value:
                val = int(item.bonus_value) if item.bonus_value.is_integer() else item.bonus_value
                bonus_display = f"+{val}% Bônus" if 'PCT' in (item.bonus_type or '') else f"+{val} Pontos"
            elif item.category == 'Cosméticos': bonus_display = "Visual"
            elif item.category == 'Consumíveis': bonus_display = "Uso Único"

            inventory_bag[item.id] = {
                'name': item.name,
                'icon': item.image_path or 'bi-box-seam',
                'category': item.category,
                'bonus_display': bonus_display,
                'description': item.description,
                'count': 0,
                'rarity': item.rarity or 'COMMON'
            }
        inventory_bag[item.id]['count'] += 1

    # --- 6. BLOQUEIOS E CONFIGURAÇÕES ---
    spec_is_locked_time = False
    spec_days_remaining = 0
    spec_is_locked_xp = False
    
    cfg_days = get_global_setting('SPEC_CHANGE_COOLDOWN_DAYS', default=14)
    cfg_xp = get_global_setting('SPEC_CHANGE_MIN_XP', default=1000)

    if perfil.last_spec_change_at:
        time_since = datetime.utcnow() - perfil.last_spec_change_at
        if time_since < timedelta(days=cfg_days):
            spec_is_locked_time = True
            spec_days_remaining = cfg_days - time_since.days

    if (perfil.score_atual or 0) < cfg_xp:
        spec_is_locked_xp = True

    # --- 7. MISSÕES E ESTATÍSTICAS ---
    stats = {
        'termo': TermoAttempt.query.filter_by(guardian_id=perfil.id, is_won=True).count(),
        'password': PasswordAttempt.query.filter_by(guardian_id=perfil.id, is_won=True).count(),
        'anagram': AnagramAttempt.query.filter(AnagramAttempt.guardian_id == perfil.id, AnagramAttempt.completed_at.isnot(None)).count(),
        'quiz': QuizAttempt.query.filter_by(guardian_id=perfil.id).count(),
        'patrol': HistoricoAcao.query.filter(HistoricoAcao.guardian_id == perfil.id, HistoricoAcao.descricao.like('Codebreaker (Patrulha):%')).count()
    }
    minigames_count = stats['termo'] + stats['password'] + stats['anagram']
    
    q_needed = get_global_setting('QUIZZES_FOR_TOKEN', default=5)
    m_needed = get_global_setting('MINIGAMES_FOR_TOKEN', default=5, setting_type=int)
    
    quizzes_remaining = q_needed - ((perfil.perfect_quiz_cumulative_count or 0) % q_needed) if q_needed > 0 else 0
    minigames_remaining = m_needed - ((perfil.perfect_minigame_cumulative_count or 0) % m_needed) if m_needed > 0 else 0

    quest_set = None
    active_missions = []
    assistant_payload = get_assistant_data(perfil, 'meu_perfil')

    if is_own_profile:
        try:
            quest_data = get_or_create_active_quest_set(perfil) 
            quest_set = quest_data.get('set')
            active_missions = quest_data.get('missions')
            
            if quest_set:
                quest_set.total_missions_count = len(active_missions)
                quest_set.completed_missions_count = sum(1 for m in active_missions if m.is_completed)
                for m in active_missions: m.description_display = m.title_generated 
        except Exception as e:
            print(f"Erro ao carregar missões: {e}")

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
        numero_conquistas=len(insignias_ganhas),
        
        # Estatísticas passadas limpas
        quizzes_respondidos_count=stats['quiz'],
        minigames_count=minigames_count,
        patrols_completed_count=stats['patrol'],
        patrol_completed_today=(perfil.last_patrol_date == date.today()),
        
        # Tokens
        quizzes_needed_for_token=q_needed,
        minigames_needed_for_token=m_needed,
        quizzes_remaining=quizzes_remaining,
        minigames_remaining=minigames_remaining,
        
        # Buffs e Status
        effective_streak_percent=effective_streak_percent,
        week_days_data=week_days_data,
        active_perks_html=active_perks_html,
        
        # Missões e Specs
        quest_set=quest_set,
        active_missions=active_missions,
        spec_is_locked_time=spec_is_locked_time, 
        spec_days_remaining=spec_days_remaining,
        spec_is_locked_xp=spec_is_locked_xp,
        min_xp_required=cfg_xp,
        user_xp=(perfil.score_atual or 0),
        
        #assistente
        assistant_data=assistant_payload
    )

##ROTA PRA EDITAR PERFIL
@guardians_bp.route('/meu-perfil/editar', methods=['GET', 'POST'])
@login_required
def edit_profile():
    logged_in_user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if not guardian:
        flash("Perfil não encontrado.", "danger")
        return redirect(url_for('guardians_bp.meu_perfil'))

    minhas_insignias = GuardianInsignia.query.filter_by(
        guardian_id=guardian.id
    ).options(joinedload(GuardianInsignia.insignia)).all()

    meus_ids_validos = [mi.insignia.id for mi in minhas_insignias]
    ids_ja_selecionados = set()
    badge_limit = int(get_global_setting('BADGE_SET_AMOUNT', default=3))

    if request.method == 'POST':
        guardian.nickname = request.form.get('nickname')
        new_avatar = request.form.get('avatar_seed')
        if new_avatar: guardian.avatar_seed = new_avatar

        guardian.featured_associations = [] 
        ids_processados = set()

        for i in range(badge_limit):
            f_id = request.form.get(f'featured_insignia_{i}')
            
            if f_id and f_id.isdigit():
                f_id_int = int(f_id)

                if f_id_int in meus_ids_validos and f_id_int not in ids_processados:
                    
                    nova_associacao = GuardianFeatured(
                        guardian_id=guardian.id,
                        insignia_id=f_id_int,
                        slot_index=i 
                    )
                    guardian.featured_associations.append(nova_associacao)
                    
                    ids_processados.add(f_id_int) 
                
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('guardians_bp.meu_perfil'))

    return render_template('guardians/page_edit_profile.html', 
                           guardian=guardian,
                           minhas_insignias=minhas_insignias,
                           badge_limit=badge_limit)


# == ROTA PARA ESCOLHA DE ESPECIALIZAÇÃO                  ==
@guardians_bp.route('/escolher-caminho', methods=['GET', 'POST'])
@login_required
def choose_specialization():
    user_id = session.get('user_id')
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    cfg_days = get_global_setting('SPEC_CHANGE_COOLDOWN_DAYS', default=14)
    is_locked = False
    days_remaining = 0
    
    if guardian.last_spec_change_at:
        now = datetime.utcnow() 
        time_since_change = now - guardian.last_spec_change_at
        
        if time_since_change < timedelta(days=cfg_days):
            is_locked = True
            days_remaining = cfg_days - time_since_change.days

    if request.method == 'POST':
        if is_locked:
            flash(f"Protocolo em resfriamento. Aguarde {days_remaining} dias para recalibrar seu caminho.", "danger")
            return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

        choice_id = request.form.get('specialization_id')
        if choice_id:
            if guardian.specialization_id == int(choice_id):
                 flash('Você já segue este protocolo.', 'info')
                 return redirect(url_for('guardians_bp.meu_perfil', perfil_id=guardian.id))

            chosen_spec = Specialization.query.get(choice_id)
            first_level = sorted(chosen_spec.levels, key=lambda x: x.level_number)[0]
            guardian.specialization_id = int(choice_id)
            guardian.nivel_id = first_level.id 
            guardian.last_spec_change_at = datetime.utcnow() 

            db.session.flush()
            db.session.commit()
            
            flash(f'Protocolo {chosen_spec.name} iniciado! Próxima troca disponível em {cfg_days} dias.', 'success')
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