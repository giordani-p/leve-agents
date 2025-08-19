# tasks/advisor_task.py
from crewai import Task
from agents.advisor_agent import advisor_agent

advisor_task = Task(
    # Descrição clara (com espaços corretos) e mapeando para os campos do JSON
    name="Recomendação de Cursos de Graduação",
    description=(
        "Com base em {interesse} e {preferencia}, encontre até 3 cursos de graduação no Brasil "
        "que mais se adequem ao perfil do usuário. Para cada curso, inclua: nome, instituição, "
        "modalidade (presencial/ead/hibrido), duração, pré-requisitos, faixa de custo/bolsa (se disponível) "
        "e o link oficial da página do curso. Organize as opções em ranking de relevância e adicione um "
        "summary (2–3 linhas) e next_steps (3 itens) com orientações práticas para o jovem."
    ),

    # Expected output em modo estrito: pedir APENAS JSON válido, sem texto extra
    expected_output=(
        "Retorne APENAS um JSON válido (sem texto antes/depois). "
        "Regras: (1) Máximo 3 itens em 'options'; (2) 'rank' único ∈ {1,2,3}; "
        "(3) 'modality' ∈ {'presencial','ead','hibrido'}; (4) se um dado não existir, use 'não informado'; "
        "(5) 'official_url' deve ser o link oficial da instituição/curso; "
        "(6) 'sources[*].accessed_at' no formato YYYY-MM-DD.\n\n"
        "Formato:\n"
        "```json\n"
        "{"
        "  \"summary\": \"string (2–3 linhas)\","
        "  \"options\": ["
        "    {"
        "      \"rank\": 1,"
        "      \"course_name\": \"string\","
        "      \"institution\": \"string\","
        "      \"modality\": \"presencial | ead | hibrido\","
        "      \"duration\": \"string\","
        "      \"prerequisites\": \"string\","
        "      \"cost_info\": \"string\","
        "      \"scholarships_info\": \"string\","
        "      \"official_url\": \"https://...\","
        "      \"why_top_pick\": \"string\""
        "    }"
        "  ],"
        "  \"next_steps\": [\"string\", \"string\", \"string\"],"
        "  \"sources\": ["
        "    { \"title\": \"string\", \"url\": \"https://...\", \"accessed_at\": \"YYYY-MM-DD\" }"
        "  ]"
        "}"
        "\n```"
    ),

    # Agente responsável por executar a tarefa
    agent=advisor_agent,

    # Execução síncrona (aguarda a resposta antes de continuar)
    async_execution=False,
)
