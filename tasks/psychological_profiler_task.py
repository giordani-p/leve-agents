# tasks/psychological_profiler_task.py
from crewai import Task
from agents.psychological_profiler_agent import psychological_profiler_agent

psychological_profiler_task = Task(
    name="Análise Psicológica e Comportamental",
    description=(
        "Analise o snapshot do jovem e gere insights psicológicos profundos que complementem os dados objetivos. "
        "Foque em: motivações, valores, estilos comportamentais, preferências de trabalho e necessidades de desenvolvimento. "
        "Use DISC e CliftonStrengths do snapshot como base, integrando-os de forma coerente. "
        "Seja conciso e focado nos aspectos mais relevantes para orientação personalizada. "
    ),

    expected_output=(
        "Retorne APENAS um JSON com os seguintes campos:\n\n"
        "- perfil_psicologico: string. Resumo integrado do perfil psicológico\n"
        "- motivacoes_principais: lista. Principais motivações (máx 3)\n"
        "- valores_core: lista. Valores fundamentais (máx 3)\n"
        "- estilo_aprendizado: string. Estilo dominante (visual/auditivo/cinestesico/leitura)\n"
        "- estilo_comunicacao: string. Estilo preferido (direto/diplomatico/detalhado/conciso)\n"
        "- estilo_lideranca: string. Estilo natural (autoritario/democratico/laissez-faire/servidor)\n"
        "- ambiente_ideal: objeto. {estruturado: boolean, flexivel: boolean, colaborativo: boolean, independente: boolean}\n"
        "- modalidade_trabalho: string. Preferida (presencial/remoto/hibrido)\n"
        "- tipo_atividade: string. Preferida (analitica/criativa/social/tecnica)\n"
        "- tolerancia_risco: string. Nível (baixa/media/alta)\n"
        "- gatilhos_estresse: lista. Principais gatilhos (máx 3)\n"
        "- areas_desenvolvimento: lista. Áreas prioritárias (máx 3)\n"
        "- pontos_fortes: lista. Principais pontos fortes (máx 3)\n"
        "- desafios_comportamentais: lista. Desafios principais (máx 3)\n"
        "- perfis_carreira_compativel: lista. Perfis compatíveis (máx 3)\n"
        "- estrategias_personalizacao: lista. Estratégias de personalização (máx 3)\n"
        "- alertas_importantes: lista. Alertas comportamentais (máx 3)\n"
        "- interpretacao_talentos: string. Interpretação dos talentos CliftonStrengths\n"
        "- integracao_metodologias: string. Como DISC e CliftonStrengths se complementam\n\n"
        "Regras: Use apenas texto simples, seja conciso, foque no essencial para orientação personalizada.\n"
    ),
    agent=psychological_profiler_agent,
    async_execution=False,
)