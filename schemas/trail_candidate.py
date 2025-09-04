# schemas/trail_candidate.py
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

Difficulty = Literal["Beginner", "Intermediate", "Advanced"]
Status = Literal["Published", "Draft", "Archived"]


class TrailCandidate(BaseModel):
    """
    Representa um item do catálogo de trilhas já normalizado para uso no
    Sistema de Recomendação (CLI).

    Observações:
    - publicId é obrigatório e serve como identificador essencial.
    - slug é opcional (para exibição/URLs quando fizer sentido).
    - status é mantido apenas para auditoria/checagens; o filtro por 'Published'
      deve ser aplicado na etapa de seleção antes da recomendação.
    """
    publicId: UUID = Field(..., description="Identificador público obrigatório (UUID).")
    slug: Optional[str] = Field(default=None, description="Slug da trilha (opcional).")
    title: str
    tags: List[str] = Field(default_factory=list)
    difficulty: Optional[Difficulty] = Field(default=None)
    description: str = Field(default="")
    status: Optional[Status] = Field(default=None, description="Status original no catálogo (auditoria).")
    combined_text: str = Field(
        default="",
        description="Concatenação de campos textuais (título, subtítulo, tags, descrição) para similaridade.",
    )

    @classmethod
    def from_source(cls, item: dict) -> "TrailCandidate":
        """
        Normaliza um item bruto do JSON de origem para o contrato TrailCandidate.
        """
        # Identificador essencial (UUID)
        public_id_raw = item.get("publicId") or item.get("id")
        if not public_id_raw:
            raise ValueError("publicId é obrigatório para construir TrailCandidate.")
        public_id = UUID(str(public_id_raw))

        # Campos básicos
        slug = item.get("slug") or None
        title = item.get("title") or ""
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []

        # Difficulty normalizada
        raw_diff = item.get("difficulty")
        difficulty: Optional[Difficulty] = None
        if isinstance(raw_diff, str):
            norm = raw_diff.strip().lower()
            if norm in {"beginner", "iniciante"}:
                difficulty = "Beginner"
            elif norm in {"intermediate", "intermediário", "intermediario"}:
                difficulty = "Intermediate"
            elif norm in {"advanced", "avançado", "avancado"}:
                difficulty = "Advanced"

        # Descrição e status (para auditoria)
        description = item.get("description") or item.get("summary") or ""
        raw_status = item.get("status")
        status: Optional[Status] = None
        if isinstance(raw_status, str):
            s = raw_status.strip().lower()
            if s == "published":
                status = "Published"
            elif s == "draft":
                status = "Draft"
            elif s == "archived":
                status = "Archived"

        # Texto combinado (inclui subtítulo, se houver)
        subtitle = item.get("subtitle") or ""
        combined_parts = [title, subtitle] + tags + [description]
        combined_text = " | ".join([str(p) for p in combined_parts if p])

        return cls(
            publicId=public_id,
            slug=slug,
            title=title,
            tags=tags,
            difficulty=difficulty,
            description=description,
            status=status,
            combined_text=combined_text,
        )
