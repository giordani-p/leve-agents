# Leve Agents - Sistema de Orientação Educacional e Profissional

Sistema inteligente de agentes especializados em orientação educacional e profissional para jovens brasileiros (15-26 anos). Utiliza CrewAI para coordenação de múltiplos agentes especializados com monitoramento de custos via AgentOps.

## 🚀 Características Principais

- **3 Agentes Especializados**: Orientador Educacional, Especialista de Carreira e Perfilador Psicológico
- **Sistema de Recomendação**: Busca híbrida (BM25 + semântica) para trilhas educacionais personalizadas
- **Monitoramento de Custos**: Integração com AgentOps para acompanhamento de gastos de LLM
- **Validação Completa**: Schemas Pydantic com validação de negócio
- **Múltiplos LLMs**: Suporte a OpenAI e Groq
- **CLI Intuitivo**: Interface de linha de comando para cada agente

## 🏗️ Arquitetura

### Agentes Especializados

1. **Orientador Educacional** (`advisor_agent`)
   - Planejamento estratégico de carreira de longo prazo
   - Análise de perfil completo e identificação de direções
   - Roadmap de desenvolvimento com marcos e prazos

2. **Especialista de Carreira** (`career_coach_agent`)
   - Execução prática para conseguir primeiro emprego
   - Conselhos concretos sobre currículo, entrevistas e networking
   - Foco em ações imediatas e acionáveis

3. **Perfilador Psicológico** (`psychological_profiler_agent`)
   - Análise psicológica e comportamental profunda
   - Identificação de motivações, valores e estilos de aprendizado
   - Insights para personalização de recomendações

### Sistema de Recomendação

4. **Sistema de Recomendação** (`reco/`)
   - **Busca Híbrida**: Combina BM25 (textual) e MPNet (semântica) para máxima precisão
   - **Personalização**: Recomendações baseadas no perfil completo do usuário
   - **Múltiplas Fontes**: Suporte a API da Leve e arquivos locais
   - **Ranking Inteligente**: Sistema de boosts e filtros de negócio
   - **Observabilidade**: Logs detalhados para análise e otimização

## ⚙️ Configuração Rápida

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# APIs de LLM (pelo menos uma obrigatória)
GROQ_API_KEY=sua_chave_groq_aqui
OPENAI_API_KEY=sua_chave_openai_aqui

# Monitoramento de custos (opcional)
AGENTOPS_API_KEY=sua_chave_agentops_aqui
```

### 3. Obter chaves de API

#### Groq (Recomendado - Gratuito)
1. Acesse [https://console.groq.com/](https://console.groq.com/)
2. Crie uma conta gratuita
3. Gere sua API key

#### OpenAI (Opcional)
1. Acesse [https://platform.openai.com/](https://platform.openai.com/)
2. Crie uma conta
3. Gere sua API key

#### AgentOps (Opcional - Monitoramento)
1. Acesse [https://agentops.ai](https://agentops.ai)
2. Crie uma conta gratuita
3. Gere sua API key

## 🎯 Como Usar

### Orientador Educacional
```bash
python -m cli.main_advisor -i "programação" -p "online"
python -m cli.main_advisor --snapshot files/snapshots/pablo_001.json --json
```

### Especialista de Carreira
```bash
python -m cli.main_career -q "Como montar um currículo sem experiência?"
python -m cli.main_career -q "Quais áreas posso trabalhar?" --snapshot-path files/snapshots/ana_001.json
```

### Perfilador Psicológico
```bash
python -m cli.main_psychological -d "Escolaridade: Ensino médio completo..."
python -m cli.main_psychological --data-file files/snapshots/carlos_001.json --json
```

### Sistema de Recomendação
```bash
# Busca básica
python -m cli.main_reco -q "Quero aprender programação do zero"

# Com perfil personalizado
python -m cli.main_reco -q "Quais áreas combinam com meu perfil?" --snapshot-path files/snapshots/ana_001.json

# Usando API da Leve
python -m cli.main_reco -q "Como organizar meus estudos?" --source api --api-base http://localhost:3000

