from typing import Literal, Optional, List
from pydantic import BaseModel, Field, HttpUrl
from pydantic.config import ConfigDict


class ResourceItem(BaseModel):
    """
    Recurso opcional sugerido pelo agente para complementar a resposta.
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=160)
    type: Literal["template", "article", "video", "checklist"]
    url: Optional[HttpUrl] = None


class CareerOutput(BaseModel):
    """
    Contrato de saída do Agent 02 – Especialista de Carreira (career_agent).
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["ok", "fora_do_escopo"]
    short_answer: str = Field(..., min_length=1, max_length=240)
    detailed_answer: str = Field(..., min_length=1)
    resources: Optional[List[ResourceItem]] = None
