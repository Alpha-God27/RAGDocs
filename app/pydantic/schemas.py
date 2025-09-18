from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class ApiKeyValidationRequest(BaseModel):
    """Request model for API key validation"""
    api_key: str = Field(..., min_length=1, description="OpenRouter API key")


class ApiKeyValidationResponse(BaseModel):
    """Response model for API key validation"""
    valid: bool = Field(..., description="Whether the API key is valid")
    message: str = Field(default="", description="Validation message")


class DocumentIndexRequest(BaseModel):
    """Request model for indexing a document from URL"""
    label: str = Field(..., min_length=1, max_length=100, description="Human-readable label for the document")
    url: HttpUrl = Field(..., description="URL of the document to index")
    enable_crawling: bool = Field(default=True, description="Whether to crawl related pages automatically")
    max_pages: int = Field(default=10, ge=1, le=25, description="Maximum number of pages to crawl")


class DocumentIndexResponse(BaseModel):
    """Response model for document indexing"""
    success: bool = Field(..., description="Whether indexing was successful")
    message: str = Field(..., description="Status message")
    document_id: str = Field(..., description="Unique identifier for the indexed document")
    chunks_count: int = Field(..., description="Number of text chunks created")
    pages_crawled: int = Field(default=1, description="Number of pages crawled and indexed")
    urls_indexed: List[str] = Field(default_factory=list, description="List of URLs that were indexed")


class DocumentListResponse(BaseModel):
    """Response model for listing indexed documents"""
    documents: List[dict] = Field(..., description="List of indexed documents with metadata")


class QueryRequest(BaseModel):
    """Request model for querying the RAG system"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    document_id: Optional[str] = Field(None, description="Specific document to search (if None, searches all)")
    model: Optional[str] = Field(None, description="LLM model to use for generation")
    max_docs: Optional[int] = Field(4, ge=1, le=10, description="Maximum number of documents to retrieve")


class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    answer: str = Field(..., description="Generated answer")
    sources: List[dict] = Field(..., description="Source documents used for the answer")
    model_used: str = Field(..., description="LLM model used for generation")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")

