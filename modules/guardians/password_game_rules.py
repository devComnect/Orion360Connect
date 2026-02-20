import random
import re, math
from application.models import db, PasswordGameConfig

# --- FUNÇÕES AUXILIARES DE MATEMÁTICA ---
def get_digits(password):
    """Extrai todos os dígitos individuais da senha como lista de inteiros."""
    return [int(d) for d in password if d.isdigit()]

def rule_sum_15(password):
    digits = get_digits(password)
    return sum(digits) == 15

def rule_sum_25(password):
    digits = get_digits(password)
    return sum(digits) == 25

def rule_sum_40(password):
    digits = get_digits(password)
    return sum(digits) == 40

def rule_sub_first_last_2(password):
    # O primeiro menos o último deve ser 2
    digits = get_digits(password)
    if len(digits) < 2: return False
    return (digits[0] - digits[-1]) == 2

def rule_sub_last_first_3(password):
    # O último menos o primeiro deve ser 3
    digits = get_digits(password)
    if len(digits) < 2: return False
    return (digits[-1] - digits[0]) == 3


# ==============================================================================
# BANCO DE REGRAS (REGEX-ONLY)
# ==============================================================================
PASSWORD_RULES_DB = {
    # --- FÁCIL ---
    101: {"id": 101, "diff": "easy", "desc": "Mínimo de 8 caracteres.", "regex": r"^.{8,}$"},
    102: {"id": 102, "diff": "easy", "desc": "Pelo menos um número.", "regex": r"\d"},
    103: {"id": 103, "diff": "easy", "desc": "Pelo menos uma letra maiúscula.", "regex": r"[A-Z]"},
    104: {"id": 104, "diff": "easy", "desc": "Pelo menos um caractere especial (!@#$).", "regex": r"[!@#$%^&*(),.?\":{}|<>]"},
    105: {"id": 105, "diff": "easy", "desc": "Pelo menos duas letras minúsculas.", "regex": r"(?:[a-z].*){2}"},
    106: {"id": 106, "diff": "easy", "desc": "Deve começar com uma letra.", "regex": r"^[a-zA-Z]"},
    107: {"id": 107, "diff": "easy", "desc": "Deve conter um hífen (-) ou underline (_).", "regex": r"[-_]"},
    108: {"id": 108, "diff": "easy", "desc": "Máximo de 20 caracteres.", "regex": r"^.{0,20}$"},
    109: {"id": 109, "diff": "easy", "desc": "Pelo menos dois números.", "regex": r"(?:\d.*){2}"},

    # --- MÉDIO ---
    201: {"id": 201, "diff": "medium", "desc": "Deve conter o ano atual (2025).", "regex": r"2025"},
    202: {"id": 202, "diff": "medium", "desc": "Deve começar com 'CMD' ou 'ROOT'.", "regex": r"^(CMD|ROOT)"},
    203: {"id": 203, "diff": "medium", "desc": "Deve terminar com três números.", "regex": r"\d{3}$"},
    204: {"id": 204, "diff": "medium", "desc": "Não pode conter espaços.", "regex": r"^[^ ]*$"},
    205: {"id": 205, "diff": "medium", "desc": "Deve conter uma extensão de script (.PY, .SH, .BAT).", "regex": r"\.(PY|SH|BAT)"},
    206: {"id": 206, "diff": "medium", "desc": "Deve conter 'ADMIN' ou 'USER'.", "regex": r"(ADMIN|USER)"},
    207: {"id": 207, "diff": "medium", "desc": "Deve conter o operador matemático '+' ou '='.", "regex": r"[+=]"},
    208: {"id": 208, "diff": "medium", "desc": "Deve conter exatamente 18 caracteres.", "regex": r"^.{18}$"},
    209: {"id": 209, "diff": "medium", "desc": "Deve conter três caracteres repetidos em sequência (Ex: AAA, 111).", "regex": r"(.)\1\1"},

    # --- DIFÍCIL ---
    301: {"id": 301, "diff": "hard", "desc": "Deve conter um protocolo (HTTP, FTP, SSH, TELNET).", "regex": r"(HTTP|FTP|SSH|TELNET)"},
    302: {"id": 302, "diff": "hard", "desc": "Deve conter 'SUDO' em maiúsculas.", "regex": r"SUDO"},
    303: {"id": 303, "diff": "hard", "desc": "Deve conter um numeral romano (I, V, X, L, C).", "regex": r"[IVXLC]"},
    304: {"id": 304, "diff": "hard", "desc": "Deve conter uma porta comum (80, 443, 21, 22).", "regex": r"(80|443|21|22)"},
    305: {"id": 305, "diff": "hard", "desc": "Deve conter um comando SQL (SELECT, DROP, INSERT).", "regex": r"(SELECT|DROP|INSERT)"},
    306: {"id": 306, "diff": "hard", "desc": "Deve conter um formato de email básico (@dominio).", "regex": r"@\w+\."},
    307: {"id": 307, "diff": "hard", "desc": "Deve conter 'TRUE' ou 'FALSE'.", "regex": r"(TRUE|FALSE)"},
    308: {"id": 308, "diff": "hard", "desc": "Deve conter um comando Linux (LS, CD, MKDIR, RM).", "regex": r"(LS|CD|MKDIR|RM)"},

    # --- INSANO ---
    401: {"id": 401, "diff": "insane", "desc": "Formato de IP (Ex: 192.168.1.1).", "regex": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"},
    402: {"id": 402, "diff": "insane", "desc": "Deve conter um código Hexadecimal de cor (Ex: #FFFFFF).", "regex": r"#[0-9A-Fa-f]{6}"},
    403: {"id": 403, "diff": "insane", "desc": "NÃO pode conter a palavra 'SENHA'.", "regex": r"^((?!SENHA).)*$"},
    404: {"id": 404, "diff": "insane", "desc": "Deve conter uma tag HTML de abertura (Ex: <DIV>, <BR>).", "regex": r"<[A-Z]+>"},
    405: {"id": 405, "diff": "insane", "desc": "Deve conter um formato de versão (vX.X.X).", "regex": r"v\d+\.\d+\.\d+"},
    406: {"id": 406, "diff": "insane", "desc": "Deve conter uma porta lógica (AND, OR, XOR, NOT).", "regex": r"\b(AND|OR|XOR|NOT)\b"},
    407: {"id": 407, "diff": "insane", "desc": "Deve conter formato de moeda ($99.99).", "regex": r"\$\d+\.\d{2}"},
    408: {"id": 408, "diff": "insane", "desc": "NÃO pode as conter vogais (A, E, I).", "regex": r"^[^AEIaei]*$"},

    500: {
        "id": 500, "diff": "medium", 
        "template": "A soma de todos os números deve ser igual a {}.", 
        "js_type": "sum"
    },
    501: {
        "id": 501, "diff": "hard", 
        "template": "O primeiro número menos o último deve ser igual a {}.", 
        "js_type": "sub_first_last"
    },
    502: {
        "id": 502, "diff": "hard", 
        "template": "O último número menos o primeiro deve ser igual a {}.", 
        "js_type": "sub_last_first"
    }
}



def get_game_config():
    """Busca a configuração no banco ou cria a padrão se não existir."""
    config = PasswordGameConfig.query.first()
    if not config:
        config = PasswordGameConfig() # Usa os defaults do Model
        db.session.add(config)
        db.session.commit()
    return config

def generate_rules_sequence():
    config = get_game_config()
    selected_rules = [] # Vai guardar strings como "101" ou "500:27"

    # 1. GERAR REGRA MATEMÁTICA DINÂMICA
    math_ids = [k for k in PASSWORD_RULES_DB.keys() if k >= 500]
    
    if math_ids:
        mid = random.choice(math_ids)
        
        # Gera valor aleatório baseado no tipo
        val = 0
        if mid == 500: # Soma
            val = random.randint(15, 50) 
        elif mid in [501, 502]: # Subtração (diferença pequena)
            val = random.randint(1, 8)
            
        # Salva no formato "ID:VALOR" (ex: "500:27")
        selected_rules.append(f"{mid}:{val}")

    # 2. SORTEIO DAS DEMAIS (Regex)
    keys_by_diff = {'easy': [], 'medium': [], 'hard': [], 'insane': []}
    for k, v in PASSWORD_RULES_DB.items():
        if k < 500: 
            keys_by_diff[v['diff']].append(str(k)) # Salva como string

    def safe_sample(pool, k):
        return random.sample(pool, min(len(pool), k))

    selected_rules.extend(safe_sample(keys_by_diff['easy'], config.rules_count_easy))
    selected_rules.extend(safe_sample(keys_by_diff['medium'], config.rules_count_medium))
    selected_rules.extend(safe_sample(keys_by_diff['hard'], config.rules_count_hard))
    
    random.shuffle(selected_rules)
    return selected_rules

def get_rules_details(rules_ids_list):
    """
    Transforma a lista ["101", "500:27"] em objetos prontos para o Frontend.
    """
    final_list = []
    
    for item in rules_ids_list:
        # Se for string composta "ID:VAL", separa
        if ":" in str(item):
            rid, val = str(item).split(":")
            rid = int(rid)
            val = int(val)
            
            rule_base = PASSWORD_RULES_DB.get(rid).copy() # Copia para não alterar o original
            
            # Injeta o valor dinâmico
            rule_base['desc'] = rule_base['template'].format(val)
            rule_base['js_val'] = val # Envia para o JS saber o alvo
            
            final_list.append(rule_base)
        else:
            # Regra normal
            rid = int(item)
            rule = PASSWORD_RULES_DB.get(rid)
            if rule: final_list.append(rule)
            
    return final_list

def validate_password_backend(password, rules_ids_list):
    failed_rules = []
    digits = get_digits(password)
    
    for item in rules_ids_list:
        rid = 0
        val = 0
        
        if ":" in str(item):
            rid_str, val_str = str(item).split(":")
            rid = int(rid_str)
            val = int(val_str)
        else:
            rid = int(item)
            
        rule = PASSWORD_RULES_DB.get(rid)
        if not rule: continue

        # Validação Dinâmica
        if rid >= 500:
            passed = False
            if not digits: 
                passed = False
            else:
                if rid == 500: # Soma
                    passed = (sum(digits) == val)
                elif rid == 501: # Subtração First-Last
                    if len(digits) >= 2:
                        passed = (digits[0] - digits[-1] == val)
                elif rid == 502: # Subtração Last-First
                    if len(digits) >= 2:
                        passed = (digits[-1] - digits[0] == val)
            
            if not passed:
                desc = rule['template'].format(val)
                failed_rules.append(desc)
                
        # Validação Regex
        elif 'regex' in rule:
            if not re.search(rule['regex'], password):
                failed_rules.append(rule['desc'])
                
    return (len(failed_rules) == 0), failed_rules