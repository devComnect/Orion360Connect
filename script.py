from app import app
from modules.tasks.utils import importar_detalhes_chamadas,repopular_eventos_operador_180d,repopular_eventos_180d, importar_detalhes_chamadas_hoje,importar_registro_chamadas_incremental, processar_e_armazenar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental
from datetime import date

'''with app.app_context():
    print("Tarefa em execução!")
    repopular_eventos_operador_180d(operador_id=2023, nome_operador='Raysa')'''



"""with app.app_context():
    print("Tarefa em execução!")
    importar_detalhes_chamadas_hoje()"""


with app.app_context():
    importar_detalhes_chamadas(
        operador_id=2025,
        nome_operador="Danilo",
        data_inicio=date(2024, 9, 1),
        data_fim=date(2024, 9, 30)
    )



