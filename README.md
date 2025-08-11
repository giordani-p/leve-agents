# Orientador Educacional - Agent

Um agente inteligente que ajuda usuários a encontrar cursos e faculdades alinhados aos seus interesses.

## Configuração Rápida
```bash
uv venv activate  
source activate/bin/activate
```

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com:

```env
# Obrigatório: Chave da API Groq (gratuita)
GROQ_API_KEY=sua_chave_groq_aqui

# Opcional: Outras APIs
OPENAI_API_KEY=sua_chave_openai_aqui
SERPER_API_KEY=sua_chave_serper_aqui
AGENTOPS_API_KEY=sua_chave_agentops_aqui
```

### 3. Obter chaves de API

#### Groq (Obrigatório)
1. Acesse https://console.groq.com/
2. Crie uma conta gratuita
3. Copie sua API key
4. Cole no arquivo `.env`

#### SerperDev (Opcional - para buscas)
1. Acesse https://serper.dev/
2. Crie uma conta
3. Copie sua API key

### 4. Executar o projeto
```bash
python main.py
```

## Estrutura do Projeto

```
estag-agent/
├── agents/           # Definição dos agentes
├── models/           # Configuração dos LLMs
├── tasks/            # Definição das tarefas
├── schemas/          # Esquemas de dados
├── files/            # Arquivos de referência
├── main.py           # Arquivo principal
└── crew_config.py    # Configuração da crew
```

## Como Usar

1. Execute `python main.py`
2. Digite o que você gostaria de aprender
3. Especifique suas preferências (online, presencial, região)
4. O agente irá buscar e recomendar cursos adequados

## Modelos Suportados

### Groq (Recomendado)
- `mixtral-8x7b-32768` (padrão)
- `llama3-8b-8192`
- `llama3-70b-8192`
- `gemma-7b-it`
- `llama2-70b-4096`

### OpenAI
- `gpt-4o`
- `gpt-3.5-turbo` 

