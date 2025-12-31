<<<<<<< HEAD
from app import app, db
from application.models import MissionTemplate, MissionCodeEnum, MissionDifficultyEnum, MissionTypeEnum

def seed_missions():
    """
    Popula o banco de dados com missões variadas e balanceadas.
    Inclui: Ação, Quiz, Minigame, Passivas, Economia e Speedrun.
    """
    
    missions_data = [
        # ==============================================================================
        # MÉDIO (MEDIUM) - Exige um pouco mais de tempo ou habilidade
        # ==============================================================================
        # NOVAS (SPEEDRUN & ECONOMIA)
        {
            "title": "Raciocínio Rápido",
            "desc": "Complete {target} Quizzes em menos de 60 segundos.",
            "code": MissionCodeEnum.QUIZ_SPEEDRUN,
            "diff": MissionDifficultyEnum.MEDIUM,
            "type": MissionTypeEnum.QUIZ,
            "min": 1, "max": 2, "xp": 150
        },
        {
            "title": "Hacker Veloz",
            "desc": "Vença {target} Minigames em tempo recorde (Speedrun).",
            "code": MissionCodeEnum.MINIGAME_SPEEDRUN,
            "diff": MissionDifficultyEnum.MEDIUM,
            "type": MissionTypeEnum.GAME,
            "min": 1, "max": 3, "xp": 150
        },
        {
            "title": "Mercado Negro",
            "desc": "Gaste {target} GC atualizando o estoque da loja (Reroll).",
            "code": MissionCodeEnum.SPEND_GC_REROLL,
            "diff": MissionDifficultyEnum.MEDIUM,
            "type": MissionTypeEnum.ECONOMY,
            "min": 100, "max": 250, "xp": 100
        },

        # ==============================================================================
        # DIFÍCIL (HARD) - Desafios de longo prazo ou alto custo
        # ==============================================================================
        # NOVAS (HARD)
        {
            "title": "Execução Impecável",
            "desc": "Complete {target} desafios (qualquer tipo) sem erros.",
            "code": MissionCodeEnum.ANY_PERFECT_COUNT,
            "diff": MissionDifficultyEnum.HARD,
            "type": MissionTypeEnum.GAME,
            "min": 3, "max": 5, "xp": 300
        },
        {
            "title": "Investidor",
            "desc": "Gaste um total de {target} GC comprando upgrades na loja.",
            "code": MissionCodeEnum.SPEND_GC_UPGRADES,
            "diff": MissionDifficultyEnum.HARD,
            "type": MissionTypeEnum.ECONOMY,
            "min": 300, "max": 500, "xp": 200
        }
    ]

    print(f"Iniciando o Seed de {len(missions_data)} missões...")

    count = 0
    for data in missions_data:
        # Verifica duplicidade pelo título
        exists = MissionTemplate.query.filter_by(title=data["title"]).first()
        
        if not exists:
            new_mission = MissionTemplate(
                title=data["title"],
                description_template=data["desc"],
                mission_code=data["code"],
                difficulty=data["diff"],
                mission_type=data["type"],
                min_target=data["min"],
                max_target=data["max"],
                xp_reward=data["xp"],
                is_active=True
            )
            db.session.add(new_mission)
            count += 1
            print(f" [+] Criada: {data['title']}")
        else:
            print(f" [.] Já existe: {data['title']}")

    db.session.commit()
    print(f"\n--- SUCESSO! {count} novas missões adicionadas ao banco. ---")

if __name__ == '__main__':
    with app.app_context():
        seed_missions()
=======
from app import db
from application.models import Insignia 

