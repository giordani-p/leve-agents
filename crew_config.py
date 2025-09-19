"""
Configuração das Crews - Leve Agents

Define as crews especializadas do sistema, cada uma com um agente e tarefa específicos.
Cada crew opera independentemente para maximizar especialização e performance.

Crews disponíveis:
- advisor_crew: Planejamento estratégico de carreira
- psychological_profiler_crew: Análise psicológica e comportamental  
- career_coach_crew: Execução prática para primeiro emprego
"""

from crewai import Crew

# Agent 00 - Orientador Educacional (Planejamento Estratégico)
from agents.advisor_agent import advisor_agent
from tasks.advisor_task import advisor_task

# Agent 01 - Perfilador Psicológico (Análise Comportamental)
from agents.psychological_profiler_agent import psychological_profiler_agent
from tasks.psychological_profiler_task import psychological_profiler_task

# Agent 02 - Especialista de Carreira (Execução Prática)
from agents.career_coach_agent import career_coach_agent
from tasks.career_coach_task import career_coach_task

# Instâncias separadas para cada crew (especialização independente)
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
