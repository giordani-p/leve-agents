from crewai import Task
from agents.career_coach_agent import career_coach_agent

career_coach_task = Task(
    name="Orientações de carreira personalizadas (primeiro emprego)",
    description=(
        "Responda à pergunta do usuário ({question}) considerando as informações do perfil do usuário: {profile_snapshot}. "
        "É fundamental que a resposta seja **altamente personalizada e contextualizada ao perfil do usuário**. Identifique as âncoras relevantes do perfil (como área de interesse, contexto de vida ou objetivos) e use-as para moldar a resposta. **Valide a experiência ou o sentimento do usuário** antes de dar o conselho, mostrando que você compreende a situação. Aja como um mentor, mostrando ao jovem como as experiências que ele já tem são valiosas para a carreira que ele busca. "
        "Ao dar conselhos, faça a 'ponte' entre a experiência do usuário e as habilidades de mercado. Mostre como o trabalho em um ambiente não formal pode ter desenvolvido **habilidades comportamentais** como proatividade e resiliência. "
        "A resposta detalhada deve ser organizada de forma didática, usando **títulos, listas e exemplos práticos**. O tom deve ser de reconhecimento e apoio."
    ),
    expected_output=(
        "Retorne EXCLUSIVAMENTE um JSON válido, sem nenhum texto antes ou depois. "
        "Siga as regras rigorosamente: (1) 'short_answer' ≤ 240 caracteres; (2) 'resources' com no máximo 5 itens; (3) 'type' ∈ {'template','article','video','checklist'}; (4) 'url' é opcional e apenas para links da web; (5) se a pergunta fugir do escopo, use status='fora_do_escopo' com uma breve instrução para o usuário; (6) o 'detailed_answer' deve obrigatoriamente usar pelo menos 1 dado do `profile_snapshot` de forma explícita. O conteúdo do 'detailed_answer' deve ser rico, com listas e exemplos práticos para ser mais fácil de ler."
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
