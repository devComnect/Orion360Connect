# modules/guardians/admin_refactored_routes.py
import os, random, io, csv
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from modules.login.decorators import  guardian_admin_required
from collections import defaultdict
from .logic import atualizar_nivel_usuario
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, case, text, desc
import re, uuid
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from . import admin_v2_bp
from modules.guardians.password_game_rules import PASSWORD_RULES_DB
from application.models import (db, Guardians, NivelSeguranca, Specialization, EventoPontuacao, 
                                Insignia, HistoricoAcao, GuardianInsignia, QuizAttempt, UserAnswer, 
                                TermoAttempt, AnagramAttempt, Specialization, GameSeason, NivelSeguranca, 
                                Perk, FeedbackReport, SpecializationPerkLevel, GlobalGameSettings, Quiz,
                                TermoGame, AnagramGame, QuizCategory, Question, AnswerOption, AnagramWord,
                                MissionCodeEnum, MissionTemplate, WeeklyQuestSet, ShopItem, GuardianPurchase, 
                                PasswordGameConfig, PasswordAttempt, GuardianShopState, MissionTypeEnum, MissionDifficultyEnum)
## FIM DE IMPORTS ##

#EXTENSOES PERMITIDAS PARA UPLOAD DE ARQUIVO
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#END#

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

# Rota principal do novo admin (/admin-v2/)
@admin_v2_bp.route('/')
@guardian_admin_required
def guardian_hub():
    """ Nova página principal do admin (Hub de Guardiões). """
    
    try:
        guardians_list = Guardians.query.options(
            joinedload(Guardians.specialization),
            joinedload(Guardians.nivel)
        ).order_by(Guardians.nome.asc()).all()
        
        all_guardian_insignias = GuardianInsignia.query.options(
            joinedload(GuardianInsignia.insignia) 
        ).all()
        
        grouped_insignias = defaultdict(list)
        for gi in all_guardian_insignias:
            grouped_insignias[gi.guardian_id].append(gi)

    except Exception as e:
        print(f"Erro ao buscar lista de guardiões: {e}")
        flash('Erro ao carregar lista de guardiões.', 'danger')
        guardians_list = []
        grouped_insignias = defaultdict(list)

    eventos_pontuacao = EventoPontuacao.query.order_by(EventoPontuacao.nome.asc()).all()
    todas_as_conquistas = Insignia.query.order_by(Insignia.nome.asc()).all()
    all_specializations = Specialization.query.order_by(Specialization.name.asc()).all()

    return render_template(
        'guardians/admin_guardians.html',
        guardians=guardians_list,
        eventos=eventos_pontuacao,
        insignias=todas_as_conquistas,
        grouped_insignias=grouped_insignias,
        specializations=all_specializations
    )

# Rota edição geral de perfil
@admin_v2_bp.route('/edit-guardian-submit', methods=['POST'])
@guardian_admin_required
def edit_guardian_submit():
    """ Processa o POST do modal de Edição de Perfil. """
    
    perfil_id = request.form.get('perfil_id') 
    perfil_guardian = Guardians.query.get(perfil_id)

    if perfil_guardian:
        try:
            perfil_guardian.score_atual = int(request.form.get('score_atual'))
            perfil_guardian.departamento_nome = request.form.get('departamento')
            perfil_guardian.is_admin = 'is_admin' in request.form
            perfil_guardian.opt_in_real_name_ranking = 'opt_in_ranking' in request.form
            spec_id = request.form.get('specialization_id')
            perfil_guardian.specialization_id = int(spec_id) if spec_id else None
            perfil_guardian.nickname = request.form.get('nickname')
            perfil_guardian.is_anonymous = 'is_anonymous' in request.form
            perfil_guardian.retake_tokens = int(request.form.get('retake_tokens'))
            perfil_guardian.minigame_retake_tokens = int(request.form.get('minigame_retake_tokens'))
            perfil_guardian.perfect_quiz_cumulative_count = int(request.form.get('perfect_quiz_cumulative_count'))
            perfil_guardian.guardian_coins = int(request.form.get('moedas', 0))

            if 'current_streak' in request.form:
                nova_ofensiva_str = request.form.get('current_streak')
                if nova_ofensiva_str:
                    nova_ofensiva_int = int(nova_ofensiva_str)

                    if nova_ofensiva_int != (perfil_guardian.current_streak or 0):
                        descricao = f"Ofensiva ajustada de {perfil_guardian.current_streak or 0} para {nova_ofensiva_int} dias pelo administrador."
                        novo_historico = HistoricoAcao(guardian_id=perfil_guardian.id, descricao=descricao, pontuacao=0)
                        db.session.add(novo_historico)

                    perfil_guardian.current_streak = nova_ofensiva_int
                    perfil_guardian.last_streak_date = date.today() if nova_ofensiva_int > 0 else None

            db.session.add(perfil_guardian)

            level_up, novas_conquistas = atualizar_nivel_usuario(perfil_guardian)
            if level_up and perfil_guardian.nivel:
                flash(f"{perfil_guardian.nome} subiu para o nível {perfil_guardian.nivel.nome}!", 'info')
            for conquista_nome in novas_conquistas:
                flash(f"{perfil_guardian.nome} desbloqueou a conquista: {conquista_nome}!", "success")

            db.session.commit()
            flash(f"Perfil de {perfil_guardian.nome} atualizado com sucesso!", 'success')

        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro ao atualizar o perfil: {e}", "danger")
    else:
        flash("Perfil de colaborador não encontrado.", 'danger')
        
    return redirect(url_for('admin_v2_bp.guardian_hub'))

