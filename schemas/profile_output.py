# schemas/profile_output.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal

class ProfileOutput(BaseModel):
    macroperfil: str = Field(..., description="Resumo geral do jovem, incluindo estilo, momento de vida ou postura. Deve ser texto simples e direto.")
    caracteristicas_chave: List[str] = Field(..., max_items=5, description="Lista de até 5 características percebidas no jovem.")
    objetivos_detectados: List[str] = Field(..., description="Metas, sonhos ou aspirações identificadas.")
    dificuldades_detectadas: List[str] = Field(..., description="Dificuldades ou barreiras percebidas no snapshot.")
    hipoteses_a_validar: List[str] = Field(..., description="Possíveis hipóteses ou causas para situações relatadas que precisam ser confirmadas futuramente.")
    recomendacoes: List[str] = Field(..., description="Sugestões práticas ou reflexivas para apoiar o jovem.")
    next_questions: List[str] = Field(..., max_items=3, description="Até 3 perguntas úteis para aprofundar a compreensão do jovem. Uso interno, não exibir diretamente.")
    alerts_politicas: List[Literal[
        "abandono escolar",
        "saúde mental",
        "violência",
        "insegurança alimentar",
        "uso de substâncias",
        "não informado"
    ]] = Field(..., description="Lista de possíveis alertas de atenção com base no conteúdo. Se nenhum for identificado, incluir 'não informado'.")

    class Config:
        extra = "forbid"
