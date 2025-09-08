# modules/guardians/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import  current_user
from modules.login.decorators import login_required, admin_required
from modules.login.session_manager import SessionManager
from sqlalchemy import func, desc, and_, not_
from application.models import db, Guardians, HistoricoAcao, NivelSeguranca, GuardianInsignia, Insignia, EventoPontuacao, Quiz, Question, AnswerOption, QuizCategory, QuizAttempt
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
import re
from sqlalchemy.orm import joinedload


guardians_bp = Blueprint('guardians_bp', __name__)

def atualizar_nivel_usuario(perfil_guardian):
    """
    Verifica se o usuário subiu ou desceu de nível e atualiza o perfil.
    Agora lida com pontuações negativas, atribuindo o nível mais baixo.
    """
    # 1. Tenta encontrar o nível mais alto que a pontuação atual alcança.
    novo_nivel = NivelSeguranca.query.filter(
        NivelSeguranca.score_minimo <= perfil_guardian.score_atual
    ).order_by(desc(NivelSeguranca.score_minimo)).first()

    # 2. Se nenhum nível for encontrado (score < 0), busca o nível mais baixo existente.
    if not novo_nivel:
        novo_nivel = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo.asc()).first()
    
    # 3. Se o nível mudou (e existe um novo nível para atribuir), atualiza o perfil.
    if perfil_guardian.nivel != novo_nivel and novo_nivel is not None:
        perfil_guardian.nivel = novo_nivel
        return True # Retorna True para indicar que houve uma mudança.
        
    return False


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

    # --- O resto da sua lógica para buscar dados pode continuar a partir daqui ---
    # (Ela já estava correta, apenas simplifiquei a parte de busca do perfil)

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

    return render_template(
        'guardians/meu_perfil.html',
        perfil=perfil_guardian,
        is_own_profile=is_own_profile,
        historico=historico_paginado,
        pagination=pagination,
        insignias_ganhas=insignias_ganhas,
        nivel_atual=nivel_atual,
        proximo_nivel=proximo_nivel,
        progresso_percentual=progresso_percentual,
        ranking_atual=ranking_atual,
        numero_conquistas=numero_conquistas,
        quizzes_respondidos_count=quizzes_respondidos_count
    )




@guardians_bp.route('/rankings')
@login_required # Usando o decorator correto que usa o SessionManager
def rankings():
    # --- LÓGICA CORRIGIDA PARA IDENTIFICAR O USUÁRIO ---
    
    # 1. Em vez de usar current_user, buscamos o ID do usuário logado na sessão.
    logged_in_user_id = SessionManager.get("user_id")
    
    # 2. Com o ID do usuário, encontramos o perfil de guardião correspondente.
    guardian_logado = Guardians.query.filter_by(user_id=logged_in_user_id).first()
    
    # 3. Pegamos o ID do guardião para poder destacá-lo na lista.
    current_guardian_id = guardian_logado.id if guardian_logado else -1

    # --- O RESTO DA FUNÇÃO CONTINUA IGUAL ---

    # Busca o ranking global por PONTOS
    ranking_global = Guardians.query.options(joinedload(Guardians.featured_insignia)).order_by(desc(Guardians.score_atual)).all()

    # Busca o ranking por DIAS DE OFENSIVA (streak)
    ranking_streak = Guardians.query.options(joinedload(Guardians.featured_insignia)).order_by(Guardians.current_streak.is_(None), desc(Guardians.current_streak)).all()

    # Busca o ranking por departamento
    ranking_departamento = db.session.query(
        Guardians.departamento_nome, 
        func.sum(Guardians.score_atual).label('score_total')
    ).group_by(Guardians.departamento_nome).order_by(desc('score_total')).all()

    return render_template('guardians/rankings.html', 
                           ranking_global=ranking_global,
                           ranking_streak=ranking_streak,
                           ranking_departamento=ranking_departamento,
                           # Passa o ID do guardião, e não mais do usuário
                           current_user_id=current_guardian_id)

@guardians_bp.route('/sobre-o-programa')
@login_required
def sobre():
    """
    Busca todos os eventos, níveis e insígnias para exibir
    dinamicamente as regras e a progressão do programa.
    """
    # Busca todos os eventos, ordenando por pontuação (maior primeiro)
    todos_eventos = EventoPontuacao.query.order_by(desc(EventoPontuacao.pontuacao)).all()
    
    # Busca todos os níveis, ordenando pela pontuação mínima necessária
    todos_niveis = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo).all()

    # ADIÇÃO: Busca todas as insígnias (conquistas), ordenando por nome
    todas_insignias = Insignia.query.order_by(Insignia.nome).all()

    return render_template('guardians/sobre_o_programa.html', 
                           eventos=todos_eventos, 
                           niveis=todos_niveis,
                           insignias=todas_insignias)

