"""
Configuração centralizada para LLMs - Leve Agents

Gerencia configurações de modelos de linguagem (OpenAI e Groq) com validação
e suporte a variáveis de ambiente para personalização.

Funcionalidades:
- Configuração centralizada para OpenAI e Groq
- Validação de parâmetros de configuração
- Suporte a variáveis de ambiente (.env)
- Configurações otimizadas por provedor
- Tratamento de timeouts e retries
"""
import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"

@dataclass
class LLMConfig:
    """Configuração centralizada para LLMs"""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 3
    


    # Modelos padrão por provedor (usados quando não especificado)
    openai_default_model: str = "gpt-4o"
    groq_default_model: str = "groq/llama-3.3-70b-versatile"
    
    # Configurações de qualidade
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

def get_llm_config() -> LLMConfig:
    """Retorna configuração do LLM baseada em variáveis de ambiente"""
    return LLMConfig(
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
        timeout=int(os.getenv("LLM_TIMEOUT", "60")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
        openai_default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
        groq_default_model=os.getenv("GROQ_DEFAULT_MODEL", "groq/gemma2-9b-it"),
        top_p=float(os.getenv("LLM_TOP_P", "1.0")),
        frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0")),
        presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", "0.0"))
    )

def validate_llm_config(config: LLMConfig) -> None:
    """Valida configuração do LLM"""
    if not 0.0 <= config.temperature <= 2.0:
        raise ValueError(f"Temperature deve estar entre 0.0 e 2.0, recebido: {config.temperature}")
    
    if not 1 <= config.max_tokens <= 10000:
        raise ValueError(f"Max tokens deve estar entre 1 e 10000, recebido: {config.max_tokens}")
    
    if not 1 <= config.timeout <= 300:
        raise ValueError(f"Timeout deve estar entre 1 e 300 segundos, recebido: {config.timeout}")
    
    if not 0 <= config.max_retries <= 10:
        raise ValueError(f"Max retries deve estar entre 0 e 10, recebido: {config.max_retries}")

# Configuração padrão
DEFAULT_CONFIG = get_llm_config()
validate_llm_config(DEFAULT_CONFIG)
