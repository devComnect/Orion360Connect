from app import app
from modules.tasks.utils import repopular_eventos_operador_180d,repopular_eventos_180d, importar_detalhes_chamadas_hoje,importar_registro_chamadas_incremental, processar_e_armazenar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental


with app.app_context():
    print("Tarefa em execução!")
    repopular_eventos_operador_180d(operador_id=2021, nome_operador='Matheus')



