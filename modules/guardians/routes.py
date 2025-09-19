# modules/guardians/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import  current_user
from modules.login.decorators import login_required, admin_required
from modules.login.session_manager import SessionManager
from sqlalchemy import func, desc, and_, not_, asc, cast, Interval, text, case
from application.models import db, Guardians, HistoricoAcao, NivelSeguranca, GuardianInsignia, Insignia, EventoPontuacao, Quiz, Question, AnswerOption, QuizCategory, QuizAttempt, UserAnswer
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.exc import IntegrityError
import re
from sqlalchemy.orm import joinedload
import random
from .logic import apply_streak_bonus, update_user_streak, atualizar_nivel_usuario, get_achievement_sort_key


guardians_bp = Blueprint('guardians_bp', __name__)


@guardians_bp.route('/meu-perfil', defaults={'perfil_id': None})
@guardians_bp.route('/meu-perfil/<int:perfil_id>')
@login_required # Usando o decorator que já corrigimos
def meu_perfil(perfil_id):
    
    # Busca o ID do usuário logado na sessão
    logged_in_user_id = SessionManager.get("user_id")
    
    perfil_guardian = None
    is_own_profile = False


    if perfil_id is None:
        # Se nenhum ID for passado na URL, estamos vendo nosso próprio perfil.
        # Buscamos o Guardião pelo ID do usuário logado na sessão.
        perfil_guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()
        is_own_profile = True
    else:
        # Se um ID foi passado, estamos vendo o perfil de outra pessoa.
        perfil_guardian = Guardians.query.get_or_404(perfil_id)
        # Verifica se o perfil que estamos vendo pertence ao usuário logado.
        if perfil_guardian.user_id == logged_in_user_id:
            is_own_profile = True

    # Se por algum motivo o perfil não for encontrado, redireciona.
    if not perfil_guardian:
        flash("Perfil de Guardião não encontrado.", "danger")
        return redirect(url_for("home_bp.render_home"))

    # Verifica se o perfil é anônimo e se não somos o dono.
    if not is_own_profile and perfil_guardian.is_anonymous:
        flash('Este guardião optou por manter o perfil privado.', 'info')
        return redirect(url_for('guardians_bp.rankings'))

    #add patrulha diaria
    patrol_completed_today = (perfil_guardian.last_patrol_date == date.today())


    # Paginação
    page = request.args.get('page', 1, type=int)
    pagination = perfil_guardian.historico_acoes.order_by(
        desc(HistoricoAcao.data_evento)
    ).paginate(page=page, per_page=10, error_out=False)
    historico_paginado = pagination.items
    
    # Insígnias
    insignias_ganhas = [gi.insignia for gi in perfil_guardian.insignias_conquistadas]
    
    # Níveis e Progresso
    nivel_atual = perfil_guardian.nivel
    proximo_nivel = None
    progresso_percentual = 0
    if nivel_atual:
        proximo_nivel = NivelSeguranca.query.filter(NivelSeguranca.score_minimo > nivel_atual.score_minimo).order_by(NivelSeguranca.score_minimo).first()
        if proximo_nivel:
            score_para_o_nivel = proximo_nivel.score_minimo - nivel_atual.score_minimo
            score_atual_no_nivel = perfil_guardian.score_atual - nivel_atual.score_minimo
            progresso_percentual = max(0, int((score_atual_no_nivel / score_para_o_nivel) * 100)) if score_para_o_nivel > 0 else 100
        else:
            progresso_percentual = 100
    
    # Ranking
    todos_os_perfis = Guardians.query.order_by(Guardians.score_atual.desc()).all()
    ranking_atual = "N/A"
    for i, p in enumerate(todos_os_perfis):
        if p.id == perfil_guardian.id:
            ranking_atual = i + 1
            break
            
    # Contadores
    numero_conquistas = len(insignias_ganhas)
    quizzes_respondidos_count = QuizAttempt.query.filter_by(guardian_id=perfil_guardian.id).count()
    patrols_completed_count = perfil_guardian.historico_acoes.filter(
        HistoricoAcao.descricao.like('Patrulha Diária%')
    ).count()
    
    # Busca todos os níveis para a tabela de progressão
    todos_os_niveis = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo.asc()).all()


    return render_template(
        'guardians/meu_perfil.html',
        perfil=perfil_guardian,
        is_own_profile=is_own_profile,
        todos_os_niveis=todos_os_niveis,
        historico=historico_paginado,
        pagination=pagination,
        insignias_ganhas=insignias_ganhas,
        nivel_atual=nivel_atual,
        proximo_nivel=proximo_nivel,
        progresso_percentual=progresso_percentual,
        ranking_atual=ranking_atual,
        numero_conquistas=numero_conquistas,
        quizzes_respondidos_count=quizzes_respondidos_count,
        patrol_completed_today=patrol_completed_today,
        patrols_completed_count=patrols_completed_count
    )




@guardians_bp.route('/rankings')
@login_required # Usando o decorator correto que usa o SessionManager
def rankings():
    
    logged_in_user_id = SessionManager.get("user_id")
    
    guardian_logado = Guardians.query.filter_by(user_id=logged_in_user_id).first()
    
    current_guardian_id = guardian_logado.id if guardian_logado else -1

    ranking_global = Guardians.query.options(joinedload(Guardians.featured_insignia)).order_by(desc(Guardians.score_atual)).all()

    ranking_streak = Guardians.query.options(joinedload(Guardians.featured_insignia)).order_by(Guardians.current_streak.is_(None), desc(Guardians.current_streak)).all()

    ranking_departamento = db.session.query(
        Guardians.departamento_nome, 
        func.sum(Guardians.score_atual).label('score_total')
    ).group_by(Guardians.departamento_nome).order_by(desc('score_total')).all()

    return render_template('guardians/rankings.html', 
                           ranking_global=ranking_global,
                           ranking_streak=ranking_streak,
                           ranking_departamento=ranking_departamento,
                           current_user_id=current_guardian_id)

# Em modules/guardians/routes.py