# Output em JSON
python -m cli.main_reco -q "trilhas para iniciantes" --json
```

## 📁 Estrutura do Projeto

```
leve-agents/
├── agents/                    # Agentes especializados
│   ├── advisor_agent.py      # Orientador Educacional
│   ├── career_coach_agent.py # Especialista de Carreira
│   └── psychological_profiler_agent.py # Perfilador Psicológico
├── cli/                      # Interfaces de linha de comando
│   ├── main_advisor.py       # CLI do Orientador
│   ├── main_career.py        # CLI do Especialista de Carreira
│   ├── main_psychological.py # CLI do Perfilador
│   └── main_reco.py          # CLI do Sistema de Recomendação
├── reco/                     # Sistema de Recomendação
│   ├── config.py            # Configuração do sistema
│   ├── pipeline.py          # Pipeline principal
│   ├── data_loader.py       # Carregamento de dados
│   ├── data_loader_api.py   # Integração com API
│   ├── embeddings/          # Provedores de embeddings
│   ├── index/               # Índices vetoriais
│   ├── retriever/           # Retrievers (dense/hybrid)
│   ├── ranker.py            # Sistema de ranking
│   ├── explainer.py         # Geração de explicações
│   └── output_builder.py    # Construção de output
├── models/                   # Configuração de LLMs
│   ├── llm.py               # Funções de LLM com AgentOps
│   └── llm_config.py        # Configurações dos modelos
├── schemas/                  # Schemas de dados
│   ├── advisor_output.py    # Schema do Orientador
│   ├── career_output.py     # Schema do Especialista
│   ├── psychological_output.py # Schema do Perfilador
│   ├── trail_input.py       # Schema de entrada de trilhas
│   ├── trail_output.py      # Schema de saída de trilhas
│   └── trail_candidate.py   # Schema de candidatos
├── tasks/                    # Definição das tarefas
│   ├── advisor_task.py      # Task do Orientador
│   ├── career_coach_task.py # Task do Especialista
│   └── psychological_profiler_task.py # Task do Perfilador
├── validators/               # Validação de negócio
├── helpers/                  # Utilitários
├── files/                    # Arquivos de referência
│   ├── snapshots/           # Perfis de exemplo
│   └── trails/              # Catálogo de trilhas
├── docs/                     # Documentação
│   └── agentops_monitoramento.md # Guia do AgentOps
├── crew_config.py           # Configuração das crews
└── requirements.txt         # Dependências
```

## 🤖 Modelos Suportados

### Groq (Recomendado)
- `groq/llama-3.1-8b-instant` (Padrão)
- `groq/llama-3.3-70b-versatile`
- `groq/gemma2-9b-it`
- `groq/compound`
- `groq/compound-mini`

### OpenAI
- `gpt-4o` (Padrão)
- `gpt-3.5-turbo`

## 🔍 Sistema de Recomendação

O sistema de recomendação utiliza uma arquitetura híbrida avançada para recomendar trilhas educacionais personalizadas:

### Arquitetura Híbrida
- **BM25 (Esparso)**: Busca textual tradicional para termos exatos
- **MPNet (Denso)**: Busca semântica para compreensão de contexto
- **Blending Inteligente**: Combinação otimizada dos dois métodos
- **Normalização**: Padronização de scores para comparação justa

### Funcionalidades Avançadas
- **Personalização**: Recomendações baseadas no perfil completo do usuário
- **Múltiplas Fontes**: API da Leve ou arquivos locais com fallback automático
- **Ranking Inteligente**: Sistema de boosts e filtros de negócio
- **Expansão de Consulta**: Sinônimos automáticos para melhor cobertura
- **Observabilidade**: Logs detalhados para análise e otimização

### Configuração Flexível
- **Thresholds por Tipo**: Diferentes limiares para trilhas vs vagas
- **Modos de Busca**: Híbrido, apenas BM25, ou apenas semântico
- **Parâmetros Ajustáveis**: Pesos, normalização e boosts configuráveis
- **Timeouts e Retries**: Configuração robusta para APIs externas

## 📊 Monitoramento de Custos

O projeto inclui integração com **AgentOps** para monitoramento automático de custos de LLM:

- **Inicialização automática** quando `AGENTOPS_API_KEY` está configurada
- **Monitoramento transparente** de todas as chamadas para APIs
- **Dashboard web** para visualização de custos e métricas
- **Logs locais** para análise offline

Para mais detalhes, consulte [docs/agentops_monitoramento.md](docs/agentops_monitoramento.md).

## 🔧 Desenvolvimento

### Estrutura de Validação
- **Schemas Pydantic** para validação de estrutura
- **Validadores de negócio** para regras específicas
- **Extração de JSON** robusta com fallbacks

### Configuração de LLM
- **Configuração centralizada** em `models/llm_config.py`
- **Suporte a múltiplos provedores** (OpenAI, Groq)
- **Configurações otimizadas** para cada modelo

### Sistema de Recomendação
- **Arquitetura híbrida** com BM25 e MPNet
- **Configuração flexível** em `reco/config.py`
- **Pipeline modular** para fácil manutenção e extensão
- **Validação rigorosa** com schemas Pydantic
- **Observabilidade completa** com logs detalhados

### Documentação
- **Docstrings padronizadas** com funcionalidades detalhadas
- **Comentários objetivos** alinhados com a versão atual
- **Exemplos de uso** nos CLIs e documentação técnica
- **Arquitetura documentada** para cada módulo principal

## 📈 Próximos Passos

- [ ] Integração com mais provedores de LLM
- [ ] Interface web para os agentes
- [ ] Sistema de cache para otimização
- [ ] Métricas avançadas de performance
- [ ] Integração com bases de dados de cursos
- [ ] Índices vetoriais persistentes (FAISS/ChromaDB)
- [ ] A/B testing para algoritmos de recomendação
- [ ] Sistema de feedback para melhorar recomendações
- [ ] Integração com mais fontes de dados educacionais

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 

