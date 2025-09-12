from pydantic import BaseModel, Field, model_validator
from typing import Optional

class AdvisorInput(BaseModel):
    snapshot_file: Optional[str] = Field(
        default=None,
        description="Caminho para o arquivo de snapshot do jovem"
    )
    interesse: Optional[str] = Field(
        default=None,
        min_length=3, 
        description="Área ou assunto que o usuário quer aprender (opcional se snapshot fornecido)"
    )
    preferencia: Optional[str] = Field(
        default=None,
        min_length=2, 
        description="Formato ou região preferida para o curso (opcional se snapshot fornecido)"
    )
    foco_especifico: Optional[str] = Field(
        default=None,
        description="Foco específico da orientação (ex: 'primeiro emprego', 'mudança de carreira', 'sobrevivência básica')"
    )
    prioridade_urgencia: Optional[str] = Field(
        default="moderada",
        description="Nível de urgência: 'baixa', 'moderada', 'alta', 'critica'"
    )
    
    @model_validator(mode='after')
    def validate_input(self) -> 'AdvisorInput':
        """Valida que pelo menos snapshot_file ou interesse seja fornecido"""
        if not self.snapshot_file and not self.interesse:
            raise ValueError("Pelo menos 'snapshot_file' ou 'interesse' deve ser fornecido")
        return self