@guardians_bp.route('/sobre-o-programa')
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
        'guardians/sobre_o_programa.html', 
        categorized_achievements=categorized_achievements,
        eventos=eventos,     
        niveis=niveis        
    )
    
@guardians_bp.route('/central-de-treinamentos')
@login_required # Usando o decorator correto que usa o SessionManager
def central():
    """
    Esta rota busca os quizzes disponíveis e calcula o tempo de expiração para cada um.
    """
    now = datetime.utcnow()
    
    # 1. Busca o ID do usuário na sessão.
    logged_in_user_id = SessionManager.get("user_id")
    
    # 2. Encontra o perfil de guardião correspondente.
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    # Se não encontrar um perfil de guardião para o usuário logado, redireciona.
    if not guardian:
        flash("Perfil de Guardião não encontrado.", "warning")
        return redirect(url_for("home_bp.render_home"))

    guardian_id = guardian.id
    
    # Subquery para encontrar quizzes já respondidos
    attempted_quiz_ids = db.session.query(QuizAttempt.quiz_id).filter(QuizAttempt.guardian_id == guardian_id)

    # Query principal
    candidate_quizzes = Quiz.query.filter(
        Quiz.is_active == True,
        Quiz.activation_date <= now.date(),
        not_(Quiz.id.in_(attempted_quiz_ids))
    ).order_by(Quiz.activation_date.desc()).all()

    # Lógica para calcular expiração
    available_quizzes_with_expiry = []
    for quiz in candidate_quizzes:
        expiry_datetime = datetime.combine(quiz.activation_date, datetime.min.time()) + timedelta(days=quiz.duration_days)
        if now < expiry_datetime:
            time_left = expiry_datetime - now
            days_left = time_left.days
            hours_left = time_left.seconds // 3600
            expiry_text = ""
            if days_left >= 2:
                expiry_text = f"Expira em {days_left} dias"
            elif days_left == 1:
                expiry_text = "Expira em 1 dia"
            elif hours_left > 1:
                expiry_text = f"Expira em {hours_left} horas"
            else:
                expiry_text = "Expira em menos de 1 hora!"
            available_quizzes_with_expiry.append({'quiz': quiz, 'expiry_text': expiry_text})

    return render_template('guardians/central_de_treinamentos.html', available_quizzes=available_quizzes_with_expiry)


@guardians_bp.route('/admin/quiz/<int:quiz_id>/visualizar')
@admin_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('guardians/quiz_preview.html', quiz=quiz)


@guardians_bp.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    guardian = Guardians.query.filter_by(user_id=SessionManager.get("user_id")).first()
    
    if not guardian:
        abort(404)

    attempt = QuizAttempt.query.filter_by(guardian_id=guardian.id, quiz_id=quiz_id).first_or_404()

    # Se a tentativa já tem uma data de finalização, significa que o quiz foi concluído.
    if attempt.completed_at:
        flash("Este quiz já foi finalizado e não pode ser acessado novamente.", "info")
        return redirect(url_for('guardians_bp.central'))

    # Lógica do timer (continua a mesma)
    remaining_time = None
    if quiz.time_limit_seconds:
        start_time = attempt.started_at.replace(tzinfo=timezone.utc)
        now_time = datetime.now(timezone.utc)
        time_limit_seconds = quiz.time_limit_seconds
        
        elapsed_seconds = (now_time - start_time).total_seconds()
        remaining_time = max(0, time_limit_seconds - elapsed_seconds)

    return render_template('guardians/take_quiz.html', quiz=quiz, remaining_time=remaining_time)


