"""
Task do Orientador Educacional - Leve Agents

Define a tarefa de planejamento estratégico de carreira de longo prazo para jovens brasileiros.
Inclui análise completa de perfil, identificação de direções de carreira e criação de roadmap
personalizado com marcos e prazos.

Funcionalidades:
- Análise de perfil completo (acadêmico, habilidades, contexto socioeconômico)
- Identificação de direções de carreira baseadas em dados objetivos
- Criação de roadmap de desenvolvimento com marcos e prazos
- Análise de oportunidades de mercado e tendências
- Estratégias adaptadas para diferentes realidades
- Plano de ação com próximos passos específicos
- Análise de riscos e oportunidades
"""
from crewai import Task
from agents.advisor_agent import advisor_agent

advisor_task = Task(
    name="Planejamento Estratégico de Carreira",
    description=(
        "Analise o perfil completo do jovem e crie um plano estratégico de carreira de longo prazo. "
        "Se um snapshot for fornecido em {snapshot_file}, leia o arquivo JSON e use todas as informações disponíveis: "
        "situação acadêmica, objetivos, habilidades, barreiras, contexto socioeconômico, perfil DISC, "
        "talentos CliftonStrengths e aspirações profissionais. Se apenas interesse/preferência for fornecido, "
        "adapte para essas informações. Considere o foco específico ({foco_especifico}) e prioridade ({prioridade_urgencia}). "
        "Crie um plano estratégico que inclua: "
        "- Análise do perfil e identificação de direções de carreira "
        "- Roadmap de desenvolvimento com marcos e prazos "
        "- Identificação de oportunidades de mercado e tendências "
        "- Estratégias adaptadas para diferentes realidades: acadêmica, técnica, artística, empreendedora "
        "- Plano de ação com próximos passos específicos e priorizados "
        "- Análise de riscos e oportunidades "
        "Para cada direção de carreira, inclua: tipo, título, descrição, requisitos, "
        "prazo estimado, investimento necessário, por que é recomendado, próximos passos "
        "específicos e score de compatibilidade (1-10). "
        "IMPORTANTE: Se precisar buscar informações na web, use a ferramenta de busca com uma string simples, "
        "exemplo: 'cursos técnicos em informática no Brasil' ou 'bolsas de estudo para jovens'."
    ),
    expected_output=(
        "Retorne APENAS um JSON válido (sem texto antes/depois). "
        "Regras: (1) Máximo 5 itens em 'options'; (2) 'rank' único ∈ {1,2,3,4,5}; "
        "(3) 'type' deve ser um dos tipos de recomendação válidos; (4) 'compatibility_score' ∈ {1,2,3,4,5,6,7,8,9,10}; "
        "(5) se um dado não existir, use 'não informado' ou null (não a string 'null'); (6) 'sources[*].accessed_at' no formato YYYY-MM-DD; "
        "(8) 'type' deve incluir 'estagio' como opção válida; "
        "(7) 'nivel_prioridade' ∈ {1,2,3,4,5}.\n\n"
        "Formato:\n"
        "```json\n"
        "{"
        "  \"summary\": \"string (2–3 linhas resumindo o plano estratégico)\","
        "  \"profile_analysis\": {"
        "    \"perfil_principal\": \"string\","
        "    \"pontos_fortes\": [\"string\", \"string\", \"string\"],"
        "    \"areas_desenvolvimento\": [\"string\", \"string\", \"string\"],"
        "    \"barreiras_principais\": [\"string\", \"string\", \"string\"],"
        "    \"nivel_prioridade\": 1"
        "  },"
        "  \"options\": ["
        "    {"
        "      \"rank\": 1,"
        "      \"type\": \"curso_graduacao | curso_tecnico | curso_livre | certificacao | empreendedorismo | trabalho_manual | carreira_artistica | apoio_psicologico | orientacao_basica | curso_preparatorio | especializacao\","
        "      \"title\": \"string\","
        "      \"institution\": \"string ou null\","
        "      \"modality\": \"presencial | ead | hibrido | online | semipresencial ou null\","
        "      \"duration\": \"string ou null\","
        "      \"prerequisites\": \"string\","
        "      \"cost_info\": \"string\","
        "      \"scholarships_info\": \"string\","
        "      \"official_url\": \"https://... ou null\","
        "      \"why_recommended\": \"string\","
        "      \"next_steps\": [\"string\", \"string\", \"string\"],"
        "      \"compatibility_score\": 8"
        "    }"
        "  ],"
        "  \"general_next_steps\": [\"string\", \"string\", \"string\"],"
        "  \"sources\": ["
        "    { \"title\": \"string\", \"url\": \"https://...\", \"accessed_at\": \"YYYY-MM-DD\" }"
        "  ],"
        "  \"personalized_advice\": \"string\","
        "  \"risk_factors\": [\"string\", \"string\"],"
        "  \"opportunities\": [\"string\", \"string\", \"string\"]"
        "}"
        "\n```"
    ),

    # Agente responsável por executar a tarefa
    agent=advisor_agent,

    # Execução síncrona (aguarda a resposta antes de continuar)
    async_execution=False,
)
