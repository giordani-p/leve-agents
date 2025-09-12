"""
Schema de saída do Orientador Educacional - Leve Agents

Define a estrutura de dados para respostas do agente orientador,
incluindo recomendações de cursos, caminhos de carreira e próximos passos.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional
from typing_extensions import Annotated

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, StringConstraints, conint

# Aliases de string com restrições
ShortStr = Annotated[str, StringConstraints(min_length=3, max_length=140, strip_whitespace=True)]
SentenceStr = Annotated[str, StringConstraints(min_length=5, max_length=400, strip_whitespace=True)]
NextStepStr = Annotated[str, StringConstraints(min_length=5, max_length=140, strip_whitespace=True)]

# Inteiro ranqueado 1..5
RankInt = Annotated[int, conint(ge=1, le=5)]

class Modality(str, Enum):
    presencial = "presencial"
    ead = "ead"
    hibrido = "hibrido"
    online = "online"
    semipresencial = "semipresencial"

class RecommendationType(str, Enum):
    curso_graduacao = "curso_graduacao"
    curso_tecnico = "curso_tecnico"
    curso_livre = "curso_livre"
    certificacao = "certificacao"
    empreendedorismo = "empreendedorismo"
    trabalho_manual = "trabalho_manual"
    carreira_artistica = "carreira_artistica"
    apoio_psicologico = "apoio_psicologico"
    orientacao_basica = "orientacao_basica"
    curso_preparatorio = "curso_preparatorio"
    especializacao = "especializacao"
    estagio = "estagio"

class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: ShortStr
    url: HttpUrl
    accessed_at: date  # YYYY-MM-DD

class Option(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: RankInt  # 1..5 (unicidade será verificada nas validações de negócio)
    type: RecommendationType  # Tipo de recomendação
    title: ShortStr  # Nome do curso/oportunidade
    institution: Optional[ShortStr]  # Instituição (opcional para alguns tipos)
    modality: Optional[Modality]  # Modalidade (opcional para alguns tipos)
    duration: Optional[ShortStr]  # Duração (opcional para alguns tipos)
    prerequisites: Annotated[str, StringConstraints(min_length=3, max_length=400, strip_whitespace=True)]  # Pré-requisitos ou "não informado"
    cost_info: SentenceStr  # Faixa de custo ou "não informado"
    scholarships_info: SentenceStr  # Informações sobre bolsas ou "não informado"
    official_url: Optional[HttpUrl]  # URL oficial (opcional)
    why_recommended: Annotated[str, StringConstraints(min_length=5, max_length=300, strip_whitespace=True)]  # Por que é recomendado
    next_steps: List[NextStepStr] = Field(min_length=1, max_length=3)  # Próximos passos específicos
    compatibility_score: Annotated[int, conint(ge=1, le=10)] = Field(description="Score de compatibilidade com o perfil (1-10)")

class ProfileAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    perfil_principal: ShortStr = Field(description="Perfil principal identificado")
    pontos_fortes: List[ShortStr] = Field(min_length=1, max_length=3, description="Principais pontos fortes")
    areas_desenvolvimento: List[ShortStr] = Field(min_length=1, max_length=3, description="Áreas que precisam de desenvolvimento")
    barreiras_principais: List[ShortStr] = Field(min_length=1, max_length=3, description="Principais barreiras identificadas")
    nivel_prioridade: Annotated[int, conint(ge=1, le=5)] = Field(description="Nível de prioridade para orientação (1-5)")

class OutputAdvisor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: SentenceStr  # 2–3 linhas
    profile_analysis: ProfileAnalysis  # Análise do perfil
    options: List[Option] = Field(min_length=1, max_length=5)  # Expandido para 5 opções
    general_next_steps: List[NextStepStr] = Field(min_length=2, max_length=5)  # Próximos passos gerais
    sources: List[Source] = Field(min_length=1, max_length=8)  # Expandido para mais fontes
    personalized_advice: Annotated[str, StringConstraints(min_length=5, max_length=500, strip_whitespace=True)] = Field(description="Conselho personalizado baseado no perfil")
    risk_factors: List[ShortStr] = Field(min_length=0, max_length=3, description="Fatores de risco identificados")
    opportunities: List[ShortStr] = Field(min_length=1, max_length=3, description="Oportunidades identificadas")
