import os
from enum import Enum
from langchain_openai import ChatOpenAI

# Enum para listar os modelos disponíveis via Groq
class GroqModel(str, Enum):
   # MISTRAL_SABA = "groq/mistral-saba-24b" 
    LLAMA3_8B = "groq/llama3-8b-8192"
    LLAMA3_70B = "groq/llama3-70b-8192"
    GEMMA = "groq/gemma2-9b-it"
    LLAMA2_70B = "groq/llama-3.3-70b-versatile"

# Função que retorna um LLM configurado para usar a Groq
def get_groq_llm(model_name: GroqModel = GroqModel.GEMMA) -> ChatOpenAI:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente (.env)")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.7,
        max_tokens=2500
    )

# Função que retorna um LLM configurado para usar a OpenAI
def get_openai_llm(model: str = "gpt-4o") -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente (.env)")

    return ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=0.7,
        max_tokens=2000
    )
