from app import app, db
from application.models import GlobalGameSettings

def seed_reward_settings():
    """
    Popula o banco com as configurações do sistema de Recompensas (Gacha & Economia).
    """
    settings_data = [
        # --- PROBABILIDADES DO DROP (Soma recomendada: 100%) ---
        {
            "key": "SHOP_WEIGHT_COMMON", "value": "60",
            "desc": "Peso (Chance) de aparecer item Comum.", "cat": "SHOP"
        },
        {
            "key": "SHOP_WEIGHT_RARE", "value": "30",
            "desc": "Peso (Chance) de aparecer item Raro.", "cat": "SHOP"
        },
        {
            "key": "SHOP_WEIGHT_EPIC", "value": "8",
            "desc": "Peso (Chance) de aparecer item Épico.", "cat": "SHOP"
        },
        {
            "key": "SHOP_WEIGHT_LEGENDARY", "value": "2",
            "desc": "Peso (Chance) de aparecer item Lendário.", "cat": "SHOP"
        },
        
        # --- CUSTOS DE REROLL ---
        {
            "key": "SHOP_REROLL_BASE_COST", "value": "1",
            "desc": "Custo inicial (GC) para atualizar a loja.", "cat": "SHOP"
        },
        {
            "key": "SHOP_REROLL_MULTIPLIER", "value": "2.0",
            "desc": "Multiplicador de custo a cada reroll (Ex: 2.0 dobra o preço).", "cat": "SHOP"
        }
    ]

    print("Atualizando Configurações de Recompensa...")
    
    count = 0
    for item in settings_data:
        setting = GlobalGameSettings.query.filter_by(setting_key=item['key']).first()
        
        if not setting:
            new_setting = GlobalGameSettings(
                setting_key=item['key'],
                setting_value=item['value'],
                description=item['desc'],
                category=item['cat']
            )
            db.session.add(new_setting)
            count += 1
            print(f"+ Criado: {item['key']}")
        else:
            # Atualiza descrição/categoria se já existir, mas mantém o valor que você editou no painel
            setting.description = item['desc']
            setting.category = item['cat']

    db.session.commit()
    print(f"Concluído! {count} novas configurações inseridas.")

if __name__ == '__main__':
    with app.app_context():
        seed_reward_settings()