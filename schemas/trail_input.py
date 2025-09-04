# schemas/trail_input.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TrailInput(BaseModel):
    """
    Entrada do Sistema de Recomendação (CLI).

    Campos:
      - user_question: pergunta/dúvida do jovem (obrigatório).
      - user_id: identificador do usuário (UUID) para cruzar com perfil/progresso (opcional).
      - contexto_extra: detalhes adicionais relevantes (ex.: área de interesse, nível, objetivo) (opcional).
      - max_results: quantidade máxima de sugestões a retornar (padrão 3).

    Observações:
      - A fonte de dados vem de arquivos JSON sob 'files/'.
      - O sistema aplica filtro rígido por trilhas com status 'Published'.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    user_question: str = Field(
        ...,
        min_length=8,
        max_length=500,
        description="Pergunta/dúvida do jovem em linguagem natural.",
        examples=["Quero aprender lógica de programação do zero, por onde começo?"],
    )
    user_id: Optional[UUID] = Field(
        default=None,
        description="UUID do usuário, se disponível, para personalização baseada no perfil/progresso.",
        examples=["3f1a9c3e-8b4c-4cb7-9c31-2cf3f0a2a8d3"],
    )
    contexto_extra: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=500,
        description="Contexto adicional livre (ex.: área de interesse, objetivo, nível atual).",
        examples=["Interesse em front-end e JavaScript; nível iniciante; 30 min/dia."],
    )
    max_results: int = Field(
        default=3,
        ge=1,
        le=3,
        description="Número máximo de trilhas sugeridas a retornar (1 a 3)."
    )
