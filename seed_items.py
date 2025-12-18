from app import app, db
from application.models import ShopItem  # Certifique-se que o import está correto


def seed_shop_items():
    """
    Popula a tabela shop_items com base na classe ShopItem fornecida.
    """
    with app.app_context():
        print("--- Iniciando Seed da Loja ---")
        
        # Limpa itens antigos para evitar duplicatas
        print("Apagando itens antigos...")
        try:
            db.session.query(ShopItem).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao limpar tabela: {e}")

        items_data = [
            # =========================================
            # CONSUMÍVEIS (Retakes) - Limite: Infinito
            # =========================================
            {
                "name": "Token de Retake (Quiz) I",
                "description": "Fragmento de memória volátil. Permite refazer 1 Quiz falho.\n'Uma segunda chance concedida pelo sistema.'",
                "category": "Consumíveis",
                "cost": 15,
                "image_path": "bi bi-arrow-counterclockwise",
                "bonus_type": "retake_quiz",
                "bonus_value": 1.0,
                "rarity": "COMMON",
                "purchase_limit": None
            },
            {
                "name": "Pack de Retake (Quiz) II",
                "description": "Backup robusto. Contém 3 chances de refazer Quizzes.\n'Mentores experientes sempre mantêm backups.'",
                "category": "Consumíveis",
                "cost": 40,
                "image_path": "bi bi-database-add",
                "bonus_type": "retake_quiz",
                "bonus_value": 3.0,
                "rarity": "RARE",
                "purchase_limit": None
            },
            {
                "name": "Token de Retake (Minigame) I",
                "description": "Reinicia o loop lógico de um minigame perdido.\n'Falha no sistema detectada. Reiniciando protocolo...'",
                "category": "Consumíveis",
                "cost": 20,
                "image_path": "bi bi-controller",
                "bonus_type": "retake_minigame",
                "bonus_value": 1.0,
                "rarity": "COMMON",
                "purchase_limit": None
            },
            {
                "name": "Pack de Retake (Minigame) II",
                "description": "Cluster de processamento extra. Garante 3 tentativas em minigames.\n'A persistência é a chave da defesa.'",
                "category": "Consumíveis",
                "cost": 50,
                "image_path": "bi bi-joystick",
                "bonus_type": "retake_minigame",
                "bonus_value": 3.0,
                "rarity": "RARE",
                "purchase_limit": None
            },

            # =========================================
            # EQUIPAMENTOS - COOKIE (Bônus XP Quiz) - Limite: 1
            # =========================================
            {
                "name": "Cookie de Acesso I",
                "description": "Sobras da velha cantina. +2% de XP em Quizzes.\n'Tem gosto de café frio e vitória.'",
                "category": "Equipamentos",
                "cost": 20,
                "image_path": "bi bi-cookie",
                "bonus_type": "bonus_quiz",
                "bonus_value": 2.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Cookie de Acesso II",
                "description": "Receita otimizada. +5% de XP em Quizzes.\n'Energia pura para processamento neural.'",
                "category": "Equipamentos",
                "cost": 50,
                "image_path": "bi bi-box-seam",
                "bonus_type": "bonus_quiz",
                "bonus_value": 5.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },
            {
                "name": "Cookie de Acesso III",
                "description": "Raridade pré-Grande Guerra. +10% de XP em Quizzes.\n'Dizem que um desses alimentava um servidor por dias.'",
                "category": "Equipamentos",
                "cost": 100,
                "image_path": "bi bi-gem",
                "bonus_type": "bonus_quiz",
                "bonus_value": 10.0,
                "rarity": "EPIC",
                "purchase_limit": 1
            },

            # =========================================
            # EQUIPAMENTOS - CERTIFICADO (Bônus Decriptar)
            # =========================================
            {
                "name": "Certificado Digital I",
                "description": "Validação básica. +3% de chance/pontos no Decriptar.\n'Assinado digitalmente por um bot júnior.'",
                "category": "Equipamentos",
                "cost": 20,
                "image_path": "bi bi-file-earmark-check",
                "bonus_type": "bonus_decriptar",
                "bonus_value": 3.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Certificado Digital II",
                "description": "Criptografia avançada. +7% de chance/pontos no Decriptar.\n'Usado pela elite da segurança.'",
                "category": "Equipamentos",
                "cost": 50,
                "image_path": "bi bi-file-earmark-lock2",
                "bonus_type": "bonus_decriptar",
                "bonus_value": 7.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },
            {
                "name": "Certificado Digital III",
                "description": "Chave Mestra Root. +12% de chance/pontos no Decriptar.\n'Acesso irrestrito aos segredos profundos.'",
                "category": "Equipamentos",
                "cost": 100,
                "image_path": "bi bi-patch-check-fill",
                "bonus_type": "bonus_decriptar",
                "bonus_value": 12.0,
                "rarity": "EPIC",
                "purchase_limit": 1
            },

            # =========================================
            # EQUIPAMENTOS - CADERNO DNS (Bônus Termo)
            # =========================================
            {
                "name": "Caderno de DNS I",
                "description": "Anotações de novato. +3% de pontos no Termo.\n'Se não está no DNS, não existe.'",
                "category": "Equipamentos",
                "cost": 20,
                "image_path": "bi bi-journal",
                "bonus_type": "bonus_termo",
                "bonus_value": 3.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Caderno de DNS II",
                "description": "Logs de servidor antigo. +8% de pontos no Termo.\n'Mapeando a rede, um IP de cada vez.'",
                "category": "Equipamentos",
                "cost": 50,
                "image_path": "bi bi-journal-code",
                "bonus_type": "bonus_termo",
                "bonus_value": 8.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },

            # =========================================
            # EQUIPAMENTOS - FAREJO (Bônus Patrulha)
            # =========================================
            {
                "name": "Algoritmo Farejador I",
                "description": "Script simples de busca. +3% recompensa na Patrulha.\n'Encontra falhas óbvias em segundos.'",
                "category": "Equipamentos",
                "cost": 20,
                "image_path": "bi bi-search",
                "bonus_type": "bonus_patrulha",
                "bonus_value": 3.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Algoritmo Farejador II",
                "description": "Heurística avançada. +8% recompensa na Patrulha.\n'Nenhum pacote malicioso passa despercebido.'",
                "category": "Equipamentos",
                "cost": 50,
                "image_path": "bi bi-binoculars-fill",
                "bonus_type": "bonus_patrulha",
                "bonus_value": 8.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },

            # =========================================
            # EQUIPAMENTOS - ENGRENAGEM (Bônus Perfeição)
            # =========================================
            {
                "name": "Engrenagem de Precisão I",
                "description": "Calibrada manualmente. +5% bônus ao acertar 100%.\n'A perfeição exige as ferramentas certas.'",
                "category": "Equipamentos",
                "cost": 25,
                "image_path": "bi bi-gear",
                "bonus_type": "bonus_perfeicao",
                "bonus_value": 5.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Engrenagem de Precisão II",
                "description": "Liga resistente a falhas. +10% bônus por perfeição.\n'Gira suavemente, sem atrito, sem erros.'",
                "category": "Equipamentos",
                "cost": 60,
                "image_path": "bi bi-gear-wide-connected",
                "bonus_type": "bonus_perfeicao",
                "bonus_value": 10.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },

            # =========================================
            # EQUIPAMENTOS - SINCRONIZADOR (Velocidade)
            # =========================================
            {
                "name": "Sincronizador Neural I",
                "description": "Overclock leve. +3% bônus por terminar rápido.\n'Pense rápido, aja mais rápido ainda.'",
                "category": "Equipamentos",
                "cost": 20,
                "image_path": "bi bi-stopwatch",
                "bonus_type": "bonus_velocidade",
                "bonus_value": 3.0,
                "rarity": "COMMON",
                "purchase_limit": 1
            },
            {
                "name": "Sincronizador Neural II",
                "description": "Conexão direta de fibra. +8% bônus por terminar rápido.\n'O mundo parece estar em câmera lenta.'",
                "category": "Equipamentos",
                "cost": 50,
                "image_path": "bi bi-lightning-charge-fill",
                "bonus_type": "bonus_velocidade",
                "bonus_value": 8.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },

            # =========================================
            # MINERADORAS (Bônus G-Coins)
            # =========================================
            {
                "name": "Mineradora Legacy I",
                "description": "Hardware antigo. +10% de G-Coins em tudo.\n'Faz barulho e esquenta, mas gera lucro.'",
                "category": "Equipamentos",
                "cost": 80,
                "image_path": "bi bi-cpu",
                "bonus_type": "bonus_coins",
                "bonus_value": 10.0,
                "rarity": "RARE",
                "purchase_limit": 1
            },
            {
                "name": "Mineradora Quantum II",
                "description": "Tecnologia proibida. +25% de G-Coins em tudo.\n'Extrai valor até dos bits descartados.'",
                "category": "Equipamentos",
                "cost": 180,
                "image_path": "bi bi-gpu-card",
                "bonus_type": "bonus_coins",
                "bonus_value": 25.0,
                "rarity": "EPIC",
                "purchase_limit": 1
            },
            {
                "name": "Mineradora 'A Forja' III",
                "description": "Lenda da Dark Web. +50% de G-Coins em tudo.\n'Dizem que imprime dinheiro do próprio ar.'",
                "category": "Equipamentos",
                "cost": 400,
                "image_path": "bi bi-hdd-rack-fill",
                "bonus_type": "bonus_coins",
                "bonus_value": 50.0,
                "rarity": "LEGENDARY",
                "purchase_limit": 1
            },

            # =========================================
            # FIREWALL (Bônus Global)
            # =========================================
            {
                "name": "Firewall Pessoal I",
                "description": "Proteção extra. +5% em TODOS os ganhos de XP.\n'Nada entra sem permissão. Nada sai sem lucro.'",
                "category": "Equipamentos",
                "cost": 150,
                "image_path": "bi bi-shield",
                "bonus_type": "bonus_global",
                "bonus_value": 5.0,
                "rarity": "EPIC",
                "purchase_limit": 1
            },
            {
                "name": "Firewall 'Aégis' II",
                "description": "Escudo definitivo. +10% em TODOS os ganhos de XP.\n'A barreira impenetrável da Grande Guerra.'",
                "category": "Equipamentos",
                "cost": 350,
                "image_path": "bi bi-shield-lock-fill",
                "bonus_type": "bonus_global",
                "bonus_value": 10.0,
                "rarity": "LEGENDARY",
                "purchase_limit": 1
            }
        ]

        print(f"Inserindo {len(items_data)} itens...")

        for data in items_data:
            item = ShopItem(
                name=data['name'],
                description=data['description'],
                category=data['category'],
                cost=data['cost'],
                image_path=data['image_path'],
                bonus_type=data['bonus_type'],
                bonus_value=data['bonus_value'],
                rarity=data['rarity'],
                purchase_limit=data['purchase_limit'],
                duration_days=None,  # Padrão permanente
                is_active=True
            )
            db.session.add(item)
        
        try:
            db.session.commit()
            print("Sucesso! A Loja foi populada.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro no commit: {e}")

if __name__ == "__main__":
    seed_shop_items()