@guardians_bp.route('/quiz/start/<int:quiz_id>', methods=['POST'])
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
    Recebe as respostas, salva CADA UMA DELAS, calcula a pontuação, 
    salva o resultado e redireciona.
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

        if quiz.time_limit_seconds:
            start_time = attempt.started_at.replace(tzinfo=timezone.utc)
            submit_time = datetime.now(timezone.utc)
            time_limit_seconds = quiz.time_limit_seconds
            elapsed_on_submit = (submit_time - start_time).total_seconds()
            

            if elapsed_on_submit > time_limit_seconds:
                flash("Tempo esgotado! Sua tentativa foi registrada com 0 pontos.", "warning")
                return redirect(url_for('guardians_bp.central'))

        base_score = 0
        results_details = {}
        submitted_answers = {key: val for key, val in request.form.items() if key.startswith('question_')}
        correct_answers_count = 0
        total_possible_points = sum(q.points for q in quiz.questions)
    
    
        timer_expired = request.form.get('timer_expired') == 'true'
        abandoned = request.form.get('abandoned') == 'true'

        # Se o tempo acabou OU o quiz foi abandonado
        if timer_expired or abandoned:
            message = "..."
            attempt.score = 0
            attempt.completed_at = datetime.now(timezone.utc) # <-- GARANTE QUE A DATA SEJA SALVA
            history_entry = HistoricoAcao(...)
            db.session.add(history_entry)
            db.session.commit()
            flash(message, 'warning')
            return redirect(url_for('guardians_bp.central'))
    

        for question in quiz.questions:
            question_key = f'question_{question.id}'
            submitted_option_id = submitted_answers.get(question_key)
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            is_user_correct = False

            if submitted_option_id and correct_option and int(submitted_option_id) == correct_option.id:
                base_score += question.points
                is_user_correct = True
                correct_answers_count += 1
            
            results_details[question.id] = {
                'submitted_option_id': int(submitted_option_id) if submitted_option_id else None,
                'correct_option_id': correct_option.id if correct_option else None,
                'is_correct': is_user_correct
            }

            
            # Salva a resposta individual, vinculando-a à tentativa existente
            if submitted_option_id:
                user_answer = UserAnswer(
                    quiz_attempt_id=attempt.id, # <-- Usa o ID da tentativa encontrada
                    question_id=question.id,
                    selected_option_id=int(submitted_option_id)
                )
                db.session.add(user_answer)

        # 4. ATUALIZA a tentativa existente com a pontuação final
        attempt.score = base_score
        attempt.completed_at = datetime.now(timezone.utc) # Marca a hora de finalização
        
        
        # --- LÓGICA DE CONQUISTAS POR ACERTO --- #
        is_perfect_score = (base_score == total_possible_points)
        if is_perfect_score:
            # Incrementa a ofensiva de acertos perfeitos
            guardian.perfect_quiz_streak = (guardian.perfect_quiz_streak or 0) + 1   
        else:
            # Se não foi perfeito, zera a ofensiva de acertos
            guardian.perfect_quiz_streak = 0
        
        final_score, bonus_points = apply_streak_bonus(guardian, base_score)
        
        if final_score > 0:
            descricao = f"Completou o quiz '{quiz.title}' e ganhou {base_score} pontos."
            if bonus_points > 0:
                descricao += f" (+{bonus_points} pts de bônus de ofensiva!)"
            history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=descricao, pontuacao=final_score)
            db.session.add(history_entry)
        
        guardian.score_atual += final_score
        update_user_streak(guardian)
        
        quiz_context = {
            'quiz': quiz,
            'is_perfect_score': is_perfect_score
        }
        level_up, novas_conquistas = atualizar_nivel_usuario(guardian, quiz_context=quiz_context)
        
        if level_up and guardian.nivel:
            flash(f"Parabéns! Você subiu para o nível {guardian.nivel.nome}!", 'info')
        for conquista_nome in novas_conquistas:
            flash(f"Nova Conquista Desbloqueada: {conquista_nome}!", "success")

        db.session.commit()
        
        duration_seconds = (attempt.completed_at.replace(tzinfo=timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds()


        session['quiz_results'] = { 'quiz_id': quiz.id, 'score': base_score, 'bonus': bonus_points, 'total_score': final_score, 'details': results_details, 'total_questions': len(quiz.questions),'correct_answers': correct_answers_count, 'duration_seconds': duration_seconds }

        return redirect(url_for('guardians_bp.quiz_result', quiz_id=quiz.id))

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO PROCESSAR O QUIZ: {e}")
        flash('Ocorreu um erro ao processar seu quiz.', 'danger')
        return redirect(url_for('guardians_bp.central'))
    

@guardians_bp.route('/quiz/<int:quiz_id>/resultado')
@login_required # Garante que apenas usuários logados vejam a página de resultado
def quiz_result(quiz_id):
    """
    Exibe a página de resultados de um quiz que o usuário acabou de completar.
    """
    results = session.pop('quiz_results', None)

    if not results or results['quiz_id'] != quiz_id:
        flash('Resultados não encontrados. Por favor, complete um quiz primeiro.', 'warning')
        return redirect(url_for('guardians_bp.central'))

    quiz = Quiz.query.get_or_404(quiz_id)
    
    return render_template('guardians/quiz_result.html', quiz=quiz, results=results)



@guardians_bp.route('/admin/quiz/<int:quiz_id>/analise')
@admin_required
def quiz_analysis(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
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
    
    # 2. NOVA QUERY para as respostas individuais detalhadas
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

    # Estrutura os dados para o template
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

    return render_template('guardians/quiz_analysis.html', 
                           quiz=quiz, 
                           analysis=structured_analysis,
                           detailed_responses=detailed_responses)




@guardians_bp.route('/admin/quizzes/hub')
@admin_required
def quiz_hub():
    """
    Exibe o Hub de Análise de Quizzes com estatísticas, filtros e ordenação.
    """
    # Lógica de Filtros e Ordenação (continua a mesma)
    search_term = request.args.get('search', '')
    sort_by = request.args.get('sort', 'recent')

    # --- QUERY PRINCIPAL E UNIFICADA (COM CÁLCULO DE TEMPO SEGURO) ---
    # Usamos um CASE para garantir que só calculamos durações positivas
    valid_duration = func.timestampdiff(text('SECOND'), QuizAttempt.started_at, QuizAttempt.completed_at)
    safe_duration = case((valid_duration > 0, valid_duration), else_=None)

    query = db.session.query(
        Quiz,
        func.count(db.distinct(QuizAttempt.id)).label('total_attempts'),
        func.count(db.distinct(Question.id)).label('question_count'),
        func.sum(QuizAttempt.score).label('total_score'),
        func.sum(Question.points).label('total_possible_points_per_attempt'),
        func.sum(safe_duration).label('total_time'), # Usa a duração segura
        func.count(safe_duration).label('attempts_with_time') # Conta apenas tentativas com tempo válido
    ).outerjoin(QuizAttempt, Quiz.id == QuizAttempt.quiz_id)\
     .outerjoin(Question, Quiz.id == Question.quiz_id)\
     .group_by(Quiz.id)

    if search_term:
        query = query.filter(Quiz.title.ilike(f'%{search_term}%'))
        
    all_quizzes_stats = query.all()

    # --- Processamento dos dados e cálculo das estatísticas GERAIS ---
    quizzes_info = []
    grand_total_attempts = 0
    grand_total_earned_score = 0
    grand_total_possible_score_for_attempts = 0
    grand_total_time = 0
    grand_total_attempts_with_time = 0

    for quiz, attempts, q_count, total_score, total_possible, total_time, attempts_with_time in all_quizzes_stats:
        avg_score_percent = (total_score / (total_possible * attempts) * 100) if total_possible and attempts else 0
        avg_time = (total_time / attempts_with_time) if attempts_with_time and total_time else 0
        end_date = quiz.activation_date + timedelta(days=quiz.duration_days - 1)
        
        quizzes_info.append({
            'quiz': quiz, 'total_attempts': attempts, 'question_count': q_count,
            'avg_score_percent': avg_score_percent, 'avg_time': avg_time, 'end_date': end_date
        })
        
        grand_total_attempts += attempts
        grand_total_earned_score += total_score or 0
        grand_total_possible_score_for_attempts += (total_possible or 0) * attempts
        grand_total_time += total_time or 0
        grand_total_attempts_with_time += attempts_with_time or 0

    # --- Lógica para os Cards de Destaque ---
    general_avg_score = (grand_total_earned_score / grand_total_possible_score_for_attempts * 100) if grand_total_possible_score_for_attempts else 0
    general_avg_time = (grand_total_time / grand_total_attempts_with_time) if grand_total_attempts_with_time else 0

    quizzes_com_tentativas = [q for q in quizzes_info if q['total_attempts'] > 0]
    quizzes_com_tentativas.sort(key=lambda x: (x['avg_score_percent'] or 0))
    
    quiz_mais_dificil = quizzes_com_tentativas[0]['quiz'].title if quizzes_com_tentativas else 'N/A'
    quiz_mais_facil = quizzes_com_tentativas[-1]['quiz'].title if quizzes_com_tentativas else 'N/A'
    
    if sort_by == 'attempts':
        quizzes_info.sort(key=lambda x: x['total_attempts'], reverse=True)
    else:
        quizzes_info.sort(key=lambda x: x['quiz'].created_at, reverse=True)

    return render_template('guardians/quiz_hub.html', quizzes_info=quizzes_info, total_attempts=grand_total_attempts,
                           quiz_mais_dificil=quiz_mais_dificil, quiz_mais_facil=quiz_mais_facil,
                           search_term=search_term, sort_by=sort_by, general_avg_score=general_avg_score,
                           general_avg_time=general_avg_time)

@guardians_bp.route('/guardians-admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        
        action = request.form.get('action')

        if action == 'lancar_pontuacao':
                    colaborador_id = request.form.get('colaborador_id')
                    evento_id = request.form.get('evento_id')

                    perfil_guardian = Guardians.query.get(colaborador_id)
                    evento_selecionado = EventoPontuacao.query.get(evento_id)

                    if perfil_guardian and evento_selecionado:
                        try:
                            base_points = evento_selecionado.pontuacao

                            # --- NOVA LÓGICA DE BÔNUS ---
                            final_points, bonus_points = apply_streak_bonus(perfil_guardian, base_points)

                            # Atualiza o score do guardião com a pontuação final (com bônus)
                            perfil_guardian.score_atual += final_points

                            # Cria a descrição para o histórico, incluindo o bônus se houver
                            descricao = f"{evento_selecionado.nome}: {evento_selecionado.descricao or 'Sem descrição.'}"
                            if bonus_points > 0:
                                descricao += f" (+{bonus_points} pts de bônus de ofensiva!)"

                            novo_historico = HistoricoAcao(
                                guardian_id=colaborador_id,
                                descricao=descricao,
                                pontuacao=final_points,
                                data_evento=db.func.now()
                            )
                            db.session.add(novo_historico)

                            level_up, novas_conquistas = atualizar_nivel_usuario(perfil_guardian)
                            if level_up and perfil_guardian.nivel:
                                flash(f"{perfil_guardian.nome} teve seu nível atualizado para {perfil_guardian.nivel.nome}!", 'info')
                            for conquista_nome in novas_conquistas:
                                flash(f"{perfil_guardian.nome} desbloqueou a conquista: {conquista_nome}!", "info")

                            db.session.commit()
                            flash(f"Pontuação de {final_points} ({base_points} + {bonus_points} de bônus) lançada para {perfil_guardian.nome}.", 'success')

                        except Exception as e:
                            db.session.rollback()
                            flash(f"Ocorreu um erro ao lançar a pontuação: {e}", 'danger')
                    else:
                        flash("Colaborador ou evento não encontrado.", 'danger')

                    return redirect(url_for('guardians_bp.admin')) # Redireciona para a aba principal     
        
        
        
        elif action == 'criar_evento':
            nome = request.form.get('nome')
            pontuacao = request.form.get('pontuacao')
            descricao = request.form.get('descricao')

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

            return redirect(url_for('guardians_bp.admin') + '#panel-events')

            
           
        
        elif action == 'editar_evento':
            evento_id = request.form.get('evento_id')
            nome = request.form.get('nome')
            pontuacao = request.form.get('pontuacao')
            descricao = request.form.get('descricao')
            evento = EventoPontuacao.query.get(evento_id)
            
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
                
            return redirect(url_for('guardians_bp.admin') + '#panel-events')


        elif action == 'excluir_evento':
            evento_id = request.form.get('evento_id')
            evento = EventoPontuacao.query.get(evento_id)
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
                
            return redirect(url_for('guardians_bp.admin') + '#panel-events')

        
        elif action == 'criar_nivel':
            nome = request.form.get('nome')
            score_minimo = request.form.get('score_minimo')
            badge_icon_url = request.form.get('badge_icon_url')
            if not nome or not score_minimo or not badge_icon_url:
                flash('Todos os campos do nível são obrigatórios.', 'danger')
            else:
                try:
                    novo_nivel = NivelSeguranca(nome=nome, score_minimo=int(score_minimo), badge_icon_url=badge_icon_url)
                    db.session.add(novo_nivel)
                    db.session.commit()
                    flash(f"Nível '{nome}' criado com sucesso!", 'success')
                except IntegrityError:
                    db.session.rollback()
                    flash(f"Erro: Um nível com o nome '{nome}' já existe.", 'danger')
                    
            return redirect(url_for('guardians_bp.admin') + '#panel-levels')
        
        elif action == 'editar_nivel':
            nivel_id = request.form.get('nivel_id')
            nome = request.form.get('nome')
            score_minimo = request.form.get('score_minimo')
            badge_icon_url = request.form.get('badge_icon_url')
            nivel = NivelSeguranca.query.get(nivel_id)
            if nivel:
                try:
                    nivel.nome = nome
                    nivel.score_minimo = int(score_minimo)
                    nivel.badge_icon_url = badge_icon_url
                    db.session.commit()
                    flash(f"Nível '{nome}' atualizado com sucesso!", 'success')
                except IntegrityError:
                    db.session.rollback()
                    flash(f"Erro: Um nível com o nome '{nome}' já existe.", 'danger')
            else:
                flash("Nível não encontrado.", 'danger')
                
            return redirect(url_for('guardians_bp.admin') + '#panel-levels')

                

        elif action == 'excluir_nivel':
            nivel_id = request.form.get('nivel_id')
            nivel = NivelSeguranca.query.get(nivel_id)
            if nivel:
                try:
                    db.session.delete(nivel)
                    db.session.commit()
                    flash(f"Nível '{nivel.nome}' excluído com sucesso!", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash("Erro: O nível não pode ser excluído, pois ainda está associado a perfis.", 'danger')
            else:
                flash("Nível não encontrado.", 'danger')
                
            return redirect(url_for('guardians_bp.admin') + '#panel-levels')


        elif action == 'criar_insignia':
            nome = request.form.get('nome')
            achievement_code = request.form.get('achievement_code')
            descricao = request.form.get('descricao')
            requisito_score_str = request.form.get('requisito_score')
            caminho_imagem = request.form.get('caminho_imagem')
            
            if Insignia.query.filter_by(achievement_code=achievement_code).first():
                flash(f"Erro: O código de referência '{achievement_code}' já está em uso.", 'danger')

            # Verifica se o campo de pontuação não está vazio
            if requisito_score_str:
                requisito_score = int(requisito_score_str)
            else:
                requisito_score = 0  # Valor padrão para campos opcionais

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
                    
            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')


        elif action == 'editar_insignia':
            insignia_id = request.form.get('insignia_id')
            insignia = Insignia.query.get(insignia_id)

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

                    db.session.commit()
                    flash(f"Conquista '{insignia.nome}' atualizada com sucesso.", 'success')

                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao atualizar a conquista: {e}", "danger")
            else:
                flash("Conquista não encontrada para edição.", "danger")

            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')
    
                
        
        elif action == 'excluir_insignia':
            insignia_id = request.form.get('insignia_id')
            insignia = Insignia.query.get(insignia_id)
            if insignia:
                try:
                    # 1. Encontra e deleta todas as conquistas associadas a esta insígnia.
                    # Esta é a etapa crucial para evitar erros de chave estrangeira.
                    GuardianInsignia.query.filter_by(insignia_id=insignia_id).delete()

                    # 2. Agora, deleta a insígnia em si.
                    db.session.delete(insignia)

                    # 3. Confirma as mudanças no banco de dados.
                    db.session.commit()
                    flash(f"Insígnia '{insignia.nome}' e todas as suas concessões foram excluídas com sucesso!", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao excluir a insígnia: {e}", 'danger')
            else:
                flash("Insígnia não encontrada.", 'danger')
                
            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')


        elif action == 'dar_insignia':
            perfil_id = request.form.get('perfil_id')
            insignia_id = request.form.get('insignia_id')
            perfil_guardian = Guardians.query.get(perfil_id)
            insignia = Insignia.query.get(insignia_id)
            if perfil_guardian and insignia:
                conquista_existente = GuardianInsignia.query.filter_by(guardian_id=perfil_id, insignia_id=insignia_id).first()
                if not conquista_existente:
                    try:
                        # Adiciona a conquista
                        nova_conquista = GuardianInsignia(guardian_id=perfil_id, insignia_id=insignia_id, data_conquista=datetime.utcnow())
                        db.session.add(nova_conquista)

                        # ADIÇÃO: Cria o registro no histórico de atividades
                        novo_historico = HistoricoAcao(
                            guardian_id=perfil_id,
                            descricao=f"Conquistou a insígnia '{insignia.nome}'!",
                            pontuacao=0  # Conquistas não dão pontos, apenas o registro
                        )
                        db.session.add(novo_historico)

                        db.session.commit()
                        flash(f"Insígnia '{insignia.nome}' concedida a {perfil_guardian.nome} com sucesso!", 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Erro ao conceder insígnia: {e}", "danger")
                else:
                    flash(f"Erro: {perfil_guardian.nome} já possui a insígnia '{insignia.nome}'.", 'warning')
            else:
                flash("Colaborador ou insígnia não encontrados.", 'danger')
            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')
        
        
        elif action == 'remover_insignia':
            perfil_id = request.form.get('perfil_id')
            insignia_id = request.form.get('insignia_id')
            
            # Busca a conquista específica que queremos remover
            conquista_para_remover = GuardianInsignia.query.filter_by(
                guardian_id=perfil_id,
                insignia_id=insignia_id
            ).first()

            if conquista_para_remover:
                try:
                    # Pega o nome da insígnia ANTES de deletar, para usar na mensagem
                    nome_insignia = conquista_para_remover.insignia.nome
                    nome_guardian = conquista_para_remover.guardian.nome

                    # Remove o registro da conquista
                    db.session.delete(conquista_para_remover)

                    # Adiciona um registro no histórico informando a remoção
                    novo_historico = HistoricoAcao(
                        guardian_id=perfil_id,
                        descricao=f"Teve a insígnia '{nome_insignia}' removida por um admin.",
                        pontuacao=0
                    )
                    db.session.add(novo_historico)

                    db.session.commit()
                    flash(f"Insígnia '{nome_insignia}' removida de {nome_guardian} com sucesso!", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao remover a insígnia: {e}", 'danger')
            else:
                flash("O colaborador selecionado não possui esta insígnia para ser removida.", 'warning')
            
            return redirect(url_for('guardians_bp.admin') + '#panel-insignias')


        elif action == 'editar_perfil':
            perfil_id = request.form.get('perfil_id')
            perfil_guardian = Guardians.query.get(perfil_id)

            if perfil_guardian:
                try:
                    score_str = request.form.get('score_atual')
                    if score_str is not None:
                        perfil_guardian.score_atual = int(score_str)
                        
                    perfil_guardian.departamento_nome = request.form.get('departamento')
                    perfil_guardian.is_admin = 'is_admin' in request.form
                    perfil_guardian.opt_in_real_name_ranking = 'opt_in_ranking' in request.form

                    if 'current_streak' in request.form:
                        nova_ofensiva_str = request.form.get('current_streak')
                        if nova_ofensiva_str: # Garante que não está vazio
                            nova_ofensiva_int = int(nova_ofensiva_str)

                            # Apenas cria um log se o valor realmente mudou
                            if nova_ofensiva_int != (perfil_guardian.current_streak or 0):
                                descricao = f"Ofensiva ajustada de {perfil_guardian.current_streak or 0} para {nova_ofensiva_int} dias pelo administrador."
                                novo_historico = HistoricoAcao(guardian_id=perfil_guardian.id, descricao=descricao, pontuacao=0)
                                db.session.add(novo_historico)

                            # Atualiza o valor e a data
                            perfil_guardian.current_streak = nova_ofensiva_int
                            perfil_guardian.last_streak_date = date.today() if nova_ofensiva_int > 0 else None

                    # Checa se o nível do usuário mudou após a alteração de score
                    if atualizar_nivel_usuario(perfil_guardian):
                        flash(f"{perfil_guardian.nome} subiu para o nível {perfil_guardian.nivel.nome}!", 'info')

                    db.session.commit()
                    flash(f"Perfil de {perfil_guardian.nome} atualizado com sucesso!", 'success')

                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao atualizar o perfil: {e}", "danger")
            else:
                flash("Perfil de colaborador não encontrado.", 'danger')

            return redirect(url_for('guardians_bp.admin') + '#panel-profiles')
    

        elif action == 'zerar_historico':
            perfil_id = request.form.get('perfil_id')
            perfil_guardian = Guardians.query.get(perfil_id)
            if perfil_guardian:
                try:
                    # 1. Apaga o histórico de ações (como já fazia)
                    HistoricoAcao.query.filter_by(guardian_id=perfil_id).delete()
 
                    # 2. NOVA LINHA: Apaga todas as insígnias conquistadas pelo usuário
                    GuardianInsignia.query.filter_by(guardian_id=perfil_id).delete()
 
                    # 3. NOVA LINHA: Apaga todas as tentativas de quizzes do usuário
                    attempts_to_delete = QuizAttempt.query.filter_by(guardian_id=perfil_id).all()
                    for attempt in attempts_to_delete:
                        db.session.delete(attempt)
 
                    # 4. Zera a pontuação, dias de vigilante e atualiza o nivel
                    perfil_guardian.score_atual = 0
                    perfil_guardian.current_streak = 0
                    perfil_guardian.last_streak_date = None
                    perfil_guardian.last_patrol_date = None #zera patrulha diaria
                    perfil_guardian.featured_insignia_id = None
                    perfil_guardian.perfect_quiz_streak = 0

                   
                    
                    nivel_base = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo.asc()).first()
                    if nivel_base:
                        perfil_guardian.nivel_id = nivel_base.id
    
                    db.session.commit()
                    flash(f"O progresso de {perfil_guardian.nome} (histórico, conquistas e quizzes) foi completamente zerado.", 'success')
 
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao zerar o histórico: {e}", 'danger')
            else:
                flash("Perfil de colaborador não encontrado.", 'danger')
            return redirect(url_for('guardians_bp.admin') + '#panel-profiles')

        
        elif action == 'excluir_perfil':
            perfil_id = request.form.get('perfil_id')
            perfil_guardian = Guardians.query.get(perfil_id)
            if perfil_guardian:
                HistoricoAcao.query.filter_by(guardian_id=perfil_id).delete()
                GuardianInsignia.query.filter_by(guardian_id=perfil_id).delete()
                db.session.delete(perfil_guardian)
                db.session.commit()
                flash(f"Perfil de {perfil_guardian.nome} excluído com sucesso!", 'success')
            else:
                flash("Perfil de colaborador não encontrado.", 'danger')
                
            return redirect(url_for('guardians_bp.admin') + '#panel-profiles')

                
        elif action == 'criar_quiz':
            try:
                time_limit = request.form.get('time_limit_seconds')

                # 1. Criar o objeto Quiz principal
                novo_quiz = Quiz(
                    title=request.form.get('title'),
                    description=request.form.get('description'),
                    activation_date=datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date(),
                    duration_days=int(request.form.get('duration_days')),
                    category=QuizCategory[request.form.get('category')],
                    time_limit_seconds=int(time_limit) if time_limit else None
                )

                # 2. Estruturar os dados das perguntas e opções
                perguntas_data = {}
                for key, value in request.form.items():
                    # Usando expressão regular para extrair os índices
                    match = re.match(r'questions\[(\d+)\]\[(.+?)\](?:\[(\d+)\]\[(.+?)\])?', key)
                    if match:
                        q_index, q_field, o_index, o_field = match.groups()
                        q_index = int(q_index)
                        
                        if q_index not in perguntas_data:
                            perguntas_data[q_index] = {'options': {}}
                        
                        if o_index is None: # É um campo da pergunta (text, points)
                            perguntas_data[q_index][q_field] = value
                        else: # É um campo da opção
                            o_index = int(o_index)
                            if o_index not in perguntas_data[q_index]['options']:
                                perguntas_data[q_index]['options'][o_index] = {}
                            perguntas_data[q_index]['options'][o_index][o_field] = value

                # 3. Criar os objetos Question e AnswerOption
                for q_idx, q_data in sorted(perguntas_data.items()):
                    nova_pergunta = Question(
                        question_text=q_data['question_text'],
                        points=int(q_data['points']),
                        quiz=novo_quiz
                    )
                    
                    correct_option_index = int(q_data['correct_option'])
                    
                    for o_idx, o_data in sorted(q_data['options'].items()):
                        nova_opcao = AnswerOption(
                            option_text=o_data['option_text'],
                            is_correct=(o_idx == correct_option_index),
                            question=nova_pergunta
                        )
                        # O SQLAlchemy anexa automaticamente a opção à pergunta
                
                # 4. Adicionar tudo à sessão e salvar
                db.session.add(novo_quiz)
                db.session.commit()
                flash('Quiz criado com sucesso!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar o quiz: {e}', 'danger')
                
            return redirect(url_for('guardians_bp.admin') + '#panel-quizzes')



        elif action == 'excluir_quiz':
            quiz_id = request.form.get('quiz_id')
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                try:
                    # Graças ao 'cascade', o SQLAlchemy deletará as perguntas, opções e tentativas filhas.
                    db.session.delete(quiz)
                    db.session.commit()
                    flash(f"Quiz '{quiz.title}' excluído com sucesso!", 'success')
                except Exception as e:
                    db.session.rollback()
                    print(f"--- ERRO AO EXCLUIR QUIZ ---: {e}") # Mantendo o print para segurança
                    flash(f"Erro ao excluir o quiz. Verifique o terminal para mais detalhes.", 'danger')
            else:
                flash("Quiz não encontrado.", 'danger')        
                
                
            return redirect(url_for('guardians_bp.admin') + '#panel-quizzes')

    colaboradores = Guardians.query.order_by(Guardians.nome).all()
    eventos = EventoPontuacao.query.order_by(EventoPontuacao.nome).all()
    niveis = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo).all()
    insignias = Insignia.query.order_by(Insignia.nome).all()
    quizzes = Quiz.query.order_by(Quiz.activation_date.desc()).all()


    return render_template('guardians/guardians_admin.html', colaboradores=colaboradores, eventos=eventos, niveis=niveis, insignias=insignias, quizzes=quizzes)



@guardians_bp.route('/guardians-admin/analytics', defaults={'guardian_id': None}, methods=['GET', 'POST'])
@guardians_bp.route('/guardians-admin/analytics/<int:guardian_id>', methods=['GET'])
@login_required
def analytics(guardian_id):

    # --- WIDGET 1: MÉTRICAS GERAIS (JÁ EXISTENTE) ---
    one_month_ago = date.today() - timedelta(days=30)
    active_guardians_count = db.session.query(func.count(HistoricoAcao.guardian_id.distinct())).filter(HistoricoAcao.data_evento >= one_month_ago).scalar()
    total_quizzes_answered = QuizAttempt.query.count()
    avg_score = db.session.query(func.avg(Guardians.score_atual)).scalar() or 0
    avg_score = round(avg_score)

    # --- WIDGET 2: NOVAS MÉTRICAS DE ANÁLISE DE RISCO ---
    
    # Contabiliza cliques em simulações de phishing
    total_clicks_phishing = HistoricoAcao.query.filter(HistoricoAcao.descricao.like('%Queda em Phishing%')).count()
    
    # Contabiliza reportes de phishing (simulados e reais)
    total_reports_phishing = HistoricoAcao.query.filter(HistoricoAcao.descricao.like('%Reporte de Phishing%')).count()

    # Top 5 usuários mais vulneráveis (que mais clicaram)
    vulnerable_users = db.session.query(
        Guardians.nome,
        func.count(HistoricoAcao.id).label('click_count')
    ).join(HistoricoAcao, Guardians.id == HistoricoAcao.guardian_id).filter(
        HistoricoAcao.descricao.like('%Queda em Phishing%')
    ).group_by(Guardians.nome).order_by(desc('click_count')).limit(5).all()

    # Top 3 departamentos mais vulneráveis
    vulnerable_depts = db.session.query(
        Guardians.departamento_nome,
        func.count(HistoricoAcao.id).label('click_count')
    ).join(HistoricoAcao, Guardians.id == HistoricoAcao.guardian_id).filter(
        HistoricoAcao.descricao.like('%Queda em Phishing%')
    ).group_by(Guardians.departamento_nome).order_by(desc('click_count')).limit(3).all()


    # --- WIDGET 4: LÓGICA DE CONSULTA INDIVIDUAL (JÁ EXISTENTE) ---
    if request.method == 'POST':
        guardian_id = request.form.get('guardian_id')
        if guardian_id:
            return redirect(url_for('guardians_bp.analytics', guardian_id=guardian_id))

    selected_user = None
    user_history = None
    user_quiz_attempts = None

    if guardian_id:
        selected_user = Guardians.query.get_or_404(guardian_id)
        user_history = HistoricoAcao.query.filter_by(guardian_id=guardian_id).order_by(desc(HistoricoAcao.data_evento)).all()
        user_quiz_attempts = QuizAttempt.query.join(Quiz).filter(QuizAttempt.guardian_id == guardian_id).order_by(desc(QuizAttempt.completed_at)).all()

    all_guardians = Guardians.query.order_by(Guardians.nome).all()

    return render_template('guardians/analytics.html', 
                           active_guardians=active_guardians_count,
                           total_quizzes=total_quizzes_answered,
                           total_reports=total_reports_phishing,
                           avg_score=avg_score,
                           all_guardians=all_guardians,
                           selected_user=selected_user,
                           user_history=user_history,
                           user_quiz_attempts=user_quiz_attempts,
                           total_clicks_phishing=total_clicks_phishing,
                           vulnerable_users=vulnerable_users,
                           vulnerable_depts=vulnerable_depts)

    
##ROTA PRA EDITAR PERFIL

@guardians_bp.route('/meu-perfil/editar', methods=['GET', 'POST'])
@login_required
def edit_profile():
    logged_in_user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if not guardian:
        flash("Perfil de Guardião não pôde ser carregado para edição.", "danger")
        return redirect(url_for('guardians_bp.meu_perfil'))

    earned_insignias = [gi.insignia for gi in guardian.insignias_conquistadas]
    available_colors = {
        'Padrão (Branco)': None, 'Guardião Dourado': '#FFD700', 'Vigilante Prata': '#C0C0C0',
        'Sentinela Bronze': '#CD7F32', 'Cyber Azul': '#00BFFF', 'Hacker Verde': '#39FF14',
        'Ameaça Magenta': '#FF00FF'
    }

    if request.method == 'POST':
        
        # 1. Salva o apelido
        guardian.nickname = request.form.get('nickname')
        
        # 2. Salva a escolha de anonimato (checkbox "Manter perfil anônimo")
        # 'is_anonymous' in request.form retorna True se o checkbox foi marcado, False se não.
        guardian.is_anonymous = 'is_anonymous' in request.form
        
        # 3. Salva a escolha de exibição do nome (checkbox "Exibir nome real")
        # Esta é a coluna que você me informou que já existe.
        guardian.opt_in_real_name_ranking = 'opt_in_real_name_ranking' in request.form
        
        # 4. Salva a insígnia em destaque
        featured_id = request.form.get('featured_insignia_id')
        guardian.featured_insignia_id = int(featured_id) if featured_id else None
        
        # 5. Salva a cor do nome
        selected_color = request.form.get('name_color')
        if selected_color in available_colors.values():
            guardian.name_color = selected_color if selected_color else None
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('guardians_bp.meu_perfil'))

    return render_template('guardians/edit_profile.html', 
                           guardian=guardian, 
                           earned_insignias=earned_insignias,
                           available_colors=available_colors)
    


##PATRULHA DIARIA

@guardians_bp.route('/daily-patrol', methods=['POST'])
@login_required
def daily_patrol():
    user_id = SessionManager.get("user_id")
    guardian = Guardians.query.filter_by(user_id=user_id).first()

    if not guardian:
        return jsonify({"status": "error", "message": "Perfil de Guardião não encontrado."}), 404

    today = date.today()
    if guardian.last_patrol_date == today:
        return jsonify({"status": "error", "message": "Patrulha diária já realizada hoje!"}), 400

    guardian.score_atual = guardian.score_atual or 0
    guardian.current_streak = guardian.current_streak or 0

    base_points = random.randint(1, 10)
    final_points, bonus_points = apply_streak_bonus(guardian, base_points)
    
    messages = [
        f"Você escaneou a rede e encontrou {base_points} vulnerabilidades. Bom trabalho!",
        f"Patrulha concluída! {base_points} ameaças neutralizadas antes de se tornarem um problema.",
        f"Você revisou os logs de acesso e fortaleceu as defesas. A segurança foi reforçada!",
        f"Regras do firewall otimizadas! Você bloqueou {base_points} novas assinaturas de malware.",
        f"Verificação de patches de segurança concluída! {base_points} sistemas críticos foram atualizados.",
        f"Ronda de segurança física completa. {base_points} pontos de acesso foram verificados e estão seguros."
    ]
    selected_message = random.choice(messages)
    
    try:
        guardian.score_atual += final_points
        guardian.last_patrol_date = today 
        update_user_streak(guardian)
        
        descricao = f"Patrulha Diária: {selected_message}"
        
        if bonus_points > 0:
            descricao += f" (Bônus de ofensiva: +{bonus_points} pts)"
            
        history_entry = HistoricoAcao(
            guardian_id=guardian.id, 
            descricao=descricao, 
            pontuacao=final_points
        )
        db.session.add(history_entry)

        level_up, novas_conquistas = atualizar_nivel_usuario(guardian)
        if level_up and guardian.nivel:
            flash(f"Parabéns! Você subiu para o nível {guardian.nivel.nome}!", 'info')
        for conquista_nome in novas_conquistas:
            flash(f"Nova Conquista Desbloqueada: {conquista_nome}!", "success")

        db.session.commit()

        response_data = {
            "status": "success",
            "message": selected_message,
            "base_points": base_points,
            "bonus_points": bonus_points,
            "total_points": final_points,
            "new_achievements": [] # Lista vazia por enquanto
        }
        return jsonify(response_data)

    except Exception as e:
        db.session.rollback()
        print(f"ERRO NA PATRULHA DIÁRIA: {e}")
        return jsonify({"status": "error", "message": "Ocorreu um erro interno."}), 500
    
####REPORT HUB - ANALISE INDIVIDUAL#####
@guardians_bp.route('/admin/relatorios/selecao')
@admin_required
def report_hub():
    """
    Exibe uma página para selecionar um colaborador para gerar um relatório individual.
    """
    # Busca todos os guardiões para a lista, ordenados por nome
    all_guardians = Guardians.query.order_by(Guardians.nome).all()
    
    return render_template('guardians/report_hub.html', all_guardians=all_guardians)


@guardians_bp.route('/admin/relatorio/<int:guardian_id>')
@admin_required
def guardian_report(guardian_id):
    """
    Exibe o relatório de desempenho individual completo de um guardião.
    """
    perfil = Guardians.query.get_or_404(guardian_id)
    
    # --- Busca de Dados ---
    user_history = perfil.historico_acoes.order_by(desc(HistoricoAcao.data_evento)).all()
    user_achievements = perfil.insignias_conquistadas.all()
    user_quiz_attempts = perfil.quiz_attempts.order_by(desc(QuizAttempt.completed_at)).all()
    nivel_atual = perfil.nivel
    total_quizzes = len(user_quiz_attempts)

    # --- LÓGICA DE CÁLCULO CORRIGIDA (EM PYTHON) ---
    perfect_quizzes_count = 0
    soma_scores = 0
    total_pontos_possiveis = 0

    # Percorre as tentativas de quiz para calcular as métricas
    for attempt in user_quiz_attempts:
        if attempt.quiz: # Garante que o quiz não foi deletado
            possible_points = sum(q.points for q in attempt.quiz.questions)
            if possible_points > 0 and attempt.score == possible_points:
                perfect_quizzes_count += 1
            
            soma_scores += attempt.score
            total_pontos_possiveis += possible_points

    media_geral_acertos = (soma_scores / total_pontos_possiveis * 100) if total_pontos_possiveis > 0 else 0

    # Tempo médio de resposta do indivíduo
    user_avg_time_result = db.session.query(
        func.avg(func.timestampdiff(text('SECOND'), QuizAttempt.started_at, QuizAttempt.completed_at))
    ).filter(QuizAttempt.guardian_id == guardian_id, QuizAttempt.completed_at.isnot(None)).scalar()
    user_avg_time = int(user_avg_time_result) if user_avg_time_result else 0
        
    return render_template(
        'guardians/guardian_report.html',
        perfil=perfil,
        total_quizzes=total_quizzes,
        perfect_quizzes_count=perfect_quizzes_count,
        media_geral_acertos=media_geral_acertos,
        user_avg_time=user_avg_time,
        user_history=user_history,
        user_achievements=user_achievements,
        user_quiz_attempts=user_quiz_attempts,
        nivel_atual=nivel_atual
    )