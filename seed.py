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