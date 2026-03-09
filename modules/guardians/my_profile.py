from collections import defaultdict
from datetime import datetime, date, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from flask import jsonify, render_template, redirect, url_for, request, flash, session
from modules.guardians.missions_logic import get_or_create_active_quest_set
from modules.login.decorators import login_required
from modules.login.session_manager import SessionManager
from application.models import (db, Guardians, HistoricoAcao, NivelSeguranca, GuardianFeatured,
                                QuizAttempt, Specialization, AchievementCategory,
                                TermoAttempt, AnagramAttempt, SpecializationPerkLevel, GuardianInsignia, 
                                Perk, ShopItem, GuardianPurchase, PasswordAttempt)
from .logic import (
    get_global_setting, calculate_week_days_status, get_effective_streak_percentage, get_insignia_category, get_streak_cap, toggle_cosmetic, get_active_avatar_bg)
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
    # ── MAPA DE TIPOS ────────────────────────────────────────────
    # (stat_class, bootstrap_icon, categoria_totalizador)
    STAT_MAP = {
        'GCOIN_BONUS_PCT':      ('stat-gold', 'bi-coin',             'MOEDAS'),
        'QUIZ_BONUS_PCT':       ('stat-int',  'bi-lightning-charge', 'QUIZ'),
        'PATROL_BONUS_PCT':     ('stat-def',  'bi-shield-check',     'PATRULHA'),
        'CODEGAME_BONUS_PCT':   ('stat-mini', 'bi-controller',       'MINIGAMES'),
        'ANAGRAM_BONUS_PCT':    ('stat-mini', 'bi-puzzle',           'MINIGAMES'),
        'TERMO_BONUS_PCT':      ('stat-mini', 'bi-keyboard',         'MINIGAMES'),
        # GERAL: condicional de skill (vale para quiz E minigame)
        'PERFECTION_BONUS_PCT': ('stat-dex',  'bi-bullseye',         'GERAL'),
        'SPEED_BONUS_PCT':      ('stat-dex',  'bi-speedometer2',     'GERAL'),
        # Streak (dinâmico — não entra como pct fixo no totalizador)
        'STREAK_BONUS_PCT':     ('stat-str',  'bi-fire',             'OFENSIVA'),
        # Global score (bônus sobre tudo ganho)
        'GLOBAL_SCORE_PCT':     ('stat-all',  'bi-globe2',           'GLOBAL'),
        'DEFAULT':              ('stat-all',  'bi-caret-up-fill',    'GERAL'),
    }

    # Ordem das zonas na grade e no totalizador
    ZONE_ORDER = ['MOEDAS', 'QUIZ', 'MINIGAMES', 'PATRULHA', 'GERAL', 'GLOBAL']

    # Metadados de exibição por zona
    ZONE_META = {
        'MOEDAS':    ('bi-coin',             'stat-gold', 'Moedas'),
        'QUIZ':      ('bi-lightning-charge', 'stat-int',  'Quiz'),
        'MINIGAMES': ('bi-controller',       'stat-mini', 'Minigames'),
        'PATRULHA':  ('bi-shield-check',     'stat-def',  'Patrulha'),
        'GERAL':     ('bi-bullseye',         'stat-dex',  'Geral'),
        'GLOBAL':    ('bi-globe2',           'stat-all',  'Global'),
    }

    # Agrupa slots por zona: { 'QUIZ': [...], 'MOEDAS': [...], ... }
    grouped_slots = {zone: [] for zone in ZONE_ORDER}
    power_totals  = {}

    def _add_slot(perk_code, value, display_name, source_tag):
        style, icon, target = STAT_MAP.get(perk_code, STAT_MAP['DEFAULT'])
        val_num = float(value)
        val_display = int(val_num) if val_num == int(val_num) else val_num
        suffix = "%" if '_PCT' in perk_code else ""

        bucket = grouped_slots.get(target)
        if bucket is None:
            # zona inesperada → cria dinamicamente e adiciona ao ZONE_ORDER
            grouped_slots[target] = []
            bucket = grouped_slots[target]

        bucket.append({
            'stat_class': style,
            'icon':       icon,
            'value_str':  f"+{val_display}{suffix}",
            'name':       display_name,
            'source':     source_tag,
            'target':     target,
        })

        if '_PCT' in perk_code and perk_code != 'STREAK_BONUS_PCT':
            power_totals[target] = power_totals.get(target, 0) + int(val_display)

    # ── 0. STREAK ────────────────────────────────────────────────
    streak_html = ""
    if perfil.current_streak and perfil.current_streak > 0:
        dynamic_cap  = get_streak_cap(perfil)
        streak_pct   = effective_streak_percent
        bar_width    = int((streak_pct / dynamic_cap) * 100) if dynamic_cap > 0 else 0
        power_totals['GLOBAL'] = power_totals.get('GLOBAL', 0) + streak_pct

        streak_html = f"""
        <div class="buff-section-label">
            <i class="bi bi-fire stat-str"></i>SISTEMA — OFENSIVA DIÁRIA
        </div>
        <div class="buff-streak-block mb-3">
            <div class="buff-streak-fire"><i class="bi bi-fire"></i></div>
            <div class="buff-streak-info">
                <div class="buff-streak-label">
                    Streak Ativo &mdash; {perfil.current_streak} dias consecutivos
                </div>
                <div class="buff-streak-bar-wrap">
                    <div class="buff-streak-bar-fill" style="width:{bar_width}%"></div>
                </div>
                <div class="buff-streak-caps">
                    <span>0%</span><span>CAP: {dynamic_cap}%</span>
                </div>
            </div>
            <div class="buff-streak-val">
                <div class="buff-streak-pct">+{streak_pct}%</div>
                <div class="buff-streak-target">GLOBAL</div>
            </div>
        </div>"""

    # ── 1. PERKS DE ESPECIALIZAÇÃO ───────────────────────────────
    if perfil.specialization_id and perfil.nivel_id:
        perk_entries = db.session.query(SpecializationPerkLevel)\
            .join(Perk).filter(
                SpecializationPerkLevel.specialization_id == perfil.specialization_id,
                SpecializationPerkLevel.level == perfil.nivel.level_number
            ).options(joinedload(SpecializationPerkLevel.perk)).all()

        for entry in perk_entries:
            _add_slot(entry.perk.perk_code, entry.bonus_value,
                      entry.perk.name, "CAMINHO")

    # ── 2. INSÍGNIAS ─────────────────────────────────────────────
    if perfil.featured_associations:
        for assoc in perfil.featured_associations:
            ins = assoc.insignia
            if ins and ins.bonus_value:
                _add_slot(ins.bonus_type or 'DEFAULT', ins.bonus_value,
                          ins.nome, "INSÍGNIA")

    # ── 3. ITENS DA LOJA ─────────────────────────────────────────
    try:
        shop_bonuses = db.session.query(ShopItem)\
            .join(GuardianPurchase, ShopItem.id == GuardianPurchase.item_id)\
            .filter(
                GuardianPurchase.guardian_id == perfil.id,
                ShopItem.bonus_value > 0,
                ShopItem.bonus_type.isnot(None),
                (GuardianPurchase.expires_at == None) |
                (GuardianPurchase.expires_at > datetime.utcnow())
            ).all()

        for item in shop_bonuses:
            if 'TOKEN' in (item.bonus_type or '') or item.category == 'Consumíveis':
                continue
            _add_slot(item.bonus_type, item.bonus_value, item.name, "LOJA")
    except Exception as e:
        print(f"Erro helper buff shop: {e}")

    # ── RENDERIZAÇÃO: GRADE AGRUPADA ─────────────────────────────
    SOURCE_BADGE = {
        'CAMINHO':  ('bi-diagram-3', ''),
        'INSÍGNIA': ('bi-award',     ''),
        'LOJA':     ('bi-bag',       ''),
    }

    def _render_slot(slot):
        badge_icon, badge_label = SOURCE_BADGE.get(slot['source'], ('bi-circle', '???'))
        return f"""
        <div class="buff-slot {slot['stat_class']}" title="{slot['source']}: {slot['name']}">
            <span class="buff-slot-badge">
                <i class="bi {badge_icon}"></i> {badge_label}
            </span>
            <i class="bi {slot['icon']} buff-slot-icon"></i>
            <span class="buff-slot-value">{slot['value_str']}</span>
            <span class="buff-slot-name">{slot['name']}</span>
        </div>"""

    def _render_empty():
        return """
        <div class="buff-slot slot-empty">
            <i class="bi bi-square-dotted buff-slot-icon"></i>
            <span class="buff-slot-name">—</span>
        </div>"""

    # Itera zonas na ordem definida, pulando as vazias
    all_zones_order = ZONE_ORDER + [z for z in grouped_slots if z not in ZONE_ORDER]
    slots_section_html = ""

    for zone in all_zones_order:
        zone_slots = grouped_slots.get(zone, [])
        if not zone_slots:
            continue

        zone_icon, zone_style, zone_label = ZONE_META.get(
            zone, ('bi-plus', 'stat-all', zone)
        )

        # Renderiza os slots desta zona
        slots_html = "".join(_render_slot(s) for s in zone_slots)

        # Preenche até fechar a linha (múltiplo de 3)
        remainder = len(zone_slots) % 3
        if remainder:
            slots_html += _render_empty() * (3 - remainder)

        slots_section_html += f"""
        <div class="buff-zone-label">
            <i class="bi {zone_icon} {zone_style}"></i>{zone_label}
        </div>
        <div class="buff-slot-grid mb-3">
            {slots_html}
        </div>"""

    if not slots_section_html:
        slots_section_html = """
        <div class="p-3 text-center buff-section-label justify-content-center">
            NENHUM FRAGMENTO EQUIPADO
        </div>"""

    slots_block = f"""
    <div class="buff-section-label mt-1">
        <i class="bi bi-grid-3x3" style="opacity:0.4"></i>FRAGMENTOS EQUIPADOS
    </div>
    {slots_section_html}"""

    # ── RENDERIZAÇÃO: TOTALIZADOR ─────────────────────────────────
    total_sum = 0
    power_rows_html = ""

    for zone in all_zones_order:
        if zone not in power_totals:
            continue
        pct_value = power_totals[zone]
        zone_icon, zone_style, zone_label = ZONE_META.get(
            zone, ('bi-plus', 'stat-all', zone)
        )
        total_sum += pct_value
        power_rows_html += f"""
        <div class="buff-power-row">
            <span class="buff-power-label">
                <i class="bi {zone_icon} {zone_style}"></i>{zone_label.upper()}
            </span>
            <span class="buff-power-amount {zone_style}">+{pct_value}%</span>
        </div>"""

    if not power_rows_html:
        power_rows_html = """
        <div class="p-3 text-center buff-section-label justify-content-center">
            NENHUM MODIFICADOR PERCENTUAL ATIVO
        </div>"""

    power_section = f"""
    <div class="buff-section-label">
        <i class="bi bi-sigma" style="opacity:0.4"></i>PODER ACUMULADO
    </div>
    <div class="buff-power-total">
        {power_rows_html}
        <div class="buff-power-footer">
            <span class="buff-power-footer-label">
                <i class="bi bi-cpu me-2"></i>Índice de Poder Total
            </span>
            <span class="buff-power-footer-value">+{total_sum}%</span>
        </div>
    </div>"""

    # ── MODAL HTML FINAL ──────────────────────────────────────────
    has_content = any(grouped_slots.get(z) for z in all_zones_order)
    if not has_content and not streak_html:
        modal_html = """
        <div class='p-4 text-center buff-section-label justify-content-center'>
            NENHUM MODIFICADOR DE SISTEMA ATIVO.
        </div>"""
    else:
        modal_html = streak_html + slots_block + power_section

    # ── MINI CARD HTML ────────────────────────────────────────────
    mini_stats_html = ""
    mini_categories = [(z, power_totals[z]) for z in all_zones_order if z in power_totals]

    for zone_name, pct_value in mini_categories[:6]:
        zone_icon, zone_style, zone_label = ZONE_META.get(
            zone_name, ('bi-plus', 'stat-all', zone_name)
        )
        mini_stats_html += f"""
        <div class="buff-mini-stat">
            <span class="buff-mini-val {zone_style}">+{pct_value}%</span>
            <span class="buff-mini-key">{zone_label}</span>
        </div>"""

    shown = len(mini_categories[:6])
    for _ in range((3 - shown % 3) % 3):
        mini_stats_html += """
        <div class="buff-mini-stat">
            <span class="buff-mini-val" style="color:#2a2f38">—</span>
            <span class="buff-mini-key" style="color:#2a2f38">livre</span>
        </div>"""

    mini_html = f"""
    <div class="buff-mini-wrap">
        <div class="buff-mini-header">
            <span class="buff-mini-title">
                <i class="bi bi-cpu me-1"></i>Modificadores Ativos
            </span>
            <button class="btn-cyber btn-sm font-tech"
                    style="font-size:0.6rem; padding:4px 10px; letter-spacing:1px;"
                    data-bs-toggle="modal" data-bs-target="#statusWindowModal">
                Ver Tudo <i class="bi bi-arrow-up-right"></i>
            </button>
        </div>
        <div class="buff-mini-grid">
            {mini_stats_html}
        </div>
        <div class="buff-mini-total">
            <span class="buff-mini-total-label">
                <i class="bi bi-sigma me-1"></i>Poder Total
            </span>
            <span class="buff-mini-total-val">+{total_sum}%</span>
        </div>
    </div>"""

    return {'modal': modal_html, 'mini': mini_html}


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
    active_perks_data = generate_active_buffs_html(perfil, effective_streak_percent)

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
        if item.category in ('Consumíveis', 'Cosméticos'): 
            continue
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
    logged_guardian = perfil if is_own_profile else Guardians.query.filter_by(user_id=logged_in_user_id).first()
    assistant_payload = get_assistant_data(perfil, 'meu_perfil', viewer=logged_guardian)

    #cosméticos
    active_avatar_bg = get_active_avatar_bg(perfil.id)
    cosmetic_purchases = GuardianPurchase.query.join(ShopItem).filter(GuardianPurchase.guardian_id == perfil.id,ShopItem.category == 'Cosméticos').options(joinedload(GuardianPurchase.item)).all()

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
        active_perks_data=active_perks_data,
        
        # Missões e Specs
        quest_set=quest_set,
        active_missions=active_missions,
        spec_is_locked_time=spec_is_locked_time, 
        spec_days_remaining=spec_days_remaining,
        spec_is_locked_xp=spec_is_locked_xp,
        min_xp_required=cfg_xp,
        user_xp=(perfil.score_atual or 0),
        
        #assistente
        assistant_data=assistant_payload,

        #toggle de cosméticos
        active_avatar_bg=active_avatar_bg,
        cosmetic_purchases=cosmetic_purchases
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