# Rota para lancar pontuacao
@admin_v2_bp.route('/launch-score', methods=['POST'])
@guardian_admin_required
def launch_score():
    """ Processa o modal de Lançar Pontuação. """
    try:
        # Pega IDs - nomes correspondem ao NOVO HTML
        guardian_id = request.form.get('guardian_id')
        evento_id = request.form.get('evento_id')
        nota_admin = request.form.get('nota_admin')
        
        perfil_guardian = Guardians.query.get(guardian_id)
        evento_selecionado = EventoPontuacao.query.get(evento_id)

        if perfil_guardian and evento_selecionado:
            final_points = evento_selecionado.pontuacao
            perfil_guardian.score_atual = (perfil_guardian.score_atual or 0) + final_points
            
            descricao = f"Evento Admin: {evento_selecionado.nome}"
            if nota_admin:
                descricao += f" (Obs: {nota_admin})"
            
            novo_historico = HistoricoAcao(
                guardian_id=guardian_id,
                descricao=descricao,
                pontuacao=final_points
            )
            db.session.add(novo_historico)
            db.session.add(perfil_guardian)
            
            level_up, novas_conquistas = atualizar_nivel_usuario(perfil_guardian)
            db.session.commit() # Commit das mudanças
            
            flash(f'Pontuação ({final_points} pts) lançada para {perfil_guardian.nome}.', 'success')
            if level_up and perfil_guardian.nivel:
                flash(f"{perfil_guardian.nome} teve seu nível atualizado para {perfil_guardian.nivel.nome}!", 'info')
            for conquista_nome in novas_conquistas:
                flash(f"{perfil_guardian.nome} desbloqueou a conquista: {conquista_nome}!", "info")
            
        else:
            flash("Colaborador ou evento não encontrado.", 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao lançar a pontuação: {e}", 'danger')
        
    return redirect(url_for('admin_v2_bp.guardian_hub')) 

# rota para lancar conquista
@admin_v2_bp.route('/launch-achievement', methods=['POST'])
@guardian_admin_required
def launch_achievement():
    """ Processa o modal de Lançar Conquista. """
    try:
        guardian_id = request.form.get('guardian_id')
        insignia_id = request.form.get('insignia_id')
        
        perfil_guardian = Guardians.query.get(guardian_id)
        insignia = Insignia.query.get(insignia_id)

        if perfil_guardian and insignia:
            ja_possui = GuardianInsignia.query.filter_by(guardian_id=guardian_id, insignia_id=insignia_id).first()
            if not ja_possui:
                nova_conquista = GuardianInsignia(guardian_id=guardian_id, insignia_id=insignia_id)
                db.session.add(nova_conquista)
                
                # Adiciona log de histórico
                novo_historico = HistoricoAcao(
                    guardian_id=guardian_id,
                    descricao=f"Conquistou a insígnia '{insignia.nome}'! (Admin)",
                    pontuacao=0
                )
                db.session.add(novo_historico)
                db.session.commit()
                flash(f'Conquista "{insignia.nome}" concedida a {perfil_guardian.nome}.', 'success')
            else:
                flash(f'{perfil_guardian.nome} já possui a conquista "{insignia.nome}".', 'warning')
        else:
            flash("Colaborador ou insígnia não encontrados.", 'danger')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao conceder insígnia: {e}", "danger")
        
    return redirect(url_for('admin_v2_bp.guardian_hub'))

# rota para remover conquista
@admin_v2_bp.route('/remove-achievement', methods=['POST'])
@guardian_admin_required
def remove_achievement():
    """ 
    Processa o modal de Remover Conquista.
    """
    try:
        guardian_id = request.form.get('guardian_id')
        insignia_id = request.form.get('insignia_id')
        
        print(f"debug console guardian_id: {guardian_id}")
        print(f"debug console insignia_id: {insignia_id}") 

        # A verificação agora é por 'insignia_id'
        if not guardian_id or not insignia_id:
            flash('ID do Guardião ou da Conquista inválido.', 'danger')
            return redirect(url_for('admin_v2_bp.guardian_hub'))

        # Busca pela chave composta (lógica antiga e robusta)
        conquista_para_remover = GuardianInsignia.query.filter_by(
            guardian_id=guardian_id, 
            insignia_id=insignia_id  # <<< MUDANÇA AQUI
        ).first()

        if conquista_para_remover:
            nome_insignia = conquista_para_remover.insignia.nome
            nome_guardian = conquista_para_remover.guardian.nome
            
            db.session.delete(conquista_para_remover)
            
            novo_historico = HistoricoAcao(
                guardian_id=guardian_id,
                descricao=f"Teve a insígnia '{nome_insignia}' removida por um admin.",
                pontuacao=0
            )
            db.session.add(novo_historico)
            
            db.session.commit()
            flash(f"Insígnia '{nome_insignia}' removida de {nome_guardian} com sucesso!", 'success')
        else:
            flash("Conquista não encontrada ou não pertence a este guardião.", 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover insígnia: {e}", "danger")
        
    return redirect(url_for('admin_v2_bp.guardian_hub'))

# rota de resetar historico
@admin_v2_bp.route('/reset-history', methods=['POST'])
@guardian_admin_required
def reset_history():
    """ Processa a ação de Zerar Histórico. """
    try:
        perfil_id = request.form.get('guardian_id')
        perfil_guardian = Guardians.query.get(perfil_id)
        
        if perfil_guardian:
            HistoricoAcao.query.filter_by(guardian_id=perfil_id).delete()
            GuardianInsignia.query.filter_by(guardian_id=perfil_id).delete()
            TermoAttempt.query.filter_by(guardian_id=perfil_id).delete()
            GuardianPurchase.query.filter_by(guardian_id=perfil_id).delete()
            PasswordAttempt.query.filter_by(guardian_id=perfil_id).delete()
            GuardianShopState.query.filter_by(guardian_id=perfil_id).delete()

            quest_sets_to_delete = WeeklyQuestSet.query.filter_by(guardian_id=perfil_id).all()
            for quest_set in quest_sets_to_delete:
                db.session.delete(quest_set)

            attempts_to_delete = QuizAttempt.query.filter_by(guardian_id=perfil_id).all()
            for attempt in attempts_to_delete:
                db.session.delete(attempt)
            
            anagram_attempts_to_delete = AnagramAttempt.query.filter_by(guardian_id=perfil_id).all()
            for attempt in anagram_attempts_to_delete:
                db.session.delete(attempt)
     
            perfil_guardian.score_atual = 0
            perfil_guardian.current_streak = 0
            perfil_guardian.last_streak_date = None
            perfil_guardian.last_patrol_date = None
            perfil_guardian.featured_insignia_id = None
            perfil_guardian.last_spec_change_at = None
            perfil_guardian.perfect_quiz_streak = 0
            perfil_guardian.retake_tokens = 1
            perfil_guardian.minigame_retake_tokens = 1
            perfil_guardian.specialization_id = None
            perfil_guardian.nivel_id = None
            perfil_guardian.perfect_quiz_cumulative_count = 0
            perfil_guardian.perfect_minigame_cumulative_count = 0
            perfil_guardian.name_color = None
            perfil_guardian.trophy_tier = None 
            perfil_guardian.featured_insignia_id = None
            
            
            db.session.commit()
            flash(f"O progresso de {perfil_guardian.nome} foi completamente zerado.", 'success')
        else:
            flash("Perfil de colaborador não encontrado.", 'danger')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao zerar o histórico: {e}", 'danger')

    return redirect(url_for('admin_v2_bp.guardian_hub'))

# rota de feedbacks
@admin_v2_bp.route('/feedback', methods=['GET', 'POST'])
@guardian_admin_required
def feedback_hub():
    """
    Novo Hub de Gerenciamento de Feedback, integrado ao Admin v2.
    """
    
    if request.method == 'POST':
        action = request.form.get('action')
        report_id = request.form.get('report_id')
        report = FeedbackReport.query.get(report_id)

        if not report:
            flash('Reporte de feedback não encontrado.', 'danger')
            return redirect(url_for('admin_v2_bp.feedback_hub', **request.args))

        try:
            if action == 'toggle_resolved':
                report.is_resolved = not report.is_resolved # Alterna o status
                db.session.commit()
                status_text = "resolvido" if report.is_resolved else "não resolvido"
                flash(f'Reporte #{report_id} marcado como {status_text}.', 'success')

            elif action == 'delete_feedback':
                if report.attachment_path:
                    try:
                        file_path = os.path.join(current_app.root_path, 'static', report.attachment_path)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Aviso: Não foi possível deletar o anexo {report.attachment_path}. Erro: {e}")
                
                db.session.delete(report)
                db.session.commit()
                flash(f'Reporte #{report_id} excluído com sucesso.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro: {e}', 'danger')

        return redirect(url_for('admin_v2_bp.feedback_hub', **request.args))

    
    filter_status = request.args.get('filter_status', 'unresolved') # Padrão: Não Resolvidos
    filter_type = request.args.get('filter_type', 'all') 
    filter_guardian = request.args.get('filter_guardian', '') 
    filter_sort = request.args.get('filter_sort', 'newest') 

    query = FeedbackReport.query.join(Guardians, FeedbackReport.guardian_id == Guardians.id).options(
        joinedload(FeedbackReport.guardian) # Carrega o guardião junto
    )

    if filter_status == 'unresolved':
        query = query.filter(FeedbackReport.is_resolved == False)
    elif filter_status == 'resolved':
        query = query.filter(FeedbackReport.is_resolved == True)

    if filter_type in ['BUG', 'SUGGESTION']:
        query = query.filter(FeedbackReport.report_type == filter_type)

    if filter_guardian:
        search_term = f'%{filter_guardian}%'
        query = query.filter(
            Guardians.nome.ilike(search_term) |
            Guardians.nickname.ilike(search_term)
        )

    if filter_sort == 'oldest':
        query = query.order_by(FeedbackReport.created_at.asc())
    else: 
        query = query.order_by(FeedbackReport.created_at.desc())

    reports = query.all()
    
    current_filters = {
        'filter_status': filter_status,
        'filter_type': filter_type,
        'filter_guardian': filter_guardian,
        'filter_sort': filter_sort
    }

    return render_template(
        'guardians/admin_feedback_hub.html', 
        reports=reports, 
        current_filters=current_filters
    )

# func para calculos do grafico de GSI (SKILL)
def calculate_gsi_for_all():
    """ 
    Helper para calcular o GSI (0-1000).
    Versão Final: Corrige a falta de 'is_won' em AnagramAttempt e QuizAttempt.
    """
    try:
        guardians = Guardians.query.all()
        if not guardians:
            return {'<500':0, '500-750':0, '750-900':0, '900+':0}, []

        max_xp = max([g.score_atual or 0 for g in guardians]) or 1
        total_quizzes_active = Quiz.query.count() or 1 
        
        gsi_data = []

        for g in guardians:
            score = g.score_atual or 0
            streak = g.current_streak or 0
            
            # --- 1. XP Relativo (300 pts) ---
            xp_score = (score / max_xp) * 300
            
            # --- 2. Precisão em Quizzes (250 pts) ---
            # Usa perfect_quiz_cumulative_count como indicador de qualidade
            quiz_attempts_count = QuizAttempt.query.filter_by(guardian_id=g.id).count()
            perfect_quizzes = g.perfect_quiz_cumulative_count or 0
            
            if quiz_attempts_count > 0:
                ratio_perfect = perfect_quizzes / quiz_attempts_count
                quiz_acc_score = (ratio_perfect * 150) + min(100, quiz_attempts_count * 5)
            else:
                quiz_acc_score = 0

            # --- 3. Hacking Skills (200 pts) ---
            # Termo e Password tem is_won. Anagrama usa final_score > 0.
            
            termo_wins = TermoAttempt.query.filter_by(guardian_id=g.id, is_won=True).count()
            pass_wins = PasswordAttempt.query.filter_by(guardian_id=g.id, is_won=True).count()
            
            # CORREÇÃO AQUI: Anagrama conta como vitória se pontuou algo
            anagram_wins = AnagramAttempt.query.filter(
                AnagramAttempt.guardian_id == g.id, 
                AnagramAttempt.final_score > 0
            ).count()
            
            total_hack_wins = termo_wins + pass_wins + anagram_wins
            
            # Meta: 15 vitórias em minigames para pontuação máxima neste quesito
            hack_score = min(200, (total_hack_wins / 15) * 200)

            # --- 4. Engajamento (150 pts) ---
            eng_rate = 0
            if total_quizzes_active > 0:
                eng_rate = min(1.0, quiz_attempts_count / total_quizzes_active)
            eng_score = eng_rate * 150

            # --- 5. Streak (100 pts) ---
            streak_score = min(100, (streak / 15) * 100)

            # --- TOTAL ---
            final_gsi = int(xp_score + quiz_acc_score + hack_score + eng_score + streak_score)
            final_gsi = min(1000, final_gsi)
            
            gsi_data.append({
                'name': g.nome,
                'gsi': final_gsi,
                'rate': f"{int(eng_rate*100)}%", 
                'active': 'Sim' if streak > 0 else 'Não'
            })

        # Distribuição
        dist = {'<500': 0, '500-750': 0, '750-900': 0, '900+': 0}
        for d in gsi_data:
            s = d['gsi']
            if s < 500: dist['<500'] += 1
            elif s < 750: dist['500-750'] += 1
            elif s < 900: dist['750-900'] += 1
            else: dist['900+'] += 1

        gsi_data.sort(key=lambda x: x['gsi'], reverse=True)
        
        return dist, gsi_data[:5]

    except Exception as e:
        print(f"Erro interno no calculo GSI: {e}")
        return {'<500': 0, '500-750': 0, '750-900': 0, '900+': 0}, []

# rota de hub de analises
@admin_v2_bp.route('/analytics')
@guardian_admin_required
def analytics_hub():
    """
    Novo Hub de Análises unificado (Visão Geral, Quizzes, Guardiões).
    Controlado por request.args.
    """
    try:
        # 2. Tenta realizar o cálculo
        gsi_dist, gsi_top5 = calculate_gsi_for_all()
    except Exception as e:
        # Se der erro no cálculo, loga e mantém os valores padrão (0)
        print(f"Erro ao calcular GSI: {e}")
        # flash(f"Erro ao gerar métricas GSI: {e}", "warning") # Opcional
    # --- DADOS PARA A ABA 1: VISÃO GERAL ---
    one_month_ago = date.today() - timedelta(days=30)
    active_guardians_count = db.session.query(func.count(HistoricoAcao.guardian_id.distinct())).filter(HistoricoAcao.data_evento >= one_month_ago).scalar()
    total_quizzes_answered = QuizAttempt.query.count()
    avg_score_result = db.session.query(func.avg(Guardians.score_atual)).scalar()
    avg_score = round(avg_score_result or 0)

    # Métricas de Análise de Risco
    total_clicks_phishing = HistoricoAcao.query.filter(HistoricoAcao.descricao.like('%Queda em Phishing%')).count()
    total_reports_phishing = HistoricoAcao.query.filter(HistoricoAcao.descricao.like('%Reporte de Phishing%')).count()
    
    vulnerable_users = db.session.query(
        Guardians.nome, func.count(HistoricoAcao.id).label('click_count')
    ).join(HistoricoAcao, Guardians.id == HistoricoAcao.guardian_id).filter(
        HistoricoAcao.descricao.like('%Queda em Phishing%')
    ).group_by(Guardians.nome).order_by(desc('click_count')).limit(5).all()

    vulnerable_depts = db.session.query(
        Guardians.departamento_nome, func.count(HistoricoAcao.id).label('click_count')
    ).join(HistoricoAcao, Guardians.id == HistoricoAcao.guardian_id).filter(
        HistoricoAcao.descricao.like('%Queda em Phishing%')
    ).group_by(Guardians.departamento_nome).order_by(desc('click_count')).limit(3).all()

    # --- DADOS PARA A ABA 2: ANÁLISE POR QUIZ ---
    valid_duration = func.timestampdiff(text('SECOND'), QuizAttempt.started_at, QuizAttempt.completed_at)
    safe_duration = case((valid_duration > 0, valid_duration), else_=None)

    query_quizzes = db.session.query(
        Quiz,
        func.count(db.distinct(QuizAttempt.id)).label('total_attempts'),
        func.count(db.distinct(Question.id)).label('question_count'),
        func.sum(QuizAttempt.score).label('total_score'),
        func.sum(Question.points).label('total_possible_points_per_attempt'),
        func.sum(safe_duration).label('total_time'),
        func.count(safe_duration).label('attempts_with_time')
    ).outerjoin(QuizAttempt, Quiz.id == QuizAttempt.quiz_id)\
     .outerjoin(Question, Quiz.id == Question.quiz_id)\
     .group_by(Quiz.id)

    all_quizzes_stats = query_quizzes.all()
    quizzes_info = []
    grand_total_attempts = 0
    grand_total_earned_score = 0
    grand_total_possible_score_for_attempts = 0
    grand_total_time = 0
    grand_total_attempts_with_time = 0

    for quiz, attempts, q_count, total_score, total_possible, total_time, attempts_with_time in all_quizzes_stats:

        actual_total_earned = (total_score / q_count) if q_count and total_score else 0
        actual_total_possible_for_attempts = (total_possible * attempts) if total_possible and attempts else 0
        
        avg_score_percent = (actual_total_earned / actual_total_possible_for_attempts * 100) if actual_total_possible_for_attempts > 0 else 0
        
        avg_time = (total_time / attempts_with_time) if attempts_with_time and total_time else 0
        end_date = quiz.activation_date + timedelta(days=quiz.duration_days - 1)
        
        quizzes_info.append({
            'quiz': quiz, 'total_attempts': attempts, 'question_count': q_count,
            'avg_score_percent': avg_score_percent, 'avg_time': avg_time, 'end_date': end_date
        })
        

        grand_total_attempts += attempts
        grand_total_earned_score += actual_total_earned
        grand_total_possible_score_for_attempts += actual_total_possible_for_attempts
        grand_total_time += total_time or 0
        grand_total_attempts_with_time += attempts_with_time or 0

    general_avg_score = (grand_total_earned_score / grand_total_possible_score_for_attempts * 100) if grand_total_possible_score_for_attempts else 0
    general_avg_time = (grand_total_time / grand_total_attempts_with_time) if grand_total_attempts_with_time else 0
    quizzes_com_tentativas = [q for q in quizzes_info if q['total_attempts'] > 0]
    quizzes_com_tentativas.sort(key=lambda x: (x['avg_score_percent'] or 0))
    quiz_mais_dificil = quizzes_com_tentativas[0]['quiz'].title if quizzes_com_tentativas else 'N/A'
    quiz_mais_facil = quizzes_com_tentativas[-1]['quiz'].title if quizzes_com_tentativas else 'N/A'
    quizzes_info.sort(key=lambda x: x['quiz'].created_at, reverse=True)

    all_guardians = Guardians.query.order_by(Guardians.nome).all()
    guardian_id = request.args.get('guardian_id', type=int)
    selected_user_data = {} 

    if guardian_id:
        perfil = Guardians.query.get_or_404(guardian_id)
        
        user_history = perfil.historico_acoes.order_by(desc(HistoricoAcao.data_evento)).limit(20).all()
        user_achievements = perfil.insignias_conquistadas.all()
        
        user_quiz_attempts = perfil.quiz_attempts.options(
            joinedload(QuizAttempt.quiz).joinedload(Quiz.questions)
        ).order_by(desc(QuizAttempt.completed_at)).all()
        
        total_quizzes_user = len(user_quiz_attempts)
        perfect_quizzes_count = 0
        soma_scores = 0
        total_pontos_possiveis = 0
        
        quiz_performance_list = []

        for attempt in user_quiz_attempts:
            possible_points = 0
            quiz_title = "Quiz Excluído"
            
            if attempt.quiz: 
                quiz_title = attempt.quiz.title
                possible_points = sum(q.points for q in attempt.quiz.questions)
            
            if possible_points > 0 and attempt.score == possible_points:
                perfect_quizzes_count += 1
            
            soma_scores += attempt.score
            total_pontos_possiveis += possible_points

            attempt_percent = (attempt.score / possible_points * 100) if possible_points > 0 else 0
            quiz_performance_list.append({
                'title': quiz_title,
                'score_earned': attempt.score,
                'score_possible': possible_points,
                'percent': attempt_percent
            })

        media_geral_acertos = (soma_scores / total_pontos_possiveis * 100) if total_pontos_possiveis > 0 else 0

        user_avg_time_result = db.session.query(
            func.avg(func.timestampdiff(text('SECOND'), QuizAttempt.started_at, QuizAttempt.completed_at))
        ).filter(QuizAttempt.guardian_id == guardian_id, QuizAttempt.completed_at.isnot(None), valid_duration > 0).scalar()
        user_avg_time = int(user_avg_time_result) if user_avg_time_result else 0
        
        patrol_count = HistoricoAcao.query.filter(
            HistoricoAcao.guardian_id == guardian_id,
            HistoricoAcao.descricao.like('%Patrulha Diária%')
        ).count()
        
        termo_count = TermoAttempt.query.filter_by(guardian_id=guardian_id).count()
        anagram_count = AnagramAttempt.query.filter_by(guardian_id=guardian_id).count()
        
        
        selected_user_data = {
            'perfil': perfil,
            'user_history': user_history,
            'user_achievements': user_achievements,
            'quiz_performance': quiz_performance_list,
            'total_quizzes': total_quizzes_user,
            'perfect_quizzes_count': perfect_quizzes_count,
            'media_geral_acertos': media_geral_acertos,
            'user_avg_time': user_avg_time,
            'patrol_count': patrol_count,
            'total_minigames': total_quizzes_user + termo_count + anagram_count
        }

    return render_template(
        'guardians/admin_analytics_hub.html',
        # Tab 1
        active_guardians=active_guardians_count,
        total_quizzes=total_quizzes_answered,
        total_reports=total_reports_phishing,
        avg_score=avg_score,
        total_clicks_phishing=total_clicks_phishing,
        vulnerable_users=vulnerable_users,
        vulnerable_depts=vulnerable_depts,
        gsi_dist=gsi_dist,
        gsi_top5=gsi_top5,
        # Tab 2
        quizzes_info=quizzes_info,
        total_quiz_attempts_geral=grand_total_attempts,
        quiz_mais_dificil=quiz_mais_dificil,
        quiz_mais_facil=quiz_mais_facil,
        general_avg_score=general_avg_score,
        general_avg_time=general_avg_time,
        # Tab 3
        all_guardians=all_guardians,
        selected_guardian_id=guardian_id,
        selected_user_data=selected_user_data,
        date=date 
    )


# rota de analise individual de cada quiz
@admin_v2_bp.route('/analytics/quiz/<int:quiz_id>')
@guardian_admin_required
def quiz_analysis(quiz_id):
    """
    Exibe a análise detalhada de um único quiz (respostas e estatísticas).
    Integrado ao layout do Admin v2.
    """
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # 1. Query para estatísticas agregadas (Sua lógica antiga)
    analysis_results = db.session.query(
        UserAnswer.question_id,
        Question.question_text,
        UserAnswer.selected_option_id,
        AnswerOption.option_text,
        AnswerOption.is_correct,
        func.count(UserAnswer.id).label('answer_count')
    ).join(Question, UserAnswer.question_id == Question.id)\
     .join(AnswerOption, UserAnswer.selected_option_id == AnswerOption.id)\
     .filter(Question.quiz_id == quiz_id)\
     .group_by(UserAnswer.question_id, Question.question_text, UserAnswer.selected_option_id, AnswerOption.option_text, AnswerOption.is_correct)\
     .order_by(UserAnswer.question_id, AnswerOption.id)\
     .all()
    
    # 2. Query para respostas individuais detalhadas (Sua lógica antiga)
    detailed_responses = db.session.query(
        Question.id.label('question_id'),
        Guardians.nome.label('guardian_name'),
        AnswerOption.option_text.label('answer_text'),
        AnswerOption.is_correct
    ).join(QuizAttempt, Guardians.id == QuizAttempt.guardian_id)\
     .join(UserAnswer, QuizAttempt.id == UserAnswer.quiz_attempt_id)\
     .join(Question, UserAnswer.question_id == Question.id)\
     .join(AnswerOption, UserAnswer.selected_option_id == AnswerOption.id)\
     .filter(QuizAttempt.quiz_id == quiz_id)\
     .order_by(Question.id, Guardians.nome)\
     .all()

    # Estrutura os dados agregados para o template
    structured_analysis = {}
    for row in analysis_results:
        q_id = row.question_id
        if q_id not in structured_analysis:
            structured_analysis[q_id] = {
                'question_text': row.question_text,
                'options': [],
                'total_responses': 0
            }
        structured_analysis[q_id]['options'].append({
            'option_text': row.option_text,
            'count': row.answer_count,
            'is_correct': row.is_correct
        })
        structured_analysis[q_id]['total_responses'] += row.answer_count
    
    # Nova estrutura para as respostas detalhadas (agrupadas por questão)
    structured_detailed = {}
    for row in detailed_responses:
        q_id = row.question_id
        if q_id not in structured_detailed:
            structured_detailed[q_id] = []
        structured_detailed[q_id].append({
            'guardian_name': row.guardian_name,
            'answer_text': row.answer_text,
            'is_correct': row.is_correct
        })

    return render_template('guardians/admin_quiz_analysis.html', 
                           quiz=quiz, 
                           analysis=structured_analysis,
                           detailed_responses=structured_detailed)

# rota de preview para quizzes criados
@admin_v2_bp.route('/admin/quiz/<int:quiz_id>/visualizar')
@guardian_admin_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('guardians/admin_quiz_preview.html', quiz=quiz)

# Rota de configs globais
@admin_v2_bp.route('/configuracoes', methods=['GET', 'POST'])
@guardian_admin_required
def config_hub():
    """
    Página unificada para Configurações, Especializações e Temporadas.
    """
    if request.method == 'POST':
        action = request.form.get('action')
        redirect_hash = '' 

        try:
            # --- Ações da Aba: Configs Globais ---
            if action == 'save_global_settings':
                for key, value in request.form.items():
                    if key == 'action': # Ignora o campo 'action'
                        continue
                    
                    setting = GlobalGameSettings.query.filter_by(setting_key=key).first()
                    if setting:
                        setting.setting_value = value
                
                db.session.commit()
                flash('Configurações do jogo salvas com sucesso!', 'success')
                redirect_hash = '#tab-geral' 

            # --- Ações da Aba: Especializações ---
            elif action == 'create_specialization':
                name = request.form.get('name')
                spec_code = request.form.get('spec_code')
                description = request.form.get('description')
                color_hex = request.form.get('color_hex')
                if not name or not spec_code or not description:
                     flash('Todos os campos são obrigatórios.', 'danger')
                else:
                    new_spec = Specialization(name=name, spec_code=spec_code, description=description, color_hex=color_hex)
                    db.session.add(new_spec)
                    db.session.commit()
                    flash(f'Especialização "{name}" criada!', 'success')
                redirect_hash = '#tab-specializations'

            elif action == 'edit_specialization':
                spec_id = request.form.get('spec_id')
                spec = Specialization.query.get(spec_id)
                if spec:
                    spec.name = request.form.get('name')
                    spec.description = request.form.get('description')
                    spec.color_hex = request.form.get('color_hex')
                    db.session.commit()
                    flash(f'Especialização "{spec.name}" atualizada.', 'success')
                redirect_hash = '#tab-specializations'

            elif action == 'delete_specialization':
                spec_id = request.form.get('spec_id')
                spec = Specialization.query.get(spec_id)
                if spec:
                    guardian_count = Guardians.query.filter_by(specialization_id=spec_id).count()

                    if guardian_count > 0:
                        flash(f'Não é possível excluir "{spec.name}". {guardian_count} guardião(ões) estão neste caminho. Remova-os primeiro.', 'danger')
                    else:
                        try:
                            db.session.delete(spec)
                            db.session.commit()
                            flash(f'Especialização "{spec.name}" excluída com sucesso!', 'success')
                        except Exception as e:
                            db.session.rollback()
                            flash(f'Erro ao excluir. Detalhes: {e}', 'danger')
                else:
                    flash('Especialização não encontrada.', 'danger')
                redirect_hash = '#tab-specializations'

            elif action == 'create_level_for_spec':
                spec_id = request.form.get('spec_id')
                redirect_hash = '#tab-specializations'

                if 'avatar_file' not in request.files or request.files['avatar_file'].filename == '':
                    flash('O campo de imagem do avatar é obrigatório.', 'danger')
                    return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

                file = request.files['avatar_file']
                if file and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        extension = filename.rsplit('.', 1)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}.{extension}"
                        save_path = os.path.join(current_app.root_path, 'static/img/avatares', unique_filename)
                        file.save(save_path)
                        db_path = f'img/avatares/{unique_filename}'

                        novo_nivel = NivelSeguranca(
                            nome=request.form.get('nome'), score_minimo=int(request.form.get('score_minimo')),
                            avatar_url=db_path, level_number=int(request.form.get('level_number')),
                            specialization_id=spec_id 
                        )
                        db.session.add(novo_nivel)
                        db.session.commit()
                        flash("Nível criado com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Erro ao criar nível: {e}", 'danger')
                else:
                    flash('Tipo de arquivo de avatar inválido.', 'danger')
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)
            
            elif action == 'edit_level_for_spec':
                nivel_id = request.form.get('nivel_id')
                nivel = NivelSeguranca.query.get(nivel_id)

                if nivel:
                    redirect_hash = f'#details-for-spec-{nivel.specialization_id}'
                    try:
                        nivel.nome = request.form.get('nome')
                        nivel.score_minimo = int(request.form.get('score_minimo'))
                        nivel.level_number = int(request.form.get('level_number'))

                        if 'avatar_file' in request.files:
                            file = request.files['avatar_file']

                            if file and file.filename != '':
                                if allowed_file(file.filename):
                                    filename = secure_filename(file.filename)
                                    extension = filename.rsplit('.', 1)[1].lower()
                                    unique_filename = f"{uuid.uuid4().hex}.{extension}"
                                    save_path = os.path.join(current_app.root_path, 'static/img/avatares', unique_filename)
                                    file.save(save_path)

                                    old_db_path = nivel.avatar_url
                                    if old_db_path:
                                        try:
                                            old_file_path = os.path.join(current_app.root_path, 'static', old_db_path)
                                            if os.path.exists(old_file_path):
                                                os.remove(old_file_path)
                                        except Exception as ex:
                                            print(f"Não foi possível deletar o avatar antigo: {ex}")

                                    nivel.avatar_url = f'img/avatares/{unique_filename}'
                                else:
                                    flash('Novo arquivo de avatar inválido (tipo não permitido). A imagem não foi alterada.', 'warning')

                        db.session.commit()
                        flash("Nível atualizado com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Erro ao editar nível: {e}", 'danger')
                else:
                    flash("Nível não encontrado para edição.", "danger")

                return redirect(url_for('admin_v2_bp.config_hub') + '#tab-specializations')

            elif action == 'save_perk_levels':
                spec_id = request.form.get('spec_id')
                redirect_hash = '#tab-specializations'
                
                try:
                    # 1. APAGA todos os bônus antigos desta especialização
                    SpecializationPerkLevel.query.filter_by(specialization_id=spec_id).delete()

                    # 2. Pega os novos dados enviados como listas
                    perk_ids = request.form.getlist('perk_id[]')
                    bonus_values = request.form.getlist('bonus_value[]')
                    level_numbers = request.form.getlist('level_number[]')

                    # 3. RECRIA os bônus com base nos dados do formulário
                    for i in range(len(perk_ids)):
                        # Ignora linhas vazias ou inválidas
                        if perk_ids[i] and bonus_values[i] and level_numbers[i]:
                            new_perk_level = SpecializationPerkLevel(
                                specialization_id=spec_id,
                                perk_id=int(perk_ids[i]),
                                level=int(level_numbers[i]),
                                bonus_value=float(bonus_values[i])
                            )
                            db.session.add(new_perk_level)
                    
                    db.session.commit()
                    flash('Bônus dos níveis salvos com sucesso!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao salvar os bônus: {e}', 'danger')
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            elif action == 'delete_level_for_spec':
                level_id = request.form.get('level_id')
                level_to_delete = NivelSeguranca.query.get(level_id)
                if level_to_delete:
                    guardian_count = Guardians.query.filter_by(nivel_id=level_id).count()
                    if guardian_count > 0:
                        flash(f"Não é possível excluir o nível '{level_to_delete.nome}'. {guardian_count} guardião(ões) estão neste nível.", 'danger')
                    else:
                        spec_id_redirect = level_to_delete.specialization_id
                        db.session.delete(level_to_delete)
                        db.session.commit()
                        flash(f"Nível '{level_to_delete.nome}' excluído com sucesso!", 'success')
                        return redirect(url_for('admin_v2_bp.config_hub') + '#tab-specializations')

            # --- Ações da Aba: Temporadas ---
            elif action == 'create_season':
                name = request.form.get('name')
                start_date_str = request.form.get('start_date')
                end_date_str = request.form.get('end_date')
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                rewards_desc = request.form.get('rewards_description_html')
                new_season = GameSeason(name=name, start_date=start_date, end_date=end_date, rewards_description_html=rewards_desc)
                db.session.add(new_season)
                db.session.commit()
                flash(f'Temporada "{name}" criada.', 'success')
                redirect_hash = '#tab-seasons'
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            elif action == 'edit_season':
                season_id = request.form.get('season_id')
                season = GameSeason.query.get(season_id)
                if season:
                    season.name = request.form.get('name')
                    start_date_str = request.form.get('start_date')
                    end_date_str = request.form.get('end_date')
                    season.start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                    season.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                    season.rewards_description_html = request.form.get('rewards_description_html')
                    db.session.commit()
                    flash(f'Temporada "{season.name}" atualizada.', 'success')
                    redirect_hash = '#tab-seasons'
                    return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            elif action == 'delete_season':
                season_id = request.form.get('season_id')
                season = GameSeason.query.get(season_id)
                if season:
                    db.session.delete(season)
                    db.session.commit()
                    flash(f'Temporada "{season.name}" excluída.', 'success')
                redirect_hash = '#tab-seasons'
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            elif action == 'set_active':
                season_id = request.form.get('season_id')
                GameSeason.query.filter(GameSeason.id != season_id).update({'is_active': False})
                season = GameSeason.query.get(season_id)
                season.is_active = True
                db.session.commit()
                flash(f'Temporada "{season.name}" definida como ativa!', 'success')
                redirect_hash = '#tab-seasons'
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            elif action == 'finalize_season':
                season_id = request.form.get('season_id')
                season_to_finalize = GameSeason.query.get(season_id)
                redirect_hash = '#tab-seasons'
                if not season_to_finalize:
                    flash('Temporada não encontrada.', 'danger')
                elif not season_to_finalize.is_active:
                    flash('Apenas a temporada ativa pode ser finalizada.', 'warning')

                # 1. Busca Top 3 Vencedores (Score) e armazena seus dados
                top_3_score = Guardians.query.order_by(Guardians.score_atual.desc()).limit(3).all()
                winners_data = {} 
                position_text_map = {1: '1º Lugar', 2: '2º Lugar', 3: '3º Lugar'}

                for i, guardian in enumerate(top_3_score):
                    tier = i + 1
                    winners_data[guardian.id] = (tier, guardian.score_atual)

                try:
                    UserAnswer.query.delete()
                    QuizAttempt.query.delete()
                    TermoAttempt.query.delete()
                    AnagramAttempt.query.delete()
                    GuardianInsignia.query.delete()
                    HistoricoAcao.query.delete()
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao limpar tabelas da temporada: {e}', 'danger')
                    return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

                reset_values = {
                    Guardians.score_atual: 0,
                    Guardians.current_streak: 0,
                    Guardians.last_streak_date: None,
                    Guardians.last_patrol_date: None,
                    Guardians.specialization_id: None,
                    Guardians.nivel_id: None,
                    Guardians.featured_insignia_id: None,
                    Guardians.perfect_quiz_streak: 0,
                    Guardians.retake_tokens: 1, # Reseta para 1 (ou seu default)
                    Guardians.perfect_quiz_cumulative_count: 0,
                    Guardians.name_color: None
                }
                Guardians.query.update(reset_values)

                if winners_data:
                    for guardian_id, (tier, final_score) in winners_data.items():
                        guardian_to_update = Guardians.query.get(guardian_id)
                        if guardian_to_update:
                            # a) Atualiza o troféu (só se for melhor que um existente)
                            if guardian_to_update.trophy_tier is None or tier < guardian_to_update.trophy_tier:
                                guardian_to_update.trophy_tier = tier
                            
                            # b) Adiciona o novo (e único) log de histórico
                            position_text = position_text_map.get(tier, f'{tier}º Lugar')
                            descricao = f"Finalizou a Temporada '{season_to_finalize.name}' em {position_text} com {final_score} pontos."
                            new_log = HistoricoAcao(
                                guardian_id=guardian_id,
                                descricao=descricao,
                                pontuacao=0 # O log não dá pontos, apenas registra a vitória
                            )
                            db.session.add(guardian_to_update)
                            db.session.add(new_log)

                # 5. Desativa a temporada
                season_to_finalize.is_active = False
                db.session.add(season_to_finalize)

                # 6. Salva todas as mudanças
                db.session.commit()
                flash(f'Temporada "{season_to_finalize.name}" finalizada! Vencedores premiados e pontuações zeradas.', 'success')
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            # ---  Ações da Aba: Eventos ---
            elif action == 'criar_evento':
                nome = request.form.get('nome')
                pontuacao = request.form.get('pontuacao')
                descricao = request.form.get('descricao')
                if not nome or not pontuacao:
                    flash('Nome e pontuação do evento são obrigatórios.', 'danger')
                else:
                    novo_evento = EventoPontuacao(nome=nome, pontuacao=int(pontuacao), descricao=descricao)
                    db.session.add(novo_evento)
                    db.session.commit()
                    flash(f"Evento '{nome}' criado com sucesso!", 'success')
                redirect_hash = '#tab-events' # Aponta para a nova aba

            elif action == 'editar_evento':
                evento_id = request.form.get('evento_id')
                evento = EventoPontuacao.query.get(evento_id)
                if evento:
                    evento.nome = request.form.get('nome')
                    evento.pontuacao = int(request.form.get('pontuacao'))
                    evento.descricao = request.form.get('descricao')
                    db.session.commit()
                    flash(f"Evento '{evento.nome}' atualizado!", 'success')
                else:
                    flash("Evento não encontrado.", 'danger')
                redirect_hash = '#tab-events'

            elif action == 'excluir_evento':
                evento_id = request.form.get('evento_id')
                evento = EventoPontuacao.query.get(evento_id)
                if evento:
                    try:
                        db.session.delete(evento)
                        db.session.commit()
                        flash(f"Evento '{evento.nome}' excluído!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash("Erro: O evento não pode ser excluído (pode estar em uso).", 'danger')
                else:
                    flash("Evento não encontrado.", 'danger')
                redirect_hash = '#tab-events'

            # --- Ações da Aba: Missoes ---
            elif action == 'criar_missao':
                title = request.form.get('title')
                desc_template = request.form.get('description_template')
                mission_code_str = request.form.get('mission_code')
                difficulty_str = request.form.get('difficulty')
                mission_type_str = request.form.get('mission_type')
                min_target = request.form.get('min_target', 1, type=int)
                max_target = request.form.get('max_target', 5, type=int)
                xp_reward = request.form.get('xp_reward', 100, type=int)

                if not title or not desc_template or not mission_code_str:
                    flash('Título, Descrição e Código de Ação são obrigatórios.', 'danger')
                else:
                    mission_code = MissionCodeEnum[mission_code_str] 
                    difficulty = MissionDifficultyEnum[difficulty_str] if difficulty_str else MissionDifficultyEnum.EASY
                    mission_type = MissionTypeEnum[mission_type_str] if mission_type_str else MissionTypeEnum.ACTION
                    nova_missao = MissionTemplate(
                        title=title,
                        description_template=desc_template,
                        difficulty=difficulty,    
                        mission_type=mission_type,
                        mission_code=mission_code,
                        xp_reward=xp_reward,
                        min_target=min_target,
                        max_target=max_target,
                        is_active=True
                    )
                    db.session.add(nova_missao)
                    db.session.commit()
                    flash(f"Modelo de Missão '{title}' criado com sucesso!", 'success')
                redirect_hash = '#tab-missoes' 
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)
            
            elif action == 'editar_missao':
                mission_id = request.form.get('mission_id')
                missao = MissionTemplate.query.get(mission_id)
                
                if missao:
                    try:
                        missao.title = request.form.get('title')
                        missao.description_template = request.form.get('description_template')
                        
                        # Atualiza Enums
                        missao.mission_code = MissionCodeEnum[request.form.get('mission_code')]
                        missao.difficulty = MissionDifficultyEnum[request.form.get('difficulty')]
                        missao.mission_type = MissionTypeEnum[request.form.get('mission_type')]
                        
                        # Atualiza Inteiros
                        missao.xp_reward = request.form.get('xp_reward', type=int)
                        missao.min_target = request.form.get('min_target', 1, type=int)
                        missao.max_target = request.form.get('max_target', 5, type=int)
                        
                        missao.is_active = 'is_active' in request.form
                        
                        db.session.commit()
                        flash(f"Missão '{missao.title}' atualizada com sucesso.", 'success')
                    except KeyError as e:
                        db.session.rollback()
                        flash(f"Erro ao atualizar: Opção inválida selecionada ({e}).", 'danger')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Erro interno: {e}", 'danger')
                else:
                    flash('Missão não encontrada.', 'danger')
                    
                redirect_hash = '#tab-missoes'
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)
            
            elif action == 'excluir_missao':
                mission_id = request.form.get('mission_id')
                missao = MissionTemplate.query.get(mission_id)
                if missao:
                    nome_missao = missao.title
                    db.session.delete(missao)
                    db.session.commit()
                    flash(f"Missão '{nome_missao}' excluída com sucesso.", 'success')
                else:
                    flash('Missão não encontrada.', 'danger')
                redirect_hash = '#tab-missoes'
                return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)

            # --- Ações da Aba: Loja ---
            elif action == 'criar_item_loja':
                nome = request.form.get('name')
                desc = request.form.get('description')
                custo = int(request.form.get('cost', 0))
                categoria = request.form.get('category')
                img_path = request.form.get('image_path')
                bonus_type = request.form.get('bonus_type')
                b_val_input = request.form.get('bonus_value')
                bonus_val = float(b_val_input) if b_val_input else 0.0
                limit = request.form.get('purchase_limit')
                rarity = request.form.get('rarity')
                
                purchase_limit = int(limit) if limit and int(limit) > 0 else None
                dur_input = request.form.get('duration_days')
                duration_days = int(dur_input) if dur_input and int(dur_input) > 0 else None

                novo_item = ShopItem(
                    name=nome, description=desc, cost=custo, category=categoria,
                    image_path=img_path, bonus_type=bonus_type, bonus_value=bonus_val,
                    purchase_limit=purchase_limit, rarity=rarity, is_active=True
                )
                db.session.add(novo_item)
                db.session.commit()
                flash(f"Item '{nome}' adicionado à loja!", 'success')
                redirect_hash = '#tab-loja'

            elif action == 'editar_item_loja':
                item_id = request.form.get('item_id')
                item = ShopItem.query.get(item_id)
                if item:
                    item.name = request.form.get('name')
                    item.description = request.form.get('description')
                    item.cost = int(request.form.get('cost', 0))
                    item.category = request.form.get('category')
                    item.image_path = request.form.get('image_path')
                    item.bonus_type = request.form.get('bonus_type')
                    item.rarity = request.form.get('rarity')
                    b_val_input = request.form.get('bonus_value')
                    item.bonus_value = float(b_val_input) if b_val_input else 0.0
                    limit = request.form.get('purchase_limit')
                    item.purchase_limit = int(limit) if limit and int(limit) > 0 else None
                    dur_input = request.form.get('duration_days')
                    item.duration_days = int(dur_input) if dur_input and int(dur_input) > 0 else None
                    item.is_active = 'is_active' in request.form
                    
                    db.session.commit()
                    flash(f"Item '{item.name}' atualizado.", 'success')
                redirect_hash = '#tab-loja'

            elif action == 'excluir_item_loja':
                item_id = request.form.get('item_id')
                item = ShopItem.query.get(item_id)
                if item:
                    db.session.delete(item)
                    db.session.commit()
                    flash("Item removido da loja.", 'success')
                redirect_hash = '#tab-loja'

        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
            
        return redirect(url_for('admin_v2_bp.config_hub') + redirect_hash)
    
    # Dados para Aba "Configurações Globais" (NOVO)
    all_settings = GlobalGameSettings.query.order_by(GlobalGameSettings.category, GlobalGameSettings.setting_key).all()
    settings_by_category = {}
    for setting in all_settings:
        if setting.category not in settings_by_category:
            settings_by_category[setting.category] = []
        settings_by_category[setting.category].append(setting)

    # Dados para Aba "Especializações"
    specializations = Specialization.query.options(
        joinedload(Specialization.levels),
        joinedload(Specialization.perks).joinedload(SpecializationPerkLevel.perk)
    ).order_by(Specialization.name).all()
    all_perks = Perk.query.order_by(Perk.name).all()

    # Dados para Aba "Temporadas"
    seasons = GameSeason.query.order_by(GameSeason.start_date.desc()).all()
    eventos = EventoPontuacao.query.order_by(EventoPontuacao.nome.asc()).all()

    # Dados para missoes
    mission_templates = MissionTemplate.query.order_by(MissionTemplate.title).all()

    # Dados para shop
    shop_items = ShopItem.query.order_by(ShopItem.category, ShopItem.cost).all()

    return render_template(
        'guardians/admin_config_hub.html',
        settings_by_category=settings_by_category,
        specializations=specializations,
        all_perks=all_perks,
        seasons=seasons,
        eventos=eventos,
        mission_templates=mission_templates,
        mission_codes=MissionCodeEnum,
        shop_items=shop_items,
        achievement_bonus_types=BONUS_TYPES
    )

