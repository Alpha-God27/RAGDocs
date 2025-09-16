from pydantic import BaseModel, Field
from typing import List, Optional


class ValidateKeyResponse(BaseModel):
    ok: bool = True


class IndexUrlRequest(BaseModel):
    label: str = Field(..., min_length=2, max_length=80)
    url: str = Field(..., min_length=8)


class IndexUrlResponse(BaseModel):
    label: str
    persist_dir: str


class DocsListResponse(BaseModel):
    labels: List[str]


class AskRequest(BaseModel):
    label: str
    question: str
    model: Optional[str] = Field(default="openrouter/auto")


class AskResponse(BaseModel):
    answer: str

