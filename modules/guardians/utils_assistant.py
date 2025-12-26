import random
from application.models import db, Guardians

# --- CONFIGURAÇÃO DOS TEXTOS ---

# --- 1. CONFIGURAÇÃO DOS PERSONAGENS (LORE PACKS) ---

# Configuração do Robô de Tutorial (O Laranja Sorento)
TUTORIAL_BOT_CONFIG = {
    'seed': 'Felix_Tutorial_v2', # Seed que gera um robozinho amigável
    'color': '#ffc107',          # Amarelo/Laranja (Warning/Info)
    'name': 'PROTOCOLO DE INICIAÇÃO'
}

# Pacotes de Lore com personalidades distintas
LORE_PACKS = {
    'SYSTEM': {
        'name': 'OBSERVADOR DO SISTEMA',
        'color': '#ffc107',
        'seed': 'Grey_Logic_Mind', 
        'quotes': [
            "Sistema: A Grid não falha. Ela se adapta.",
            "Histórico: A Ruptura não foi um colapso — foi uma escolha.",
            "Registro: Alguns dados foram apagados para nunca mais serem encontrados.",
            "Sistema: Estabilidade absoluta gera corrupção silenciosa.",
            "Curiosidade: A Grid reage de forma distinta a cada Mentor.",
            "Arquivo Antigo: Nem todos os silêncios são ausência.",
            "Sistema: Aprendizado registrado. Persistência incerta.",
            "Histórico: O ano de 2077 contém lacunas não autorizadas.",
            "Aviso: Dados irrelevantes foram preservados por razões desconhecidas.",
            "Registro Fragmentado: O sistema lembra o que tenta esquecer."
        ]
    },
    'BLUE': {
        'name': 'SENTINELA (DEFENSOR)',
        'color': '#039BE5',
        'seed': 'Sara',
        'quotes': [
            "Sentinela: Proteger é decidir o que deve continuar.",
            "Arquivo Azul: Integridade alta não garante sobrevivência.",
            "Registro Sentinela: O primeiro firewall foi construída com medo humano.",
            "Sistema Azul: Nem toda ameaça vem de fora da Grid.",
            "Sentinela Antigo: A estabilidade pode se tornar prisão.",
            "Histórico: Um Sentinela recusou o reinício. Seu estado é desconhecido.",
            "Aviso Azul: Defender demais pode impedir adaptação.",
            "Curiosidade: Alguns Sentinels ainda escutam comandos obsoletos."
        ]
    },
    'RED': {
        'name': 'INVASORA (HACKER)',
        'color': '#E53935',
        'seed': 'Kingston', 
        'quotes': [
            "Invasor: Um sistema testado sobrevive.",
            "Registro Vermelho: A primeira invasão evitou um colapso maior.",
            "Aviso: Ataque sem aprendizado é ruído.",
            "Histórico: Uma Invasora alcançou o Core por três segundos.",
            "Intruder Antigo: Quebrar é uma forma de entender.",
            "Sistema Vermelho: Nenhum ponto é inalcançável.",
            "Curiosidade: Algumas invasões não possuem origem detectável.",
            "Alerta: Pressão constante altera o comportamento da Grid."
        ]
    },
    'GREY': {
        'name': 'ARQUIETO (GESTOR)',
        'color': '#546E7A', 
        'seed': 'Leo', 
        'quotes': [
            "Arquiteto: O equilíbrio não é neutro — é calculado.",
            "Registro Cinza: Conflito controlado previne extinção.",
            "Sistema Grey: Otimização excessiva gera instabilidade futura.",
            "Arquiteto Antigo: Tudo flui, inclusive o erro.",
            "Histórico: Os Cycles não foram criados para reiniciar — mas para conter.",
            "Aviso: Alterar o fluxo muda destinos.",
            "Curiosidade: Nem todos os dados sobrevivem por mérito.",
            "Registro: O Curador nunca foi confirmado oficialmente."
        ]
    },
    'MYTH': {
        'name': 'ANOMALIA DESCONHECIDA',
        'color': '#d63384',
        'seed': 'Amaya', 
        'quotes': [
            "Lenda: Um Guardian sobreviveu a todos os Cycles registrados.",
            "Registro Corrompido: 'Eles nunca deveriam ter nos dado autonomia.'",
            "Sussurro da Grid: Nem todos os Mentores permanecem humanos.",
            "Arquivo Perdido: Um Cycle terminou sem registro de conflito.",
            "Presságio: Quando a Grid silencia, algo foi arquivado.",
            "Lenda Urbana: Prime Operators influenciam probabilidades futuras.",
            "Aviso Anômalo: Atividade detectada sem Mentor associado.",
            "Registro Selado: AXIOM_RECONVERGENCE permanece inacessível.",
            "Sistema: O próximo Cycle observa.",
            "Grid: Nada é esquecido. Apenas arquivado."
        ]
    }
}

# Tutoriais (Mantidos)
TUTORIALS = {
    'meu_perfil': {
        'id': 'intro_profile',
        'text': "Saudações! Eu sou seu assistente de iniciação. Aqui no seu Perfil, você gerencia sua evolução, escolhe Caminhos e equipa módulos."
    },
    'loja': {
        'id': 'intro_shop',
        'text': "Bem-vindo ao Mercado! Troque suas G-Coins por bônus. Cuidado: alguns itens são instáveis, mas muito poderosos."
    }
    # ... outros tutoriais
}

def get_assistant_data(guardian, page_key):
    """
    Retorna dados do assistente.
    Se for Tutorial -> Usa o Bot Laranja.
    Se for Lore -> Sorteia uma Facção/Personagem e usa o avatar correspondente.
    """
    if not guardian: return None

    seen_data = guardian.tutorials_seen or {}
    tutorial_config = TUTORIALS.get(page_key)
    
    # 1. PRIORIDADE MÁXIMA: Tutorial
    if tutorial_config:
        t_id = tutorial_config['id']
        if str(t_id) not in seen_data:
            return {
                'text': tutorial_config['text'],
                'is_tutorial': True,
                'tutorial_id': t_id,
                'auto_dismiss': False,
                'avatar_seed': TUTORIAL_BOT_CONFIG['seed'],
                'theme_color': TUTORIAL_BOT_CONFIG['color'],
                'title': TUTORIAL_BOT_CONFIG['name']
            }

    # 2. LORE ALEATÓRIA (Chance de 30%)
    CHANCE_DE_LORE = 1 
    
    if random.random() < CHANCE_DE_LORE:
        # Sorteia qual "Pacote de Lore" vai aparecer
        # Podemos colocar pesos aqui se quiser (ex: Myth ser mais raro)
        # Vamos fazer MYTH ser mais raro (10% de chance dentro dos 30%)
        
        pack_keys = ['SYSTEM', 'SYSTEM', 'SYSTEM', 'BLUE', 'RED', 'GREY', 'MYTH'] 
        selected_key = random.choice(pack_keys)
        pack = LORE_PACKS[selected_key]
        
        return {
            'text': random.choice(pack['quotes']),
            'is_tutorial': False,
            'tutorial_id': None,
            'auto_dismiss': True,
            'avatar_seed': pack['seed'],
            'theme_color': pack['color'],
            'title': pack['name']
        }

    return None