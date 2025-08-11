from crewai import Task
from agents.advisor_agent import advisor_agent

# Define a tarefa que será executada pelo agente Advisor
advisor_task = Task(
    # Descrição geral da tarefa 
    description=(
        "Um jovem deseja encontrar um curso ou faculdade alinhado aos seus interesses e preferências. "
        "Ele demonstrou interesse em **{interesse}** e prefere cursos ou faculdades com o formato ou localização: **{preferencia}**. "
        "Utilize ferramentas de busca e arquivos locais sempre que necessário para entregar uma resposta útil e personalizada."
    ),
    
    # Formato esperado da resposta final gerada pelo agente
    expected_output=(
        "Uma orientação completa com pelo mneos 3 opções estruturada que inclua:\n"
        "1. **Descrição do curso ou faculdade**: breve descrição\n"
        "2. **Instituição**: nome da instituição\n"
        "3. **Localização**: cidade e estado\n"
        "4. **Formato**: presencial, EAD, etc\n" 
        "5. **Preço**: valor médio do curso ou faculdade\n"
        "6. **Motivação**: mensagem final de encorajamento\n\n"
        "A resposta deve ser acessível, prática e inspirar confiança no jovem."
    ),
    output_file="output.txt",
    # Agente responsável por executar a tarefa
    agent=advisor_agent,

    # Execução síncrona (aguarda resposta antes de continuar)
    async_execution=False,
)
