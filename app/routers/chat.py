"""API endpoints for RAGDocs."""

import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.pydantic.schemas import (
    ApiKeyValidationRequest,
    ApiKeyValidationResponse,
    DocumentIndexRequest,
    DocumentIndexResponse,
    DocumentListResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse
)
from app.services.openrouter_service import openrouter_service
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


def _extract_api_key(authorization: Optional[str]) -> str:
    """Extract API key from Authorization header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Expected 'Bearer <api_key>'"
        )
    
    api_key = authorization.split(" ", 1)[1].strip()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is empty"
        )
    
    return api_key


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@router.post("/validate-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(authorization: Optional[str] = Header(default=None)):
    """
    Validate OpenRouter API key.
    
    Requires Authorization header with format: Bearer <api_key>
    """
    try:
        api_key = _extract_api_key(authorization)
        result = await openrouter_service.validate_api_key(api_key)
        
        return ApiKeyValidationResponse(
            valid=result["valid"],
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return ApiKeyValidationResponse(
            valid=False,
            message="Internal validation error"
        )


@router.post("/index-document", response_model=DocumentIndexResponse)
async def index_document(
    request: DocumentIndexRequest,
    authorization: Optional[str] = Header(default=None)
):
    """
    Index a document from URL for RAG search.
    
    Requires Authorization header with format: Bearer <api_key>
    """
    try:
        api_key = _extract_api_key(authorization)
        
        # Validate API key first
        validation = await openrouter_service.validate_api_key(api_key)
        if not validation["valid"]:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid API key: {validation['message']}"
            )
        
        # Discover related pages if crawling is enabled
        urls_to_process = await document_processor.discover_related_pages(
            str(request.url), 
            enable_crawling=request.enable_crawling
        )
        
        # Limit the number of pages based on request
        if hasattr(request, 'max_pages'):
            urls_to_process = urls_to_process[:request.max_pages]
        
        logger.info(f"Processing {len(urls_to_process)} pages for document '{request.label}'")
        
        # Scrape content from all discovered URLs
        if len(urls_to_process) == 1:
            # Single page - use the existing method
            doc_data = await document_processor.scrape_url(str(request.url))
            all_documents = [doc_data]
        else:
            # Multiple pages - use the new batch method
            all_documents = await document_processor.scrape_multiple_urls(urls_to_process)
        
        if not all_documents:
            raise HTTPException(
                status_code=400,
                detail="No content could be extracted from the provided URL(s)"
            )
        
        # Combine all documents into chunks
        all_chunks = []
        total_content_length = 0
        
        for doc_data in all_documents:
            # Add label and multi-page info to document data
            doc_data["label"] = request.label
            doc_data["is_multi_page"] = len(all_documents) > 1
            
            # Create text chunks for this document
            chunks = document_processor.chunk_text(
                doc_data["content"],
                metadata={
                    "title": doc_data["title"],
                    "url": doc_data["url"],
                    "label": request.label,
                    "page_number": doc_data.get("page_number", 1),
                    "total_pages": len(all_documents)
                }
            )
            
            all_chunks.extend(chunks)
            total_content_length += doc_data["content_length"]
        
        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No content could be extracted from the URL"
            )
        
        # Use the first document's data as the main document metadata
        main_doc_data = all_documents[0]
        main_doc_data["total_content_length"] = total_content_length
        main_doc_data["pages_count"] = len(all_documents)
        main_doc_data["urls_indexed"] = [doc["url"] for doc in all_documents]
        
        # Add to vector store
        document_id = await vector_store.add_document(main_doc_data, all_chunks, api_key)
        
        logger.info(f"Successfully indexed document {document_id} with {len(all_chunks)} chunks from {len(all_documents)} pages")
        
        return DocumentIndexResponse(
            success=True,
            message=f"Successfully indexed {len(all_documents)} page(s) for '{request.label}'",
            document_id=document_id,
            chunks_count=len(all_chunks),
            pages_crawled=len(all_documents),
            urls_indexed=[doc["url"] for doc in all_documents]
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during document indexing"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all indexed documents."""
    try:
        documents = vector_store.get_all_documents()
        
        # Format documents for response
        doc_list = []
        for doc in documents:
            doc_list.append({
                "document_id": doc["document_id"],
                "label": doc.get("label", "Untitled"),
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "chunks_count": doc.get("chunks_count", 0),
                "content_length": doc.get("content_length", 0)
            })
        
        return DocumentListResponse(documents=doc_list)
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing documents"
        )


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    authorization: Optional[str] = Header(default=None)
):
    """
    Query indexed documents using RAG.
    
    Requires Authorization header with format: Bearer <api_key>
    """
    try:
        api_key = _extract_api_key(authorization)
        
        # Validate API key
        validation = await openrouter_service.validate_api_key(api_key)
        if not validation["valid"]:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid API key: {validation['message']}"
            )
        
        # Check if we have any documents
        if len(vector_store.get_all_documents()) == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents have been indexed yet. Please index a document first."
            )
        
        # Search for relevant chunks
        max_docs = request.max_docs or settings.max_retrieve_docs
        similar_chunks = await vector_store.search_similar(
            query=request.question,
            api_key=api_key,
            top_k=max_docs,
            document_id=request.document_id
        )
        
        if not similar_chunks:
            # Still generate a response even if no chunks found
            context = "No relevant context found in the indexed documents."
            sources = []
        else:
            # Create context from similar chunks
            context_parts = []
            sources = []
            
            for chunk in similar_chunks:
                context_parts.append(chunk["text"])
                sources.append({
                    "document_id": chunk["document_id"],
                    "document_title": chunk["document_title"],
                    "document_url": chunk["document_url"],
                    "chunk_id": chunk["chunk_id"],
                    "similarity_score": chunk["score"],
                    "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                })
            
            context = "\n\n".join(context_parts)
        
        # Generate response using OpenRouter
        model_to_use = request.model or settings.default_llm_model
        
        system_prompt = (
            "You are a helpful assistant that answers questions based on provided context. "
            "Use ONLY the information in the context to answer the question. "
            "If the answer is not in the context, clearly state that the information is not available. "
            "Keep your answers concise and relevant."
        )
        
        user_prompt = f"Context:\n{context}\n\nQuestion: {request.question}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await openrouter_service.generate_chat_completion(
            messages=messages,
            api_key=api_key,
            model=model_to_use,
            temperature=0.1
        )
        
        logger.info(f"Generated response for query: {request.question[:50]}...")
        
        return QueryResponse(
            answer=response["content"],
            sources=sources,
            model_used=response["model"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during query processing"
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete an indexed document."""
    try:
        success = vector_store.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during document deletion"
        )


@router.get("/stats")
async def get_stats():
    """Get vector store statistics."""
    try:
        stats = vector_store.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting statistics"
        )

