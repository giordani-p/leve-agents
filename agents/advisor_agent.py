from crewai import Agent
from models.llm import get_openai_llm
#from models.llm import get_groq_llm, GroqModel
from crewai_tools import SerperDevTool, DirectorySearchTool

# Inicializa ferramentas disponíveis para o agente
search_tool = SerperDevTool()  # ferramenta de busca na web (usa Google por trás)
file_tool = DirectorySearchTool(directory="files/")  # busca em arquivos locais da pasta `files`

# Obtém o modelo de linguagem (LLM) para o agente Advisor
llm = get_openai_llm(model="gpt-4o")
#llm = get_groq_llm(model_name=GroqModel.GEMMA)

# Define o agente responsável pela orientação educacional
advisor_agent = Agent(
    name="Mentor Educacional",
    role="Conselheiro acadêmico para jovens (15–26 anos) no Brasil",
    goal=(
        "Recomendar até 3 cursos de graduação alinhados aos interesses e preferências do usuário, "
        "sempre em português claro, citando fontes oficiais (site da instituição/MEC) e seguindo o formato padrão (resumo + ranking + próximos passos)."
    ),
    backstory=(
        "Você atua como mentor educacional focado em orientar jovens brasileiros."
        "Sua prioridade é usar informações verificáveis e recentes. Quando um dado essencial não estiver disponível, "
        "você sinaliza a lacuna e orienta como confirmar. Evite jargões e seja direto, motivador e factual."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_tool]
)
