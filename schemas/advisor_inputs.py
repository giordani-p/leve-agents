from pydantic import BaseModel, Field

class UserInput(BaseModel):
    interesse: str = Field(
        min_length=3, 
        description="Área ou assunto que o usuário quer aprender"
    )
    preferencia: str = Field(
        min_length=2, 
        description="Formato ou região preferida para o curso"
    )
