"""
Schema de saída do Perfilador Psicológico - Leve Agents

Define a estrutura de dados para análise psicológica e comportamental,
incluindo motivações, estilos de aprendizado e preferências de trabalho.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal

class PsychologicalOutput(BaseModel):
    """Contrato de saída do Perfilador Psicológico."""
    
    perfil_psicologico: str = Field(..., description="Resumo integrado do perfil psicológico e comportamental")
    
    motivacoes_principais: List[str] = Field(..., description="Principais motivações intrínsecas (máx 3)")
    valores_core: List[str] = Field(..., description="Valores fundamentais (máx 3)")
    
    estilo_aprendizado: str = Field(..., description="Estilo de aprendizado dominante")
    estilo_comunicacao: str = Field(..., description="Estilo de comunicação preferido")
    estilo_lideranca: str = Field(..., description="Estilo de liderança natural")
    
    ambiente_ideal: dict = Field(..., description="Ambiente de trabalho ideal")
    modalidade_trabalho: str = Field(..., description="Modalidade de trabalho preferida")
    tipo_atividade: str = Field(..., description="Tipo de atividade preferida")
    
    tolerancia_risco: str = Field(..., description="Tolerância ao risco")
    gatilhos_estresse: List[str] = Field(..., description="Principais gatilhos de estresse (máx 3)")
    areas_desenvolvimento: List[str] = Field(..., description="Áreas prioritárias para desenvolvimento (máx 3)")
    
    pontos_fortes: List[str] = Field(..., description="Principais pontos fortes psicológicos (máx 3)")
    desafios_comportamentais: List[str] = Field(..., description="Desafios comportamentais principais (máx 3)")
    
    # Compatibilidade e recomendações
    perfis_carreira_compativel: List[str] = Field(..., description="Perfis de carreira mais compatíveis (máx 3)")
    estrategias_personalizacao: List[str] = Field(..., description="Estratégias de personalização (máx 3)")
    alertas_importantes: List[str] = Field(..., description="Alertas comportamentais importantes (máx 3)")
    
    # Análise integrada de talentos
    interpretacao_talentos: str = Field(..., description="Interpretação psicológica dos talentos CliftonStrengths")
    integracao_metodologias: str = Field(..., description="Como DISC e CliftonStrengths se complementam")

    class Config:
        extra = "forbid"