# C.1 — Nova rota de toggle
def toggle_cosmetic(guardian_id: int, purchase_id: int) -> dict:
    purchase = GuardianPurchase.query.get(purchase_id)

    if not purchase or purchase.guardian_id != guardian_id:
        return {'success': False, 'message': 'Item não encontrado.'}

    if not purchase.item.cosmetic_slot:
        return {'success': False, 'message': 'Item não é um cosmético válido.'}

    slot = purchase.item.cosmetic_slot

    if purchase.is_cosmetic_active:
        # Toggle OFF
        purchase.is_cosmetic_active = False
        db.session.commit()
        return {'success': True, 'is_active': False}
    else:
        # ── CORREÇÃO: busca e desativa um a um, sem join no update ──
        purchases_to_deactivate = GuardianPurchase.query.join(ShopItem).filter(
            GuardianPurchase.guardian_id == guardian_id,
            GuardianPurchase.is_cosmetic_active == True,
            ShopItem.cosmetic_slot == slot
        ).all()  # ← traz os objetos primeiro

        for p in purchases_to_deactivate:
            p.is_cosmetic_active = False  # ← atualiza cada um individualmente

        # Ativa o escolhido
        purchase.is_cosmetic_active = True
        db.session.commit()
        return {'success': True, 'is_active': True}

@guardians_bp.route('/cosmetic/toggle/<int:purchase_id>', methods=['POST'])
@login_required
def toggle_cosmetic_route(purchase_id):
    user_id = session.get('user_id')
    guardian = Guardians.query.filter_by(user_id=user_id).first()
    if not guardian:
        return redirect(url_for('guardians_bp.meu_perfil'))

    result = toggle_cosmetic(guardian.id, purchase_id)  # ← .id aqui
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    flash('Cosmético atualizado.', 'success')
    return redirect(url_for('guardians_bp.meu_perfil'))


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