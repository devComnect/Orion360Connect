from app import db
from application.models import Insignia 

def seed_insignias():
    print(">>> Iniciando seed de Insígnias (Conquistas)...")
    
    DEFAULT_IMG = "img/conquistas/acumulador.png"

    insignias_data = [
        # --- 1. CATEGORIA: POR QUIZ ---
        {
            "nome": "Iniciado da Rede", "achievement_code": "QUIZ_NOVICE_1",
            "descricao": "O primeiro passo para a sabedoria é questionar.\nVocê completou seus primeiros módulos.",
            "bonus_type": "QUIZ_BONUS_PCT", "bonus_value": 2.0
        },
        {
            "nome": "Analista de Protocolos", "achievement_code": "QUIZ_INTERMEDIATE_1",
            "descricao": "Sua dedicação aos estudos foi notada.\nRetenção de dados aumentada.",
            "bonus_type": "QUIZ_BONUS_PCT", "bonus_value": 4.0
        },
        {
            "nome": "Mestre do Conhecimento", "achievement_code": "QUIZ_ADVANCED_1",
            "descricao": "Não há pergunta sem resposta.\nReferência teórica para a equipe.",
            "bonus_type": "QUIZ_BONUS_PCT", "bonus_value": 7.0
        },
        {
            "nome": "Oráculo do Sistema", "achievement_code": "QUIZ_MASTER_1",
            "descricao": "Biblioteca ambulante de cibersegurança.\nProcessamento neural acelerado.",
            "bonus_type": "QUIZ_BONUS_PCT", "bonus_value": 10.0
        },

        # --- 2. CATEGORIA: POR MINIGAME ---
        {
            "nome": "Linguista do DNS", "achievement_code": "MINIGAME_TERMO_PRO",
            "descricao": "Decifrando domínios com precisão cirúrgica.\nVocabulário técnico afiado.",
            "bonus_type": "TERMO_BONUS_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Criptógrafo da Ordem", "achievement_code": "MINIGAME_ANAGRAM_PRO",
            "descricao": "Reorganizando o caos em informação.\nCertificados decifrados.",
            "bonus_type": "ANAGRAM_BONUS_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Quebrador de Cofres", "achievement_code": "MINIGAME_SECRET_PRO",
            "descricao": "Padrões complexos são quebra-cabeças infantis.\nAcesso concedido.",
            "bonus_type": "PW_BONUS_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Processador Neural", "achievement_code": "MINIGAME_SPEED_MASTER",
            "descricao": "Reflexos superam a latência da rede.\Eficiência motora suprema.",
            "bonus_type": "SPEED_BONUS_PCT", "bonus_value": 5.0
        },

        # --- 3. CATEGORIA: POR PATRULHA ---
        {
            "nome": "Vigia Noturno", "achievement_code": "PATROL_ROOKIE",
            "descricao": "Enquanto outros dormem, você monitora.",
            "bonus_type": "PATROL_BONUS_PCT", "bonus_value": 2.5
        },
        {
            "nome": "Olho da Torre", "achievement_code": "PATROL_WATCHER",
            "descricao": "Nada passa despercebido no seu setor.",
            "bonus_type": "PATROL_BONUS_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Sentinela Onipresente", "achievement_code": "PATROL_GUARDIAN",
            "descricao": "Sua presença no sistema é constante como um heartbeat.",
            "bonus_type": "PATROL_BONUS_PCT", "bonus_value": 7.5
        },
        {
            "nome": "Guardião da Fronteira", "achievement_code": "PATROL_LEGEND",
            "descricao": "A primeira e a última linha de defesa.",
            "bonus_type": "PATROL_BONUS_PCT", "bonus_value": 10.0
        },

        # --- 4. CATEGORIA: POR OFENSIVA ---
        {
            "nome": "Conexão Estável", "achievement_code": "STREAK_WEEKLY",
            "descricao": "Sete dias sem falhas de pacote.\nConsistência estabelecida.",
            "bonus_type": "STREAK_BONUS_PCT", "bonus_value": 3.0
        },
        {
            "nome": "Fluxo Contínuo", "achievement_code": "STREAK_MONTHLY",
            "descricao": "Um mês inteiro de dedicação ininterrupta.",
            "bonus_type": "STREAK_BONUS_PCT", "bonus_value": 6.0
        },
        {
            "nome": "Persistência de Dados", "achievement_code": "STREAK_QUARTERLY",
            "descricao": "Faça chuva ou faça sol, o log registra sua presença.",
            "bonus_type": "STREAK_BONUS_PCT", "bonus_value": 9.0
        },
        {
            "nome": "Imortal Digital", "achievement_code": "STREAK_YEARLY",
            "descricao": "O tempo passa, mas sua ofensiva permanece.\nLenda viva.",
            "bonus_type": "STREAK_BONUS_PCT", "bonus_value": 15.0
        },

        # --- 5. CATEGORIA: POR ITEMS ---
        {
            "nome": "Consumidor Beta", "achievement_code": "ITEM_BUYER_1",
            "descricao": "Adquirindo as primeiras ferramentas do ofício.",
            "bonus_type": "GCOIN_BONUS_PCT", "bonus_value": 2.0
        },
        {
            "nome": "Mercador de Bits", "achievement_code": "ITEM_COLLECTOR_1",
            "descricao": "Seu inventário começa a dar inveja aos novatos.",
            "bonus_type": "GCOIN_BONUS_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Magnata do Cyberespaço", "achievement_code": "ITEM_WHALE_1",
            "descricao": "A economia do servidor gira em torno das suas transações.",
            "bonus_type": "GCOIN_BONUS_PCT", "bonus_value": 8.0
        },
        {
            "nome": "Arsenal Completo", "achievement_code": "ITEM_COMPLETIONIST",
            "descricao": "Não há mais nada na loja que você não possua.",
            "bonus_type": "GCOIN_BONUS_PCT", "bonus_value": 12.0
        },

        # --- 6. CATEGORIA: POR DESEMPENHO ---
        {
            "nome": "Agente Promissor", "achievement_code": "LEVEL_10_REACHED",
            "descricao": "Superando a fase de recrutamento com louvor.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 2.0
        },
        {
            "nome": "Operativo de Elite", "achievement_code": "LEVEL_50_REACHED",
            "descricao": "Metade do caminho para a glória.\nExperiência respeitável.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 5.0
        },
        {
            "nome": "Veterano de Guerra", "achievement_code": "SCORE_HIGH_ROLLER",
            "descricao": "Milhares de pontos acumulados em combate real.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 8.0
        },
        {
            "nome": "Singularidade", "achievement_code": "LEVEL_MAX_CAP",
            "descricao": "Você atingiu o teto teórico de performance.\nMais máquina do que humano.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 10.0
        },

        # --- 7. CATEGORIA: POR REPORT DE PHISH ---
        {
            "nome": "Filtro Humano", "achievement_code": "PHISH_DETECT_NOVICE",
            "descricao": "Separando o lixo do que é legítimo.",
            "bonus_type": "PERFECTION_BONUS_PCT", "bonus_value": 3.0
        },
        {
            "nome": "Caçador de Iscas", "achievement_code": "PHISH_DETECT_INTER",
            "descricao": "Identificando armadilhas sociais com facilidade.",
            "bonus_type": "PERFECTION_BONUS_PCT", "bonus_value": 6.0
        },
        {
            "nome": "Terror dos Scammers", "achievement_code": "PHISH_DETECT_ADV",
            "descricao": "Seu nome está na lista negra dos atacantes.",
            "bonus_type": "PERFECTION_BONUS_PCT", "bonus_value": 9.0
        },
        {
            "nome": "Firewall Biológico", "achievement_code": "PHISH_DETECT_MASTER",
            "descricao": "Nenhum e-mail malicioso sobrevive à sua triagem.",
            "bonus_type": "PERFECTION_BONUS_PCT", "bonus_value": 12.0
        },

        # --- 8. CATEGORIA: POR PÓDIO ---
        {
            "nome": "Competidor Nascido", "achievement_code": "PODIUM_TOP_10",
            "descricao": "Entrando no hall da fama, entre os 10 melhores.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 3.0
        },
        {
            "nome": "Medalhista de Bronze", "achievement_code": "PODIUM_TOP_3",
            "descricao": "Um lugar no pódio garantido.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 6.0
        },
        {
            "nome": "Vice-Campeão", "achievement_code": "PODIUM_TOP_2",
            "descricao": "Por um bit não foi o primeiro.\nRival digno.",
            "bonus_type": "GLOBAL_SCORE_PCT", "bonus_value": 9.0
        },
        {
            "nome": "Lenda Viva", "achievement_code": "PODIUM_TOP_1",
            "descricao": "O topo da cadeia alimentar digital.",
            "bonus_type": "ADD_QUIZ_TOKEN", 
            "bonus_value": 1.0 
        }
    ]

    print(f"Preparando para inserir {len(insignias_data)} insígnias...")

    for data in insignias_data:
        insignia = Insignia.query.filter_by(achievement_code=data['achievement_code']).first()
        
        if not insignia:
            insignia = Insignia(
                nome=data['nome'],
                achievement_code=data['achievement_code'],
                descricao=data['descricao'],
                requisito_score=0,
                caminho_imagem=DEFAULT_IMG,
                bonus_type=data['bonus_type'],
                bonus_value=data['bonus_value']
            )
            db.session.add(insignia)
            print(f" [+] CRIADO: {data['nome']}")
        else:
            insignia.nome = data['nome']
            insignia.descricao = data['descricao']
            insignia.bonus_type = data['bonus_type']
            insignia.bonus_value = data['bonus_value']
            insignia.caminho_imagem = DEFAULT_IMG
            print(f" [.] ATUALIZADO: {data['nome']}")

    db.session.commit()
    print(">>> Seed de Insígnias concluído!")

# --- FUNÇÃO PRINCIPAL ESPERADA PELO APP.PY ---
def run_all_seeds():
    """Função entrypoint que o comando 'flask seed' chama."""
    seed_insignias()
    # Se tiver outras funções de seed no futuro (ex: seed_users), chame aqui