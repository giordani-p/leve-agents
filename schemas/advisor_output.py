# schemas/output_contract.py
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List
from typing_extensions import Annotated

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, StringConstraints, conint

# Aliases de string com restrições
ShortStr = Annotated[str, StringConstraints(min_length=3, max_length=140, strip_whitespace=True)]
SentenceStr = Annotated[str, StringConstraints(min_length=5, max_length=400, strip_whitespace=True)]
NextStepStr = Annotated[str, StringConstraints(min_length=5, max_length=140, strip_whitespace=True)]

# Inteiro ranqueado 1..3 (usando Annotated para evitar alerta do Pylance)
RankInt = Annotated[int, conint(ge=1, le=3)]

class Modality(str, Enum):
    presencial = "presencial"
    ead = "ead"
    hibrido = "hibrido"

class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: ShortStr
    url: HttpUrl
    accessed_at: date  # YYYY-MM-DD

class Option(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: RankInt  # 1..3 (unicidade será verificada nas validações de negócio)
    course_name: ShortStr
    institution: ShortStr
    modality: Modality
    duration: ShortStr  # ex.: "4 anos", "8 semestres"
    prerequisites: SentenceStr  # ou "não informado"
    cost_info: SentenceStr      # faixa/política ou "não informado"
    scholarships_info: SentenceStr  # detalhe ou "não informado"
    official_url: HttpUrl
    why_top_pick: Annotated[str, StringConstraints(min_length=5, max_length=180, strip_whitespace=True)]

class OutputAdvisor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: SentenceStr  # 2–3 linhas
    options: List[Option] = Field(min_length=1, max_length=3)
    next_steps: List[NextStepStr] = Field(min_length=2, max_length=5)
    sources: List[Source] = Field(min_length=1, max_length=6)