# Rota de config de conteudos
@admin_v2_bp.route('/conteudo', methods=['GET', 'POST'])
@guardian_admin_required
def content_hub():
    """
    Página unificada para Gerenciamento de Conteúdo (Quizzes, Jogos, Eventos, Conquistas).
    """
    
    if request.method == 'POST':
        action = request.form.get('action')
        redirect_hash = ''

        try:
            # --- Ações da Aba: Quizzes ---
            if action == 'criar_quiz':
                try:
                    # 1. Cria o Objeto Quiz
                    time_limit = request.form.get('time_limit_seconds')
                    novo_quiz = Quiz(
                        title=request.form.get('title'),
                        description=request.form.get('description'),
                        activation_date=datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date(),
                        duration_days=int(request.form.get('duration_days')),
                        category=QuizCategory[request.form.get('category')],
                        time_limit_seconds=int(time_limit) if time_limit else None
                    )
                    db.session.add(novo_quiz)
                    db.session.flush() # Gera o ID do Quiz para usar nas perguntas

                    # 2. Processamento Robusto dos Dados do Formulário
                    perguntas_map = {}

                    for key, value in request.form.items():
                        # Regex 1: Campos diretos da pergunta -> questions[0][question_text]
                        match_q = re.match(r'questions\[(\d+)\]\[(\w+)\]$', key)
                        
                        # Regex 2: Campos das opções -> questions[0][options][0][option_text]
                        match_o = re.match(r'questions\[(\d+)\]\[options\]\[(\d+)\]\[(\w+)\]$', key)

                        if match_q:
                            q_idx, field = match_q.groups()
                            if q_idx not in perguntas_map: perguntas_map[q_idx] = {'options': {}}
                            perguntas_map[q_idx][field] = value
                        
                        elif match_o:
                            q_idx, o_idx, field = match_o.groups()
                            if q_idx not in perguntas_map: perguntas_map[q_idx] = {'options': {}}
                            if o_idx not in perguntas_map[q_idx]['options']: perguntas_map[q_idx]['options'][o_idx] = {}
                            
                            perguntas_map[q_idx]['options'][o_idx][field] = value

                    # 3. Salva no Banco
                    for q_idx, q_data in sorted(perguntas_map.items()):
                        # Defensiva: Usa .get() para evitar o KeyError se o campo vier vazio/faltando
                        q_text = q_data.get('question_text', '').strip()
                        if not q_text:
                            continue
                       

                        nova_pergunta = Question(
                            question_text=q_text,
                            points=int(q_data.get('points', 10)),
                            quiz_id=novo_quiz.id
                        )
                        db.session.add(nova_pergunta)
                        db.session.flush() # Gera ID da Pergunta

                        # Processa as opções desta pergunta
                        options_data = q_data.get('options', {})
                        for o_idx, o_data in sorted(options_data.items()):
                            opt_text = o_data.get('option_text', 'Opção sem texto')
                            
                            # Checkbox: Se 'is_correct' estiver presente no form, é True. Se não, False.
                            # O valor vindo do HTML geralmente é 'true' ou 'on' se marcado.
                            is_correct_val = o_data.get('is_correct')
                            is_correct = True if is_correct_val else False

                            nova_opcao = AnswerOption(
                                option_text=opt_text,
                                is_correct=is_correct,
                                question_id=nova_pergunta.id
                            )
                            db.session.add(nova_opcao)

                    db.session.commit()
                    flash(f'Quiz "{novo_quiz.title}" criado com sucesso!', 'success')
                    redirect_hash = '#tab-quizzes'

                except Exception as e:
                    db.session.rollback()
                    # Log do erro no console para ajudar a debugar se persistir
                    print(f"ERRO CRIAÇÃO QUIZ: {str(e)}")
                    flash(f"Erro ao criar jogo: {e}", "danger")
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)
                    
            elif action == 'excluir_quiz':
                redirect_hash = '#tab-quizzes'
                quiz_id = request.form.get('quiz_id')
                quiz = Quiz.query.get(quiz_id)
                if quiz:
                    try:
                        db.session.delete(quiz)
                        db.session.commit()
                        flash(f"Quiz '{quiz.title}' excluído com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        print(f"--- ERRO AO EXCLUIR QUIZ ---: {e}")
                        flash(f"Erro ao excluir o quiz. Verifique o terminal para mais detalhes.", 'danger')
                else:
                    flash("Quiz não encontrado.", 'danger')        
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)
                
            elif action == 'editar_quiz':
                redirect_hash = '#tab-quizzes'
                quiz_id = request.form.get('quiz_id')
                quiz = Quiz.query.get(quiz_id)

                if quiz:
                    try:
                        quiz.title = request.form.get('title')
                        quiz.description = request.form.get('description')
                        # Atualiza apenas se o campo não estiver vazio
                        if request.form.get('time_limit_seconds'):
                            quiz.time_limit_seconds = int(request.form.get('time_limit_seconds'))
                        
                        quiz.activation_date = datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date()
                        quiz.duration_days = int(request.form.get('duration_days'))
                        quiz.category = QuizCategory[request.form.get('category')]
                        
                        db.session.commit()
                        flash(f'Quiz "{quiz.title}" atualizado com sucesso!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao editar quiz: {e}', 'danger')
                else:
                    flash('Quiz não encontrado.', 'danger')
            
            elif action == 'reset_quiz_attempt':
                redirect_hash = '#tab-quizzes'
                guardian_id = request.form.get('guardian_id')
                quiz_id = request.form.get('quiz_id')
                
                if guardian_id and quiz_id:
                    try:
                        # 1. Busca a tentativa e o quiz
                        attempt = QuizAttempt.query.filter_by(
                            guardian_id=guardian_id, 
                            quiz_id=quiz_id
                        ).first()
                        
                        quiz_obj = Quiz.query.get(quiz_id)
                        
                        if attempt:
                            # 2. LIMPEZA DE HISTÓRICO (Visual)
                            if quiz_obj:
                                logs = HistoricoAcao.query.filter(
                                    HistoricoAcao.guardian_id == guardian_id,
                                    HistoricoAcao.descricao.like(f"%{quiz_obj.title}%")
                                ).all()
                                
                                for log in logs:
                                    db.session.delete(log)

                            # 3. LIMPEZA DE DADOS (Funcional)
                            UserAnswer.query.filter_by(quiz_attempt_id=attempt.id).delete()
                            db.session.delete(attempt)
                            
                            db.session.commit()
                            flash('Tentativa resetada com sucesso. O aluno pode realizar o quiz novamente.', 'success')
                        else:
                            flash('Nenhuma tentativa encontrada para este usuário neste quiz.', 'warning')
                            
                    except Exception as e:
                        db.session.rollback()
                        print(f"Erro no reset: {e}")
                        flash(f'Erro ao resetar: {str(e)}', 'danger')
                else:
                    flash('Dados incompletos.', 'danger')

            elif action == 'import_quizzes_csv':
                redirect_hash = '#tab-quizzes'
                file = request.files.get('csv_file')
                
                if not file or file.filename == '':
                    flash('Nenhum arquivo selecionado.', 'warning')
                elif not file.filename.endswith('.csv'):
                    flash('Formato inválido. Use .csv', 'warning')
                else:
                    try:
                        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                        csv_input = csv.reader(stream)
                        
                        # Pula cabeçalho
                        next(csv_input, None)
                        
                        quizzes_criados = {} # Cache local para agrupar perguntas no mesmo quiz
                        count_quizzes = 0
                        count_questions = 0
                        
                        for row in csv_input:
                            # Validação básica de colunas
                            if len(row) < 9: continue 
                            
                            # Extração dos dados
                            q_title, q_desc, q_date, q_dur, q_time, q_cat = row[0].strip(), row[1], row[2], row[3], row[4], row[5].upper()
                            quest_text, quest_points, opts_raw = row[6], row[7], row[8]
                            
                            # 1. Recupera ou Cria o Quiz (Agrupamento pelo Título)
                            if q_title not in quizzes_criados:
                                # Verifica se categoria é válida
                                category_enum = QuizCategory.COMUM
                                if q_cat in QuizCategory.__members__:
                                    category_enum = QuizCategory[q_cat]
                                    
                                new_quiz = Quiz(
                                    title=q_title,
                                    description=q_desc,
                                    activation_date=datetime.strptime(q_date, '%Y-%m-%d').date(),
                                    duration_days=int(q_dur),
                                    time_limit_seconds=int(q_time) if q_time else None,
                                    category=category_enum
                                )
                                db.session.add(new_quiz)
                                db.session.flush() # Gera o ID do quiz para as perguntas usarem
                                quizzes_criados[q_title] = new_quiz
                                count_quizzes += 1
                            
                            current_quiz = quizzes_criados[q_title]
                            
                            # 2. Cria a Pergunta
                            if quest_text: # Só cria se tiver texto de pergunta
                                new_question = Question(
                                    quiz_id=current_quiz.id,
                                    question_text=quest_text,
                                    points=int(quest_points) if quest_points else 10
                                )
                                db.session.add(new_question)
                                db.session.flush() # Gera ID da pergunta
                                count_questions += 1
                                
                                # 3. Cria as Opções (Parse da string especial)
                                # Formato esperado: "Opção A|1;Opção B|0;Opção C|0"
                                if opts_raw:
                                    options_list = opts_raw.split(';')
                                    for opt_str in options_list:
                                        if '|' in opt_str:
                                            text, is_correct_flag = opt_str.rsplit('|', 1)
                                            is_correct = (is_correct_flag.strip() == '1')
                                            
                                            new_option = AnswerOption(
                                                question_id=new_question.id,
                                                option_text=text.strip(),
                                                is_correct=is_correct
                                            )
                                            db.session.add(new_option)

                        db.session.commit()
                        flash(f'Importação concluída: {count_quizzes} Quizzes e {count_questions} Perguntas criadas!', 'success')
                        
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro crítico na importação: {e}', 'danger')

            # --- Ações da Aba: Termo ---
            elif action == 'create_termo_game':
                redirect_hash = '#tab-termo'
                try:
                    word = request.form.get('correct_word').upper()
                    hint = request.form.get('hint')
                    if not word or not word.isalpha():
                        flash('A palavra deve conter apenas letras.', 'danger')
                    else:
                        new_game = TermoGame(
                            correct_word=word,
                            max_attempts=int(request.form.get('max_attempts')),
                            points_reward=int(request.form.get('points_reward')),
                            time_limit_seconds=int(request.form.get('time_limit_seconds')) if request.form.get('time_limit_seconds') else None,
                            activation_date=datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date(),
                            hint=hint,
                            duration_days=int(request.form.get('duration_days'))
                        )
                        db.session.add(new_game)
                        db.session.commit()
                        flash(f'Novo jogo Termo com a palavra "{word}" criado com sucesso!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Erro ao criar jogo: {e}", "danger")
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'edit_termo_game':
                redirect_hash = '#tab-termo'
                game_id = request.form.get('game_id')
                game = TermoGame.query.get(game_id)
                if game:
                    try:
                        game.correct_word = request.form.get('correct_word').upper()
                        game.max_attempts = int(request.form.get('max_attempts'))
                        game.points_reward = int(request.form.get('points_reward'))
                        time_limit = request.form.get('time_limit_seconds')
                        game.time_limit_seconds = int(time_limit) if time_limit else None
                        game.is_active = 'is_active' in request.form 
                        game.activation_date = datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date()
                        game.duration_days = int(request.form.get('duration_days'))
                        game.hint = request.form.get('hint')
                        db.session.commit()
                        flash('Jogo Termo atualizado com sucesso!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao atualizar o jogo: {e}', 'danger')
                else:
                    flash('Jogo Termo não encontrado.', 'danger')
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'delete_termo_game':
                redirect_hash = '#tab-termo'
                game_id = request.form.get('game_id')
                game = TermoGame.query.get(game_id)
                if game:
                    if game.attempts:
                        flash(f'Não é possível excluir o jogo "{game.correct_word}", pois ele já possui tentativas de usuários. Desative-o se não quiser que ele apareça.', 'warning')
                    else:
                        try:
                            db.session.delete(game)
                            db.session.commit()
                            flash(f'Jogo Termo "{game.correct_word}" excluído com sucesso!', 'success')
                        except Exception as e:
                            db.session.rollback()
                            flash(f'Erro ao excluir o jogo: {e}', 'danger')
                else:
                    flash('Jogo Termo não encontrado.', 'danger')
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'import_termo_csv':
                redirect_hash = '#tab-termo'
                file = request.files.get('csv_file')
                
                if not file or not file.filename.endswith('.csv'):
                    flash('Arquivo inválido. Envie um CSV.', 'warning')
                else:
                    try:
                        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                        csv_input = csv.reader(stream)
                        next(csv_input, None) # Pula cabeçalho
                        
                        count = 0
                        errors = []
                        
                        for row in csv_input:
                            # Layout: Palavra, Dica, Data(Y-m-d), Duracao, Tentativas, Pontos, Tempo
                            if len(row) < 7: continue
                            
                            word = row[0].upper().strip()
                            if not word.isalpha(): 
                                errors.append(f"{word} (inválida)")
                                continue
                                
                            new_game = TermoGame(
                                correct_word=word,
                                hint=row[1],
                                activation_date=datetime.strptime(row[2], '%Y-%m-%d').date(),
                                duration_days=int(row[3]),
                                max_attempts=int(row[4]),
                                points_reward=int(row[5]),
                                time_limit_seconds=int(row[6]) if row[6] else None
                            )
                            db.session.add(new_game)
                            count += 1
                            
                        db.session.commit()
                        msg = f'{count} jogos Termo importados!'
                        if errors: msg += f' Ignorados: {", ".join(errors)}'
                        flash(msg, 'success' if count > 0 else 'warning')
                        
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro na importação: {e}', 'danger')

            # --- Ações da Aba: Anagrama ---
            elif action == 'create_anagram_game':
                redirect_hash = '#tab-anagram'
                try:
                    new_game = AnagramGame(
                        title=request.form.get('title'),
                        description=request.form.get('description'),
                        points_per_word=int(request.form.get('points_per_word')),
                        duration_days=int(request.form.get('duration_days')),
                        time_limit_seconds=int(request.form.get('time_limit_seconds')) if request.form.get('time_limit_seconds') else None,
                        activation_date=datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date(),
                    )
                    db.session.add(new_game)
                    db.session.commit()
                    flash(f'Pacote de Anagrama "{new_game.title}" criado com sucesso! Agora adicione palavras a ele.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao criar pacote: {e}', 'danger')       
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'edit_anagram_game':
                game_id = request.form.get('game_id')
                game = AnagramGame.query.get(game_id)
                redirect_hash = '#tab-anagram'
                if game:
                    try:
                        game.title = request.form.get('title')
                        game.description = request.form.get('description')
                        game.points_per_word = int(request.form.get('points_per_word'))
                        game.duration_days = int(request.form.get('duration_days'))
                        game.is_active = 'is_active' in request.form
                        value = request.form.get('time_limit_seconds')
                        game.time_limit_seconds = int(value) if value else None
                        game.activation_date = datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date()
                        
                        db.session.commit()
                        flash('Jogo de Anagrama atualizado com sucesso!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao atualizar o jogo: {e}', 'danger')
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'delete_anagram_game':
                game_id = request.form.get('game_id')
                game = AnagramGame.query.get(game_id)
                redirect_hash = '#tab-anagram'
                if game:
                    if game.attempts:
                        flash(f'Não é possível excluir o jogo "{game.title}", pois ele já possui tentativas de usuários.', 'warning')
                    else:
                        db.session.delete(game)
                        db.session.commit()
                        flash(f'Jogo de Anagrama "{game.title}" excluído com sucesso!', 'success')
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'add_anagram_word':
                game_id = request.form.get('game_id')
                raw_text = request.form.get('word_text', '').upper()
                redirect_hash = '#tab-anagram' 

                if not game_id or not raw_text:
                    flash('Dados incompletos.', 'danger')
                    return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

                game = AnagramGame.query.get(game_id)
                if not game:
                    flash('Jogo não encontrado.', 'danger')
                    return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

                words_to_process = [w.strip() for w in raw_text.split(';') if w.strip()]
                
                added_count = 0
                skipped_msgs = []

                try:
                    for word_text in words_to_process:
                        if not word_text.isalpha():
                            skipped_msgs.append(f"'{word_text}' (contém símbolos/espaços)")
                            continue
                        
                        if len(word_text) < 3:
                            skipped_msgs.append(f"'{word_text}' (muito curta)")
                            continue

                        exists = AnagramWord.query.filter_by(game_id=game_id, correct_word=word_text).first()
                        if exists:
                            skipped_msgs.append(f"'{word_text}' (já existe)")
                            continue

                        new_word = AnagramWord(
                            game_id=game_id,
                            correct_word=word_text
                        )
                        db.session.add(new_word)
                        added_count += 1

                    if added_count > 0:
                        db.session.commit()
                        flash(f'{added_count} palavra(s) adicionada(s) com sucesso ao pacote "{game.title}"!', 'success')
                    else:
                        flash('Nenhuma palavra válida foi adicionada.', 'warning')

                    if skipped_msgs:
                        flash(f"Algumas palavras foram ignoradas: {', '.join(skipped_msgs)}", 'warning')

                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao processar palavras: {e}', 'danger')
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'delete_anagram_word':
                word_id = request.form.get('word_id')
                redirect_hash = '#tab-anagram'
                
                word = AnagramWord.query.get(word_id)
                if word:
                    try:
                        game_title = word.game.title # Pega o nome para o flash
                        db.session.delete(word)
                        db.session.commit()
                        flash(f'Palavra "{word.correct_word}" removida do jogo "{game_title}".', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao deletar palavra: {e}', 'danger')
                else:
                    flash('Palavra não encontrada.', 'danger')

                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)
            
            elif action == 'import_anagram_csv':
                redirect_hash = '#tab-anagram'
                file = request.files.get('csv_file')
                
                if not file or not file.filename.endswith('.csv'):
                    flash('Arquivo inválido.', 'warning')
                else:
                    try:
                        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                        csv_input = csv.reader(stream)
                        next(csv_input, None)
                        
                        count_games = 0
                        
                        # Dicionário para agrupar palavras por título de jogo
                        # { "Titulo": {dados_jogo, palavras: []} }
                        games_cache = {}
                        
                        for row in csv_input:
                            # Layout: Titulo, Desc, Data, Duracao, Tempo, Pontos/Palavra, PALAVRA
                            if len(row) < 7: continue
                            
                            title = row[0].strip()
                            word_text = row[6].upper().strip()
                            
                            if title not in games_cache:
                                games_cache[title] = {
                                    'desc': row[1],
                                    'date': row[2],
                                    'dur': int(row[3]),
                                    'time': int(row[4]) if row[4] else None,
                                    'pts': int(row[5]),
                                    'words': []
                                }
                            
                            if word_text.isalpha() and len(word_text) >= 3:
                                games_cache[title]['words'].append(word_text)
                        
                        # Salva no Banco
                        for title, data in games_cache.items():
                            if not data['words']: continue # Pula jogos sem palavras
                            
                            new_game = AnagramGame(
                                title=title,
                                description=data['desc'],
                                activation_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                                duration_days=data['dur'],
                                time_limit_seconds=data['time'],
                                points_per_word=data['pts']
                            )
                            db.session.add(new_game)
                            db.session.flush() # Gera ID
                            
                            for w in data['words']:
                                # Cria a palavra (o modelo não tem 'shuffled', lembra?)
                                db.session.add(AnagramWord(game_id=new_game.id, correct_word=w))
                            
                            count_games += 1
                            
                        db.session.commit()
                        flash(f'{count_games} pacotes de Anagrama criados com sucesso!', 'success')

                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro na importação: {e}', 'danger')
           
            # --- Ações da Aba: Eventos ---
            elif action == 'criar_evento':
                nome = request.form.get('nome')
                pontuacao = request.form.get('pontuacao')
                descricao = request.form.get('descricao')
                redirect_hash = '#tab-events'
                if not nome or not pontuacao:
                    flash('Nome e pontuação do evento são obrigatórios.', 'danger')
                else:
                    try:
                        novo_evento = EventoPontuacao(nome=nome, pontuacao=int(pontuacao), descricao=descricao)
                        db.session.add(novo_evento)
                        db.session.commit()
                        flash(f"Evento '{nome}' criado com sucesso! Pontuação: {pontuacao} pts. Descrição: {descricao or 'N/A'}", 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Erro: Um evento com o nome '{nome}' já existe. Por favor, use um nome diferente.", 'danger')
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'editar_evento':
                evento_id = request.form.get('evento_id')
                nome = request.form.get('nome')
                pontuacao = request.form.get('pontuacao')
                descricao = request.form.get('descricao')
                evento = EventoPontuacao.query.get(evento_id)
                redirect_hash = '#tab-events'
                if evento:
                    try:
                        evento.nome = nome
                        evento.pontuacao = int(pontuacao)
                        evento.descricao = descricao
                        db.session.commit()
                        flash(f"Evento '{nome}' atualizado com sucesso!", 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Erro: Um evento com o nome '{nome}' já existe. Por favor, use um nome diferente.", 'danger')
                else:
                    flash("Evento não encontrado.", 'danger')
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'excluir_evento':
                evento_id = request.form.get('evento_id')
                evento = EventoPontuacao.query.get(evento_id)
                redirect_hash = '#tab-events'
                if evento:
                    try:
                        db.session.delete(evento)
                        db.session.commit()
                        flash(f"Evento '{evento.nome}' excluído com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash("Erro: O evento não pode ser excluído porque ainda está sendo usado em um histórico.", 'danger')
                else:
                    flash("Evento não encontrado.", 'danger')
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            # --- Ações da Aba: Conquistas ---
            elif action == 'criar_insignia':
                nome = request.form.get('nome')
                achievement_code = request.form.get('achievement_code')
                descricao = request.form.get('descricao')
                requisito_score_str = request.form.get('requisito_score')
                caminho_imagem = request.form.get('caminho_imagem')
                redirect_hash = '#tab-insignias'
                if Insignia.query.filter_by(achievement_code=achievement_code).first():
                    flash(f"Erro: O código de referência '{achievement_code}' já está em uso.", 'danger')

                if requisito_score_str:
                    requisito_score = int(requisito_score_str)
                else:
                    requisito_score = 0 

                if not nome or not caminho_imagem:
                    flash('Nome e caminho da imagem da insígnia são obrigatórios.', 'danger')
                else:
                    try:
                        nova_insignia = Insignia(nome=nome, achievement_code=achievement_code, descricao=descricao, requisito_score=requisito_score, caminho_imagem=caminho_imagem)
                        db.session.add(nova_insignia)
                        db.session.commit()
                        flash(f"Insígnia '{nome}' criada com sucesso!", 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Erro: Uma insígnia com o nome '{nome}' já existe.", 'danger')
                
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'editar_insignia':
                insignia_id = request.form.get('insignia_id')
                insignia = Insignia.query.get(insignia_id)
                redirect_hash = '#tab-insignias'
                if insignia:
                    try:
                        # Pega os novos dados do formulário
                        novo_nome = request.form.get('nome')
                        novo_code = request.form.get('achievement_code')

                        # --- VALIDAÇÃO CORRIGIDA ---
                        # Verifica se o NOVO NOME já existe em OUTRA conquista
                        nome_existente = Insignia.query.filter(Insignia.nome == novo_nome, Insignia.id != insignia_id).first()
                        if nome_existente:
                            flash(f"Erro: O nome '{novo_nome}' já está em uso por outra conquista.", 'danger')
                            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')

                        # Verifica se o NOVO CÓDIGO já existe em OUTRA conquista
                        code_existente = Insignia.query.filter(Insignia.achievement_code == novo_code, Insignia.id != insignia_id).first()
                        if code_existente:
                            flash(f"Erro: O código '{novo_code}' já está em uso por outra conquista.", 'danger')
                            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')

                        # Se as validações passaram, atualiza os dados
                        insignia.nome = novo_nome
                        insignia.achievement_code = novo_code
                        insignia.descricao = request.form.get('descricao')
                        score_str = request.form.get('requisito_score')
                        insignia.requisito_score = int(score_str) if score_str else 0
                        insignia.caminho_imagem = request.form.get('caminho_imagem')
                        bonus_type = request.form.get('bonus_type')
                        bonus_value_str = request.form.get('bonus_value')
                        if bonus_type == "NONE" or not bonus_value_str:
                            insignia.bonus_type = None
                            insignia.bonus_value = None
                        else:
                            insignia.bonus_type = bonus_type
                            insignia.bonus_value = float(bonus_value_str)

                        db.session.commit()
                        flash(f"Conquista '{insignia.nome}' atualizada com sucesso.", 'success')

                    except Exception as e:
                        db.session.rollback()
                        flash(f"Ocorreu um erro ao atualizar a conquista: {e}", "danger")
                else:
                    flash("Conquista não encontrada para edição.", "danger")
                return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)

            elif action == 'excluir_insignia':
                insignia_id = request.form.get('insignia_id')
                insignia = Insignia.query.get(insignia_id)
                redirect_hash = '#tab-insignias'
                if insignia:
                    try:

                        GuardianInsignia.query.filter_by(insignia_id=insignia_id).delete()
                        db.session.delete(insignia)
                        db.session.commit()
                        flash(f"Insígnia '{insignia.nome}' e todas as suas concessões foram excluídas com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Ocorreu um erro ao excluir a insígnia: {e}", 'danger')
                else:
                    flash("Insígnia não encontrada.", 'danger')
 
            # --- Ações da Aba: password game ---
            elif action == 'config_password_game':
                config = PasswordGameConfig.query.first()
                if not config:
                    config = PasswordGameConfig()
                    db.session.add(config)
                
                config.is_active = 'is_active' in request.form
                selected_days = request.form.getlist('active_days')
                config.active_days = ",".join(selected_days)
                config.time_limit_seconds = int(request.form.get('time_limit', 120))
                config.base_reward_points = int(request.form.get('base_reward', 300))
                
                # Configuração de Dificuldade (Quantas de cada tipo)
                config.rules_count_easy = int(request.form.get('count_easy', 1))
                config.rules_count_medium = int(request.form.get('count_medium', 2))
                config.rules_count_hard = int(request.form.get('count_hard', 1))
                config.rules_count_insane = int(request.form.get('count_insane', 1))
                
                db.session.commit()
                flash('Configurações do Password Vault atualizadas!', 'success')
                redirect_hash = '#tab-password'


            else:
                flash(f'Ação POST desconhecida: {action}', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro: {e}', 'danger')
            print(f"Erro no POST de content_hub: {e}") 

        return redirect(url_for('admin_v2_bp.content_hub') + redirect_hash)
        

    quizzes = Quiz.query.order_by(Quiz.activation_date.desc()).all()
    termo_games = TermoGame.query.order_by(TermoGame.created_at.desc()).all()
    anagram_games = AnagramGame.query.order_by(AnagramGame.created_at.desc()).all()
    eventos = EventoPontuacao.query.order_by(EventoPontuacao.nome.asc()).all()
    insignias = Insignia.query.order_by(Insignia.nome).all()
    colaboradores = Guardians.query.order_by(Guardians.nome).all()

    password_config = PasswordGameConfig.query.first() or PasswordGameConfig()
    password_rules_list = sorted(PASSWORD_RULES_DB.values(), key=lambda x: x['id'])

    return render_template(
        'guardians/admin_content_hub.html',
        quizzes=quizzes,
        termo_games=termo_games,
        anagram_games=anagram_games,
        eventos=eventos,
        insignias=insignias,
        colaboradores=colaboradores,
        achievement_bonus_types=BONUS_TYPES,
        date=date,
        password_config=password_config,
        password_rules=password_rules_list,
        date_today=date.today(),
        timedelta_obj=timedelta
    )