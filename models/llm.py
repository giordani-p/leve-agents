"""
Configuração de LLMs para o projeto Leve Agents.
Suporta OpenAI e Groq com monitoramento automático via AgentOps.
"""
import os
from enum import Enum
from langchain_openai import ChatOpenAI
from .llm_config import get_llm_config, validate_llm_config

# Inicialização do AgentOps para monitoramento de custos
import agentops
if os.getenv("AGENTOPS_API_KEY"):
    agentops.init()

class GroqModel(str, Enum):
    """Modelos disponíveis via Groq API."""
    LLAMA3_8B = "groq/llama-3.1-8b-instant"
    LLAMA3_70B = "groq/llama-3.3-70b-versatile"
    GEMMA = "groq/gemma2-9b-it"
    GROQ_COMPOUND = "groq/compound"
    GROQ_COMPOUND_MINI = "groq/compound-mini"
    LLAMA2_70B = "llama-3.3-70b-versatile"  # Compatibilidade

def get_groq_llm(model_name: GroqModel = None) -> ChatOpenAI:
    """Retorna um LLM configurado para usar a Groq API."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente")

    config = get_llm_config()
    validate_llm_config(config)
    
    model_to_use = model_name if model_name else config.groq_default_model

    return ChatOpenAI(
        model=model_to_use,
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        max_retries=config.max_retries,
        top_p=config.top_p,
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty
    )

def get_openai_llm(model: str = None) -> ChatOpenAI:
    """Retorna um LLM configurado para usar a OpenAI API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")

    config = get_llm_config()
    validate_llm_config(config)
    
    model_to_use = model if model else config.openai_default_model

    return ChatOpenAI(
        api_key=api_key,
        model=model_to_use,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        max_retries=config.max_retries,
        top_p=config.top_p,
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty
    )
