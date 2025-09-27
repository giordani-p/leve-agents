"""
Task do Especialista de Carreira - Leve Agents

Define a tarefa de execução prática para conseguir primeiro emprego para jovens brasileiros.
Foca em ações concretas, acionáveis e imediatas com conselhos práticos testados.

Funcionalidades:
- Conselhos práticos sobre currículo e portfólio
- Preparação para entrevistas e processos seletivos
- Estratégias de networking e aplicações
- Negociação salarial e primeiros dias no trabalho
- Personalização baseada no perfil do usuário
- Instruções específicas com exemplos práticos
- Recursos concretos e acionáveis
"""
from crewai import Task
from agents.career_coach_agent import career_coach_agent

career_coach_task = Task(
    name="Execução Prática para Primeiro Emprego",
    description=(
        "Responda à pergunta do usuário ({question}) com foco em execução prática para conseguir primeiro emprego. "
        "Se um perfil estiver disponível ({profile_snapshot}), use essas informações para personalizar a resposta. "
        "Caso contrário, forneça conselhos gerais e práticos. "
        "É fundamental que a resposta seja **altamente prática e acionável**, fornecendo passos concretos que o jovem pode executar imediatamente. "
        "Se houver informações do perfil, identifique as âncoras relevantes (área de interesse, habilidades, contexto) e use-as para personalizar as ações práticas. "
        "**Foque em 'como fazer' ao invés de 'o que fazer'** - forneça instruções específicas, exemplos práticos e recursos concretos. "
        "A resposta deve ser organizada de forma didática, usando **títulos, listas numeradas e exemplos práticos**. "
        "O tom deve ser encorajador e prático, mostrando que conseguir primeiro emprego é possível com as ações certas."
    ),
    expected_output=(
        "Retorne EXCLUSIVAMENTE um JSON válido, sem nenhum texto antes ou depois. "
        "Siga as regras rigorosamente: (1) 'short_answer' ≤ 240 caracteres; (2) 'resources' com no máximo 5 itens; (3) 'type' ∈ {'template','article','video','checklist'}; (4) 'url' é opcional e apenas para links da web; (5) se a pergunta fugir do escopo, use status='fora_do_escopo' com uma breve instrução para o usuário; (6) se houver `profile_snapshot` disponível, o 'detailed_answer' deve usar pelo menos 1 dado do perfil de forma explícita; caso contrário, forneça conselhos gerais e práticos. O conteúdo do 'detailed_answer' deve ser rico, com listas e exemplos práticos para ser mais fácil de ler."
        "\n\nFormato JSON:\n"
        "```json\n"
        "{\n"
        "  \"status\": \"ok\" | \"fora_do_escopo\",\n"
        "  \"short_answer\": \"string (até 240 caracteres)\",\n"
        "  \"detailed_answer\": \"string (explicação clara, com listas e exemplos)\",\n"
        "  \"resources\": [\n"
        "    { \"title\": \"string\", \"type\": \"template | article | video | checklist\", \"url\": \"https://...\" }\n"
        "  ]\n"
        "}\n"
        "```\n"
    ),
    agent=career_coach_agent,
    async_execution=False,
)
