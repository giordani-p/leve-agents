from crewai import Crew

# Importa o agente principal
from agents.advisor_agent import advisor_agent

# Importa a tarefa que será executada pelo agente
from tasks.advisor_task import advisor_task

# Instancia e configura a Crew (time de execução)
crew = Crew(
    agents=[advisor_agent],     # Lista de agentes envolvidos na execução
    tasks=[advisor_task],       # Lista de tarefas atribuídas aos agentes
    verbose=True                # Ativa logs detalhados (útil para debug)
)

# Exporta a variável crew para uso externo (ex: no main.py)
__all__ = ["crew"]
