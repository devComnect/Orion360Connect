from app import app
from modules.tasks.relatorios.utils import processar_e_armazenar_eventos, importar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental


with app.app_context():
    print("Tarefa em execução!")
    processar_e_armazenar_eventos()