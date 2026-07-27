"""Pydantic mirror of contracts/schemas/*.json. Kept hand-in-hand with those
JSON Schemas deliberately -- if they drift, the contract and the
implementation have silently diverged."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    field: str
    op: Literal["eq", "in", "gte", "lte"]
    value: object


class Pagination(BaseModel):
    cursor: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class Options(BaseModel):
    profile: Literal["hybrid", "semantic", "lexical"] = "hybrid"
    minScore: Optional[float] = Field(default=None, ge=0, le=1)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    filters: list[FilterCondition] = Field(default_factory=list)
    pagination: Pagination = Field(default_factory=Pagination)
    options: Options = Field(default_factory=Options)


class Provenance(BaseModel):
    sourceUri: str
    chunkIndex: int


class ResultDiagnostics(BaseModel):
    lexicalRank: Optional[int] = None
    semanticRank: Optional[int] = None
    lexicalScore: Optional[float] = None
    semanticScore: Optional[float] = None


class SearchResult(BaseModel):
    documentId: str
    chunkId: str
    text: str
    score: float
    provenance: Provenance
    diagnostics: Optional[ResultDiagnostics] = None


class ResponsePagination(BaseModel):
    nextCursor: Optional[str] = None


class ResponseDiagnostics(BaseModel):
    filterApplied: bool
    filterExcludedAll: bool
    candidatesLexical: int
    candidatesSemantic: int


class SearchResponse(BaseModel):
    results: list[SearchResult]
    pagination: ResponsePagination
    diagnostics: ResponseDiagnostics
