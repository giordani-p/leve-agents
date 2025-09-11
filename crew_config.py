from crewai import Crew

# Agent 00 - Orientador Acadêmico
from agents.advisor_agent import advisor_agent
from tasks.advisor_task import advisor_task

# Agent 01 - Perfilador Psicológico
from agents.psychological_profiler_agent import psychological_profiler_agent
from tasks.psychological_profiler_task import psychological_profiler_task

# Agent 02 - Especialista de Carreira
from agents.career_coach_agent import career_coach_agent
from tasks.career_coach_task import career_coach_task

# Instância separada para cada crew
advisor_crew = Crew(
    agents=[advisor_agent],
    tasks=[advisor_task],
    verbose=True
)

psychological_profiler_crew = Crew(
    agents=[psychological_profiler_agent],
    tasks=[psychological_profiler_task],
    verbose=True
)

career_coach_crew = Crew(
    agents=[career_coach_agent],
    tasks=[career_coach_task],
    verbose=True
)

# Exporta as crews
__all__ = ["advisor_crew", "psychological_profiler_crew", "career_coach_crew"]
