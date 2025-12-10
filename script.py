from app import app
from modules.tasks.tasks import repopular_eventos_operador_180d,repopular_eventos_180d, importar_detalhes_chamadas_hoje,importar_registro_chamadas_incremental, processar_e_armazenar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental
from modules.tasks.tasks import importar_performance_operador, importar_detalhes_chamadas, importar_chamados, importar_chamados_debug # Repovoando individualmente
from datetime import date

'''with app.app_context():
    print("Tarefa em execução!")
    repopular_eventos_operador_180d(operador_id=2023, nome_operador='Raysa')'''



with app.app_context():
    print("Tarefa em execução!")
    importar_chamados_debug()


'''with app.app_context():
    importar_detalhes_chamadas(
        operador_id=2021,
        nome_operador="Matheus",
        data_inicio=date(2025, 10, 1),
        data_fim=date(2025, 10, 30)
    )'''

'''with app.app_context():
    registros = importar_performance_operador(
        operador_id=2029,
        nome_operador="Rafael",
        data_inicio=date(2025, 10, 7),
        data_fim=date(2025, 10, 7)
    )
    print(f"Total registros importados: {registros}")'''