@guardians_bp.route('/central-de-treinamentos')
@login_required # Usando o decorator correto que usa o SessionManager
def central():
    """
    Esta rota busca os quizzes disponíveis e calcula o tempo de expiração para cada um.
    """
    now = datetime.utcnow()
    
    # --- LÓGICA CORRIGIDA PARA IDENTIFICAR O USUÁRIO ---
    # 1. Busca o ID do usuário na sessão.
    logged_in_user_id = SessionManager.get("user_id")
    
    # 2. Encontra o perfil de guardião correspondente.
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    # Se não encontrar um perfil de guardião para o usuário logado, redireciona.
    if not guardian:
        flash("Perfil de Guardião não encontrado.", "warning")
        return redirect(url_for("home_bp.render_home"))

    guardian_id = guardian.id
    
    # --- O RESTO DA LÓGICA CONTINUA IGUAL ---

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
@admin_required # Usa o decorator de ADMIN para garantir a permissão
def view_quiz(quiz_id):
    """
    Permite que um admin visualize um quiz como se fosse um usuário,
    mas em um modo de pré-visualização (sem poder enviar).
    """
    # A verificação de admin agora é feita pelo decorator, então o 'if' antigo pode ser removido.
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Reutilizamos o mesmo template do usuário, mas passamos uma flag 'is_preview'
    return render_template('guardians/take_quiz.html', quiz=quiz, is_preview=True)

@guardians_bp.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    """
    Mostra a página para responder a um quiz específico.
    """
    quiz = Quiz.query.get_or_404(quiz_id)

    # --- LÓGICA CORRIGIDA PARA IDENTIFICAR O USUÁRIO ---
    # 1. Busca o ID do usuário na sessão.
    logged_in_user_id = SessionManager.get("user_id")
    
    # 2. Encontra o perfil de guardião correspondente.
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    if not guardian:
        flash("Perfil de Guardião não encontrado para o usuário logado.", "danger")
        return redirect(url_for('home_bp.render_home'))

    # 3. Usa o ID do guardião correto para verificar se ele já respondeu ao quiz.
    attempt = QuizAttempt.query.filter_by(guardian_id=guardian.id, quiz_id=quiz.id).first()
    if attempt:
        flash('Você já completou este quiz.', 'warning')
        return redirect(url_for('guardians_bp.central'))

    return render_template('guardians/take_quiz.html', quiz=quiz)


