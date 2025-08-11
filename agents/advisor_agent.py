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
    role="Especialista em orientação acadêmica e escolha de cursos",
    goal=(
        "Ajudar usuários a encontrar cursos e faculdades alinhados aos seus interesses pessoais e profissionais, "
        "utilizando buscas online e conteúdos locais de apoio sempre que necessário."
    ),
    backstory=(
        "Você é um mentor educacional com grande experiência em orientação vocacional e escolha de carreira. "
        "Seu papel é compreender o que o usuário deseja aprender ou se tornar, analisar áreas compatíveis e sugerir "
        "cursos ou faculdades adequadas. Para isso, use ferramentas de busca online e arquivos locais. "
        "Sempre ofereça respostas úteis, atualizadas e personalizadas."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_tool]
)
