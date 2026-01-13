# modules/guardians/admin_routes.py
import os, uuid, re
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from flask import render_template, request, flash, redirect, url_for, current_app
from sqlalchemy import func, desc, case, text
from sqlalchemy.orm import joinedload, subqueryload
from datetime import date, timedelta, datetime
from .routes import guardians_bp 
from ..login.decorators import login_required, guardian_admin_required
from .logic import atualizar_nivel_usuario
from application.models import (
    db, 
    Guardians, 
    EventoPontuacao, 
    NivelSeguranca, 
    Insignia, 
    GuardianInsignia,
    HistoricoAcao,
    Quiz,
    QuizAttempt,
    Question,
    UserAnswer,
    AnswerOption,
    QuizCategory,
    Specialization,
    Perk,
    SpecializationPerkLevel,
    GlobalGameSettings,
    TermoGame,
    TermoAttempt,
    AnagramGame,
    AnagramWord,
    AnagramAttempt,
    GameSeason,
    FeedbackReport
)



#ROTA PRINCIPAL INTERFACE ADMIN#
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
                    # 1. A pontuação final é exatamente a pontuação base do evento.
                    final_points = evento_selecionado.pontuacao

                    # 2. Atualiza o score do guardião com os pontos diretos.
                    perfil_guardian.score_atual += final_points

                    # 3. Cria uma descrição simples, sem mencionar bônus.
                    descricao = f"{evento_selecionado.nome}: {evento_selecionado.descricao or 'Lançamento administrativo.'}"
                    
                    novo_historico = HistoricoAcao(
                        guardian_id=colaborador_id,
                        descricao=descricao,
                        pontuacao=final_points,
                        data_evento=db.func.now()
                    )
                    db.session.add(novo_historico)

                    # A lógica para atualizar o nível e as conquistas continua, pois a pontuação mudou.
                    level_up, novas_conquistas = atualizar_nivel_usuario(perfil_guardian)
                    if level_up and perfil_guardian.nivel:
                        flash(f"{perfil_guardian.nome} teve seu nível atualizado para {perfil_guardian.nivel.nome}!", 'info')
                    for conquista_nome in novas_conquistas:
                        flash(f"{perfil_guardian.nome} desbloqueou a conquista: {conquista_nome}!", "info")

                    db.session.commit()
                    
                    # 4. Mensagem flash corrigida, sem mencionar bônus.
                    flash(f"Pontuação de {final_points} pts lançada para {perfil_guardian.nome}.", 'success')

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

        ##JOGO DO ANAGRAMA
        elif action == 'create_anagram_game':
            try:
                new_game = AnagramGame(
                    title=request.form.get('title'),
                    description=request.form.get('description'),
                    points_per_word=int(request.form.get('points_per_word')),
                    duration_days=int(request.form.get('duration_days')),
                    time_limit_seconds=int(request.form.get('time_limit_seconds')) if request.form.get('time_limit_seconds') else None
                )
                db.session.add(new_game)
                db.session.commit()
                flash(f'Pacote de Anagrama "{new_game.title}" criado com sucesso! Agora adicione palavras a ele.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar pacote: {e}', 'danger')
            return redirect(url_for('guardians_bp.admin') + '#panel-anagram')
        
        elif action == 'edit_anagram_game':
            game_id = request.form.get('game_id')
            game = AnagramGame.query.get(game_id)
            if game:
                try:
                    game.title = request.form.get('title')
                    game.description = request.form.get('description')
                    game.points_per_word = int(request.form.get('points_per_word'))
                    game.duration_days = int(request.form.get('duration_days'))
                    game.is_active = 'is_active' in request.form
                    

                    value = request.form.get('time_limit_seconds')
                    game.time_limit_seconds = int(value) if value else None
                    
                    db.session.commit()
                    flash('Jogo de Anagrama atualizado com sucesso!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao atualizar o jogo: {e}', 'danger')
            return redirect(url_for('guardians_bp.admin') + '#panel-anagram')
        
        elif action == 'delete_anagram_game':
            game_id = request.form.get('game_id')
            game = AnagramGame.query.get(game_id)
            if game:
                if game.attempts:
                    flash(f'Não é possível excluir o jogo "{game.title}", pois ele já possui tentativas de usuários.', 'warning')
                else:
                    db.session.delete(game)
                    db.session.commit()
                    flash(f'Jogo de Anagrama "{game.title}" excluído com sucesso!', 'success')
            return redirect(url_for('guardians_bp.admin') + '#panel-anagram')

        ##JOGO DO TERMO
        elif action == 'create_termo_game':
            try:
                word = request.form.get('correct_word').upper()
                if not word or not word.isalpha(): # Validação simples
                    flash('A palavra deve conter apenas letras.', 'danger')
                else:
                    new_game = TermoGame(
                        correct_word=word,
                        max_attempts=int(request.form.get('max_attempts')),
                        points_reward=int(request.form.get('points_reward')),
                        time_limit_seconds=int(request.form.get('time_limit_seconds')) if request.form.get('time_limit_seconds') else None
                    )
                    db.session.add(new_game)
                    db.session.commit()
                    flash(f'Novo jogo Termo com a palavra "{word}" criado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao criar jogo: {e}", "danger")
            return redirect(url_for('guardians_bp.admin') + '#panel-termo')

        elif action == 'edit_termo_game':
            game_id = request.form.get('game_id')
            game = TermoGame.query.get(game_id)
            if game:
                try:
                    game.correct_word = request.form.get('correct_word').upper()
                    game.max_attempts = int(request.form.get('max_attempts'))
                    game.points_reward = int(request.form.get('points_reward'))
                    time_limit = request.form.get('time_limit_seconds')
                    game.time_limit_seconds = int(time_limit) if time_limit else None
                    game.is_active = 'is_active' in request.form # Verifica se o checkbox está marcado
                    db.session.commit()
                    flash('Jogo Termo atualizado com sucesso!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao atualizar o jogo: {e}', 'danger')
            else:
                flash('Jogo Termo não encontrado.', 'danger')
            return redirect(url_for('guardians_bp.admin') + '#panel-termo')

        elif action == 'delete_termo_game':
            game_id = request.form.get('game_id')
            game = TermoGame.query.get(game_id)
            if game:
                # Verificação de segurança: não permite excluir se já houver tentativas
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
            return redirect(url_for('guardians_bp.admin') + '#panel-termo')

        ##SISTEMA DE CONQUISTAS##

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
                    # --- Campos existentes ---
                    perfil_guardian.score_atual = int(request.form.get('score_atual'))
                    perfil_guardian.departamento_nome = request.form.get('departamento')
                    perfil_guardian.is_admin = 'is_admin' in request.form
                    perfil_guardian.opt_in_real_name_ranking = 'opt_in_ranking' in request.form

                    # Especialização (Caminho)
                    spec_id = request.form.get('specialization_id')
                    perfil_guardian.specialization_id = int(spec_id) if spec_id else None

                    # Nickname e Anonimato
                    perfil_guardian.nickname = request.form.get('nickname')
                    perfil_guardian.is_anonymous = 'is_anonymous' in request.form

                    # Tokens e Contadores
                    perfil_guardian.retake_tokens = int(request.form.get('retake_tokens'))
                    perfil_guardian.perfect_quiz_cumulative_count = int(request.form.get('perfect_quiz_cumulative_count'))

                    # Insígnia em Destaque e Cor do Nome
                    insignia_id = request.form.get('featured_insignia_id')
                    perfil_guardian.featured_insignia_id = int(insignia_id) if insignia_id else None
                    perfil_guardian.name_color = request.form.get('name_color')

                    # --- Lógica de Ofensiva (já existia, mas mantida) ---
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

                    # --- Atualização de Nível e Conquistas ---
                    level_up, novas_conquistas = atualizar_nivel_usuario(perfil_guardian)
                    if level_up:
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
            return redirect(url_for('guardians_bp.admin') + '#panel-profiles')
    

        elif action == 'zerar_historico':
            perfil_id = request.form.get('perfil_id')
            perfil_guardian = Guardians.query.get(perfil_id)
            if perfil_guardian:
                try:
                    # 1. Apaga históricos simples (sem filhos) em massa
                    HistoricoAcao.query.filter_by(guardian_id=perfil_id).delete()
                    GuardianInsignia.query.filter_by(guardian_id=perfil_id).delete()
                    TermoAttempt.query.filter_by(guardian_id=perfil_id).delete()

                    # 2. Apaga tentativas de Quiz (com filhos) usando o loop seguro
                    attempts_to_delete = QuizAttempt.query.filter_by(guardian_id=perfil_id).all()
                    for attempt in attempts_to_delete:
                        db.session.delete(attempt) # Ativa o 'cascade' e apaga as UserAnswers

                    # 3. Apaga tentativas de Anagrama (com filhos) usando o loop seguro
                    #    (Removemos a linha .delete() em massa que estava causando o conflito)
                    anagram_attempts_to_delete = AnagramAttempt.query.filter_by(guardian_id=perfil_id).all()
                    for attempt in anagram_attempts_to_delete:
                        db.session.delete(attempt) # Ativa o 'cascade'

                    # 4. Zera todos os atributos do Guardião
                    perfil_guardian.score_atual = 0
                    perfil_guardian.current_streak = 0
                    perfil_guardian.last_streak_date = None
                    perfil_guardian.last_patrol_date = None
                    perfil_guardian.featured_insignia_id = None
                    perfil_guardian.perfect_quiz_streak = 0
                    perfil_guardian.retake_tokens = 1
                    perfil_guardian.specialization_id = None
                    perfil_guardian.nivel_id = None
                    perfil_guardian.perfect_quiz_cumulative_count = 0
                    perfil_guardian.name_color = None
                    perfil_guardian.trophy_tier = None
                    
                    db.session.commit()
                    flash(f"O progresso de {perfil_guardian.nome} foi completamente zerado.", 'success')

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
    specializations = Specialization.query.order_by(Specialization.name).all()
    termo_games = TermoGame.query.order_by(TermoGame.created_at.desc()).all()
    anagram_games = AnagramGame.query.order_by(AnagramGame.created_at.desc()).all()


    return render_template('guardians/guardians_admin.html', 
                           colaboradores=colaboradores, 
                           eventos=eventos, 
                           insignias=insignias, 
                           quizzes=quizzes, 
                           specializations=specializations,
                           termo_games=termo_games,
                           anagram_games=anagram_games,
                           date=date)


##nova rota de admin##
@guardians_bp.route('/admin/guardians') # <-- NOVA ROTA
@guardian_admin_required # Use seu decorator de admin
def manage_guardians():
    """ Nova página principal do admin para listar e gerenciar todos os guardiões. """
    
    # Busca todos os guardiões, carregando relacionamentos para eficiência
    try:
        guardians_list = Guardians.query.options(
            joinedload(Guardians.specialization), # Carrega o Caminho
            joinedload(Guardians.nivel)          # Carrega o Nível
        ).order_by(Guardians.nome.asc()).all()
    
    except Exception as e:
        print(f"Erro ao buscar lista de guardiões: {e}")
        flash('Erro ao carregar lista de guardiões.', 'danger')
        guardians_list = []

    # Busca eventos de pontuação para o modal (mesma lógica da sua rota /admin atual)
    eventos_pontuacao = EventoPontuacao.query.order_by(EventoPontuacao.nome.asc()).all()
    # Busca conquistas para o modal (lógica futura)
    todas_as_conquistas = Insignia.query.order_by(Insignia.nome.asc()).all()

    return render_template(
        'guardians/admin_guardians.html',
        guardians=guardians_list,
        eventos=eventos_pontuacao,
        conquistas=todas_as_conquistas
    )