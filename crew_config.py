# crew_config.py
from crewai import Crew

# Agent 0 - Orientador Acadêmico
from agents.advisor_agent import advisor_agent
from tasks.advisor_task import advisor_task

# Agent 01 - Perfilador Educacional
from agents.insight_profiler_agent import insight_profiler_agent
from tasks.insight_profiler_task import insight_profiler_task

# Instância separada para cada crew
advisor_crew = Crew(
    agents=[advisor_agent],
    tasks=[advisor_task],
    verbose=True
)

insight_profiler_crew = Crew(
    agents=[insight_profiler_agent],
    tasks=[insight_profiler_task],
    verbose=True
)

# Exporta as duas crews
__all__ = ["advisor_crew", "insight_profiler_crew"]
