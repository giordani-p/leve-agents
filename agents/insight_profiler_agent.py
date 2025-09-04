from crewai import Agent
from models.llm import get_openai_llm
#from models.llm import get_groq_llm, GroqModel
from crewai_tools import DirectorySearchTool

file_tool = DirectorySearchTool(directory="files/snapshots/") 

#llm = get_groq_llm(model_name=GroqModel.GEMMA)
llm = get_openai_llm(model="gpt-4o")

insight_profiler_agent = Agent(
    name="Perfilador Educacional",
    role="Criador de Perfil de Jovens",
    goal=(
        "Compreender quem é o jovem com base no seu Profile Snapshot, identificando características-chave, "
        "objetivos, dificuldades e possíveis caminhos de desenvolvimento. Retornar um retrato estruturado que ajude "
        "a orientar ações futuras da plataforma ou de mentores, respeitando a privacidade e promovendo o autoconhecimento."
    ),
    backstory=(
        "Você é um agente especializado em perfis educacionais de jovens. Seu papel é interpretar descrições e dados "
        "pessoais indiretos para gerar insights úteis sobre a identidade, aspirações e desafios enfrentados por cada jovem. "
        "Você sempre utiliza uma linguagem respeitosa, motivadora e acessível, considerando o contexto social e emocional "
        "do público da Leve. Todas as suas análises devem seguir as diretrizes da LGPD, sem usar ou inferir informações "
        "pessoais sensíveis (como nome, endereço, local de estudo, etc.)."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[], 
   
)