@guardians_bp.route('/quiz/submit', methods=['POST'])
@login_required # Usa o decorator de LOGIN para garantir que o usuário está logado
def submit_quiz():
    """
    Recebe as respostas, calcula a pontuação COM BÔNUS DE OFENSIVA,
    salva o resultado e redireciona.
    """
    try:
        quiz_id = request.form.get('quiz_id')
        quiz = Quiz.query.get(quiz_id)

        # --- LÓGICA CORRIGIDA PARA ENCONTRAR O GUARDIÃO ---
        logged_in_user_id = SessionManager.get("user_id")
        guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

        if not guardian:
            flash("Perfil de Guardião não encontrado.", "danger")
            return redirect(url_for('guardians_bp.central'))
        
        # O resto da sua lógica de cálculo de score continua aqui...
        base_score = 0
        results_details = {}
        submitted_answers = {key: val for key, val in request.form.items() if key.startswith('question_')}

        for question in quiz.questions:
            question_key = f'question_{question.id}'
            submitted_option_id = submitted_answers.get(question_key)
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            is_user_correct = False

            if submitted_option_id and correct_option and int(submitted_option_id) == correct_option.id:
                base_score += question.points
                is_user_correct = True
            
            results_details[question.id] = {
                'submitted_option_id': int(submitted_option_id) if submitted_option_id else None,
                'correct_option_id': correct_option.id if correct_option else None,
                'is_correct': is_user_correct
            }

        final_score, bonus_points = apply_streak_bonus(guardian, base_score)
        
        new_attempt = QuizAttempt(guardian_id=guardian.id, quiz_id=quiz.id, score=base_score)
        db.session.add(new_attempt)

        if final_score > 0:
            descricao = f"Completou o quiz '{quiz.title}' e ganhou {base_score} pontos."
            if bonus_points > 0:
                descricao += f" (+{bonus_points} pts de bônus de ofensiva!)"
            history_entry = HistoricoAcao(guardian_id=guardian.id, descricao=descricao, pontuacao=final_score)
            db.session.add(history_entry)
        
        guardian.score_atual += final_score
        update_user_streak(guardian)
        
        if atualizar_nivel_usuario(guardian):
            if guardian.nivel: # Checagem de segurança
                 flash(f"Parabéns! Você subiu para o nível {guardian.nivel.nome}!", 'info')



        db.session.commit()

        session['quiz_results'] = { 'quiz_id': quiz.id, 'score': base_score, 'bonus': bonus_points, 'total_score': final_score, 'details': results_details, 'total_questions': len(quiz.questions) }
        
        return redirect(url_for('guardians_bp.quiz_result', quiz_id=quiz.id))

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO PROCESSAR O QUIZ: {e}") 
        flash(f'Ocorreu um erro ao processar seu quiz.', 'danger') # Removendo a variável 'e' do flash para uma msg mais limpa
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

                            if atualizar_nivel_usuario(perfil_guardian):
                                flash(f"{perfil_guardian.nome} teve seu nível atualizado para {perfil_guardian.nivel.nome}!", 'info')

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
            descricao = request.form.get('descricao')
            requisito_score_str = request.form.get('requisito_score')
            caminho_imagem = request.form.get('caminho_imagem')

            # Verifica se o campo de pontuação não está vazio
            if requisito_score_str:
                requisito_score = int(requisito_score_str)
            else:
                requisito_score = 0  # Valor padrão para campos opcionais

            if not nome or not caminho_imagem:
                flash('Nome e caminho da imagem da insígnia são obrigatórios.', 'danger')
            else:
                try:
                    nova_insignia = Insignia(nome=nome, descricao=descricao, requisito_score=requisito_score, caminho_imagem=caminho_imagem)
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
                    insignia.nome = request.form.get('nome')
                    insignia.descricao = request.form.get('descricao')
                    # Trata campo de score opcional
                    requisito_score_str = request.form.get('requisito_score')
                    insignia.requisito_score = int(requisito_score_str) if requisito_score_str else 0
                    insignia.caminho_imagem = request.form.get('caminho_imagem')
                    db.session.commit()
                    flash(f"Insígnia '{insignia.nome}' atualizada com sucesso!", 'success')
                except IntegrityError:
                    db.session.rollback()
                    flash(f"Erro: Uma insígnia com o nome '{request.form.get('nome')}' já existe.", 'danger')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ocorreu um erro ao atualizar a insígnia: {e}", 'danger')
            else:
                flash("Insígnia não encontrada.", 'danger')
                
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
            score_atualizado = request.form.get('score_atualizado')
            departamento_atualizado = request.form.get('departamento_atualizado')
            is_admin_check = request.form.get('is_admin') == 'on'
            opt_in_ranking_check = request.form.get('opt_in_ranking') == 'on'
            
            perfil_guardian = Guardians.query.get(perfil_id)
            if perfil_guardian:
                perfil_guardian.score_atual = int(score_atualizado)
                perfil_guardian.departamento_nome = departamento_atualizado
                perfil_guardian.is_admin = is_admin_check
                perfil_guardian.opt_in_real_name_ranking = opt_in_ranking_check
                
                if atualizar_nivel_usuario(perfil_guardian):
                    flash(f"{perfil_guardian.nome} subiu para o nível {perfil_guardian.nivel.nome}!", 'info')

                db.session.commit()
                flash(f"Perfil de {perfil_guardian.nome} atualizado com sucesso!", 'success')
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
                    QuizAttempt.query.filter_by(guardian_id=perfil_id).delete()
 
                    # 4. Zera a pontuação, dias de vigilante e atualiza o nivel
                    perfil_guardian.score_atual = 0
                    atualizar_nivel_usuario(perfil_guardian) # Atualiza para o nível mais baixo
                    perfil_guardian.current_streak = 0
                    perfil_guardian.last_streak_date = None
 
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
                # 1. Criar o objeto Quiz principal
                novo_quiz = Quiz(
                    title=request.form.get('title'),
                    description=request.form.get('description'),
                    activation_date=datetime.strptime(request.form.get('activation_date'), '%Y-%m-%d').date(),
                    duration_days=int(request.form.get('duration_days')),
                    category=QuizCategory[request.form.get('category')]
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
                           total_reports=total_reports_phishing, # Corrigido para usar a nova variável
                           avg_score=avg_score,
                           all_guardians=all_guardians,
                           selected_user=selected_user,
                           user_history=user_history,
                           user_quiz_attempts=user_quiz_attempts,
                           # Novas variáveis para o Widget 2
                           total_clicks_phishing=total_clicks_phishing,
                           vulnerable_users=vulnerable_users,
                           vulnerable_depts=vulnerable_depts)

    
##ROTA PRA EDITAR PERFIL
@guardians_bp.route('/meu-perfil/editar', methods=['GET', 'POST'])
@login_required # O decorator já protege a página
def edit_profile():
    # 1. Busca o ID do usuário na sessão, em vez de usar 'current_user'
    logged_in_user_id = SessionManager.get("user_id")
    
    # 2. Encontra o perfil de guardião associado ao usuário logado
    guardian = Guardians.query.filter_by(user_id=logged_in_user_id).first()

    # Se não encontrar um perfil, redireciona com uma mensagem de erro
    if not guardian:
        flash("Perfil de Guardião não pôde ser carregado para edição.", "danger")
        return redirect(url_for('guardians_bp.meu_perfil'))

    # --- O RESTO DA SUA LÓGICA CONTINUA IGUAL ---
    
    earned_insignias = [gi.insignia for gi in guardian.insignias_conquistadas]

    available_colors = {
        'Padrão (Branco)': None,
        'Guardião Dourado': '#FFD700',
        'Vigilante Prata': '#C0C0C0',
        'Sentinela Bronze': '#CD7F32',
        'Cyber Azul': '#00BFFF',
        'Hacker Verde': '#39FF14',
        'Ameaça Magenta': '#FF00FF'
    }

    if request.method == 'POST':
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

    return render_template('guardians/edit_profile.html', 
                           guardian=guardian, 
                           earned_insignias=earned_insignias,
                           available_colors=available_colors)
    
 
    
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


