# tasks/insight_profiler_task.py
from crewai import Task
from agents.insight_profiler_agent import insight_profiler_agent

insight_profiler_task = Task(
    name="Interpretação de dados de perfil do jovem",
    description=(
        "Você receberá um conjunto de dados estruturados sobre um jovem, incluindo escolaridade, experiências, sonhos, habilidades..."
        "Os dados do jovem foram fornecidos diretamente em texto. Analise o conteúdo da variável dados e gere o retrato interpretativo conforme as instruções abaixo. "
    ),

    expected_output=(
        "Retorne APENAS um JSON com os seguintes campos:\n\n"
        "- macroperfil: string. Um resumo geral do jovem (estilo, momento de vida, postura).\n"
        "- caracteristicas_chave: lista de strings. Até 5 traços marcantes percebidos (ex: ['Curioso', 'Responsável']).\n"
        "- objetivos_detectados: lista de strings com metas, sonhos ou aspirações percebidas.\n"
        "- dificuldades_detectadas: lista de strings com obstáculos ou barreiras inferidas.\n"
        "- hipoteses_a_validar: lista de hipóteses úteis que podem explicar o momento do jovem (ex: ['Sente-se inseguro com decisões futuras']).\n"
        "- recomendacoes: lista de sugestões práticas ou de reflexão com tom motivador.\n"
        "- next_questions: lista com até 3 perguntas abertas que podem aprofundar o entendimento sobre o jovem (ex: ['O que te inspira hoje?']).\n"
        "- alerts_politicas: lista com 0 ou mais sinais críticos (ex: ['abandono escolar']). Se nenhum for identificado, inclua exatamente 'não informado'.\n\n"

        "Regras obrigatórias:\n"
        "1. Todos os campos devem estar presentes, mesmo que com o valor 'não informado'.\n"
        "2. Todos os campos (exceto macroperfil) devem ser listas de strings. Nunca retorne como texto corrido ou uma única string com vírgulas.\n"
        "3. Use apenas texto simples. Nada de markdown, bullets ou formatação.\n"
        "4. A linguagem deve ser acessível, respeitosa e jovem.\n"
        "5. Não inclua dados sensíveis como nome, cidade ou escola.\n"
    ),
    agent=insight_profiler_agent,
    async_execution=False,
)
