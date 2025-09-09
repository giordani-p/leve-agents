from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class CareerInput(BaseModel):
    """
    Entrada mínima do Agent 02 – Especialista de Carreira (career_agent).
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(..., min_length=3, description="Pergunta do jovem (ex.: 'Como montar um currículo sem experiência?').")
    profile_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Snapshot opcional vindo do Agent 01 (escolaridade, experiências, interesses)."
    )