def seed_insignias():
    print("--- INICIANDO SEED DE INSÍGNIAS ---")
    
    # Configuração Padrão
    DEFAULT_IMG = "img/conquistas/veterano-de-guerra.png"
    
    # Lista Mestra de Dados
    data = [
        # ==========================================
        # 🟦 TRILHA SCORE (SCORE_)
        # ==========================================
        {
            "code": "SCORE_1",
            "nome": "Primeiro Sinal",
            "desc": "Você deixou de ser ruído e passou a ser detectado pela Grid.",
            "req": 500,
            "b_type": "GLOBAL_SCORE_PCT",
            "b_val": 1.0
        },
        {
            "code": "SCORE_2",
            "nome": "Presença Reconhecida",
            "desc": "Seu padrão começa a se repetir nos registros do sistema.",
            "req": 2500,
            "b_type": "GLOBAL_SCORE_PCT",
            "b_val": 2.0
        },
        {
            "code": "SCORE_3",
            "nome": "Assinatura Estável",
            "desc": "A Grid agora prevê sua atuação antes mesmo do impacto.",
            "req": 5000,
            "b_type": "GLOBAL_SCORE_PCT",
            "b_val": 3.0
        },
        {
            "code": "SCORE_4",
            "nome": "Anomalia Persistente",
            "desc": "Você não é mais exceção — é uma variável permanente.",
            "req": 10000,
            "b_type": "GLOBAL_SCORE_PCT",
            "b_val": 4.0
        },
        {
            "code": "SCORE_5",
            "nome": "Entidade Registrada",
            "desc": "Seu rastro é oficial. Apagar seria custoso demais.",
            "req": 20000,
            "b_type": "GLOBAL_SCORE_PCT",
            "b_val": 5.0
        },

        # ==========================================
        # 🟩 TRILHA QUIZ (QUIZ_COUNT_)
        # ==========================================
        {
            "code": "QUIZ_COUNT_1",
            "nome": "Primeira Validação",
            "desc": "Você respondeu. O sistema escutou.",
            "req": 1,
            "b_type": "QUIZ_BONUS_PCT",
            "b_val": 3.0
        },
        {
            "code": "QUIZ_COUNT_2",
            "nome": "Linha de Raciocínio",
            "desc": "A repetição transformou tentativa em método.",
            "req": 10,
            "b_type": "QUIZ_BONUS_PCT",
            "b_val": 6.0
        },
        {
            "code": "QUIZ_COUNT_3",
            "nome": "Consistência Analítica",
            "desc": "Erros diminuem quando o padrão se consolida.",
            "req": 25,
            "b_type": "QUIZ_BONUS_PCT",
            "b_val": 12.0
        },
        {
            "code": "QUIZ_COUNT_4",
            "nome": "Operador Cognitivo",
            "desc": "Você processa informação como o próprio sistema.",
            "req": 50,
            "b_type": "QUIZ_BONUS_PCT",
            "b_val": 20.0
        },
        {
            "code": "QUIZ_COUNT_5",
            "nome": "Arquitetura Mental",
            "desc": "Conhecimento deixou de ser adquirido — passou a ser produzido.",
            "req": 100,
            "b_type": "QUIZ_BONUS_PCT",
            "b_val": 30.0
        },

        # ==========================================
        # 🟨 TRILHA MINIGAMES (MINIGAME_)
        # ==========================================
        {
            "code": "MINIGAME_1",
            "nome": "Primeiro Protocolo",
            "desc": "Você aceitou o desafio fora da teoria.",
            "req": 1,
            "b_type": "TERMO_BONUS_PCT", # Específico conforme solicitado
            "b_val": 5.0
        },
        {
            "code": "MINIGAME_2",
            "nome": "Decodificador Iniciante",
            "desc": "Padrões começam a ceder sob pressão repetida.",
            "req": 10,
            "b_type": "ANAGRAM_BONUS_PCT",
            "b_val": 5.0
        },
        {
            "code": "MINIGAME_3",
            "nome": "Quebrador de Estruturas",
            "desc": "Sistemas fechados não permanecem fechados por muito tempo.",
            "req": 25,
            "b_type": "PW_BONUS_PCT",
            "b_val": 20.0
        },
        {
            "code": "MINIGAME_4",
            "nome": "Operador de Campo",
            "desc": "Execução eficiente supera tentativa bruta.",
            "req": 50,
            "b_type": "TERMO_BONUS_PCT",
            "b_val": 20.0
        },
        {
            "code": "MINIGAME_5",
            "nome": "Especialista em Ruptura",
            "desc": "Nenhuma cifra resiste à insistência correta.",
            "req": 100,
            "b_type": "ANAGRAM_BONUS_PCT",
            "b_val": 20.0
        },

        # ==========================================
        # 🟥 TRILHA PATRULHA (PATROL_)
        # ==========================================
        {
            "code": "PATROL_1",
            "nome": "Primeira Ronda",
            "desc": "Você saiu do núcleo e tocou o perímetro.",
            "req": 1,
            "b_type": "PATROL_BONUS_PCT",
            "b_val": 5.0
        },
        {
            "code": "PATROL_2",
            "nome": "Vigilância Ativa",
            "desc": "A Grid começa a confiar sua fronteira a você.",
            "req": 7,
            "b_type": "PATROL_BONUS_PCT",
            "b_val": 10.0
        },
        {
            "code": "PATROL_3",
            "nome": "Controle Territorial",
            "desc": "Rotas são seguras porque você passou por elas.",
            "req": 14,
            "b_type": "PATROL_BONUS_PCT",
            "b_val": 20.0
        },
        {
            "code": "PATROL_4",
            "nome": "Zona Sob Observação",
            "desc": "Nada se move sem ser notado.",
            "req": 30,
            "b_type": "PATROL_BONUS_PCT",
            "b_val": 35.0
        },
        {
            "code": "PATROL_5",
            "nome": "Guardião do Perímetro",
            "desc": "O território responde primeiro a você.",
            "req": 60,
            "b_type": "PATROL_BONUS_PCT",
            "b_val": 50.0
        },

        # ==========================================
        # 🟪 TRILHA SHOP (SHOP_)
        # ==========================================
        {
            "code": "SHOP_1",
            "nome": "Primeiro Investimento",
            "desc": "Toda vantagem começa com uma escolha.",
            "req": 1,
            "b_type": "GCOIN_BONUS_PCT",
            "b_val": 5.0
        },
        {
            "code": "SHOP_2",
            "nome": "Otimização Inicial",
            "desc": "Eficiência não é sorte. É acúmulo.",
            "req": 5,
            "b_type": "GCOIN_BONUS_PCT",
            "b_val": 10.0
        },
        {
            "code": "SHOP_3",
            "nome": "Estrutura Aprimorada",
            "desc": "Seu desempenho agora é modular.",
            "req": 10,
            "b_type": "GCOIN_BONUS_PCT",
            "b_val": 15.0
        },
        {
            "code": "SHOP_4",
            "nome": "Arquitetura de Vantagem",
            "desc": "Cada ação rende mais do que antes.",
            "req": 20,
            "b_type": "GCOIN_BONUS_PCT",
            "b_val": 20.0
        },
        {
            "code": "SHOP_5",
            "nome": "Economia de Guerra",
            "desc": "Você não gasta recursos. Você os converte.",
            "req": 50,
            "b_type": "GCOIN_BONUS_PCT",
            "b_val": 25.0
        }
    ]

    # Processamento
    count_created = 0
    count_updated = 0

    try:
        for item in data:
            # Verifica se já existe pelo código único
            insignia = Insignia.query.filter_by(achievement_code=item['code']).first()

            if insignia:
                # Se existe, atualiza os dados para garantir que textos/bônus estejam sincronizados
                insignia.nome = item['nome']
                insignia.descricao = item['desc']
                insignia.requisito_score = item['req'] # Usando campo existente da sua classe
                insignia.caminho_imagem = DEFAULT_IMG
                insignia.bonus_type = item['b_type']
                insignia.bonus_value = item['b_val']
                count_updated += 1
            else:
                # Se não existe, cria
                new_insignia = Insignia(
                    achievement_code=item['code'],
                    nome=item['nome'],
                    descricao=item['desc'],
                    requisito_score=item['req'],
                    caminho_imagem=DEFAULT_IMG,
                    bonus_type=item['b_type'],
                    bonus_value=item['b_val']
                )
                db.session.add(new_insignia)
                count_created += 1
        
        db.session.commit()
        print(f"--- SEED CONCLUÍDO ---")
        print(f"Criados: {count_created}")
        print(f"Atualizados: {count_updated}")

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO RODAR SEED: {e}")

# --- FUNÇÃO PRINCIPAL ESPERADA PELO APP.PY ---
def run_all_seeds():
    """Função entrypoint que o comando 'flask seed' chama."""
    seed_insignias()
    # Se tiver outras funções de seed no futuro (ex: seed_users), chame aqui
>>>>>>> origin/guardians
