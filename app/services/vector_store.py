"""
Vector store service for RAGDocs.
Handles vector storage, similarity search, and document management using simple cosine similarity.
"""

import os
import json
import uuid
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
from app.config import settings
from app.services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage and similarity search using simple numpy operations."""
    
    def __init__(self):
        self.store_path = Path(settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Document storage: document_id -> document metadata
        self.documents: Dict[str, Dict[str, Any]] = {}
        
        # Chunk storage: chunk_id -> chunk data
        self.chunks: Dict[str, Dict[str, Any]] = {}
        
        # Vector storage: list of embeddings
        self.embeddings: List[List[float]] = []
        
        # Mapping from embedding index to chunk_id
        self.index_to_chunk_id: List[str] = []
        
        # Load existing data if available
        self._load_store()
    
    def _load_store(self):
        """Load vector store from disk."""
        try:
            # Load documents metadata
            docs_file = self.store_path / "documents.json"
            if docs_file.exists():
                with open(docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            
            # Load chunks metadata
            chunks_file = self.store_path / "chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
            
            # Load embeddings
            embeddings_file = self.store_path / "embeddings.pkl"
            if embeddings_file.exists():
                with open(embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            
            # Load index mapping
            mapping_file = self.store_path / "index_mapping.pkl"
            if mapping_file.exists():
                with open(mapping_file, 'rb') as f:
                    self.index_to_chunk_id = pickle.load(f)
            
            logger.info(f"Loaded vector store with {len(self.documents)} documents and {len(self.chunks)} chunks")
            
        except Exception as e:
            logger.warning(f"Error loading vector store: {e}")
            # Initialize empty store
            self.documents = {}
            self.chunks = {}
            self.embeddings = []
            self.index_to_chunk_id = []
    
    def _save_store(self):
        """Save vector store to disk."""
        try:
            # Save documents metadata
            with open(self.store_path / "documents.json", 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            # Save chunks metadata
            with open(self.store_path / "chunks.json", 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)
            
            # Save embeddings
            with open(self.store_path / "embeddings.pkl", 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            # Save index mapping
            with open(self.store_path / "index_mapping.pkl", 'wb') as f:
                pickle.dump(self.index_to_chunk_id, f)
            
            logger.info("Vector store saved to disk")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    async def add_document(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]], api_key: str) -> str:
        """
        Add a document and its chunks to the vector store.
        
        Args:
            document_data: Document metadata
            chunks: List of text chunks with metadata
            api_key: OpenRouter API key for embeddings
            
        Returns:
            Document ID
        """
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Store document metadata
            self.documents[document_id] = {
                **document_data,
                "document_id": document_id,
                "chunks_count": len(chunks)
            }
            
            # Generate embeddings for all chunk texts
            chunk_texts = [chunk["text"] for chunk in chunks]
            
            # Use the async function directly (we're already in an async context)
            embeddings_list = await openrouter_service.create_embeddings(chunk_texts, api_key)
            
            # Store chunks and embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                chunk_id = f"{document_id}_{i}"
                
                self.chunks[chunk_id] = {
                    **chunk,
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "embedding_index": len(self.embeddings)
                }
                
                # Store embedding and mapping
                self.embeddings.append(embedding)
                self.index_to_chunk_id.append(chunk_id)
            
            # Save to disk
            self._save_store()
            
            logger.info(f"Added document {document_id} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise ValueError(f"Failed to add document: {str(e)}")
    
    async def search_similar(
        self, 
        query: str, 
        api_key: str,
        top_k: int = 4, 
        document_id: Optional[str] = None,
        similarity_threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query
            api_key: OpenRouter API key for embeddings
            top_k: Number of results to return
            document_id: Optional document ID to search within
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with similarity scores
        """
        try:
            if not self.embeddings or len(self.chunks) == 0:
                return []
            
            # Generate query embedding
            query_embeddings = await openrouter_service.create_embeddings([query], api_key)
            query_embedding = query_embeddings[0]
            
            # Calculate similarities
            similarities = []
            for i, stored_embedding in enumerate(self.embeddings):
                # Simple cosine similarity
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                similarities.append((similarity, i))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Filter and format results
            results = []
            for similarity, idx in similarities[:top_k * 2]:  # Get more than needed for filtering
                if similarity < similarity_threshold:
                    continue
                
                chunk_id = self.index_to_chunk_id[idx]
                chunk = self.chunks.get(chunk_id)
                
                if chunk is None:
                    continue
                
                # Filter by document if specified
                if document_id and chunk.get("document_id") != document_id:
                    continue
                
                # Add document metadata
                doc_metadata = self.documents.get(chunk["document_id"], {})
                
                results.append({
                    "chunk_id": chunk_id,
                    "text": chunk["text"],
                    "score": float(similarity),
                    "document_id": chunk["document_id"],
                    "document_title": doc_metadata.get("title", ""),
                    "document_url": doc_metadata.get("url", ""),
                    "chunk_metadata": chunk.get("metadata", {})
                })
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import math
            
            # Ensure vectors are same length
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0.0
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        return self.documents.get(document_id)
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all document metadata."""
        return list(self.documents.values())
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.
        Note: This is a simplified implementation. In production, you might want
        to rebuild the FAISS index to remove the vectors completely.
        """
        try:
            if document_id not in self.documents:
                return False
            
            # Remove chunks belonging to this document
            chunks_to_remove = [
                chunk_id for chunk_id, chunk in self.chunks.items()
                if chunk.get("document_id") == document_id
            ]
            
            for chunk_id in chunks_to_remove:
                del self.chunks[chunk_id]
            
            # Remove document
            del self.documents[document_id]
            
            # Note: For simplicity, we're not rebuilding the FAISS index
            # In production, you might want to rebuild it periodically
            
            self._save_store()
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "total_embeddings": len(self.embeddings),
            "embedding_dimension": len(self.embeddings[0]) if self.embeddings else 0
        }


# Create a singleton instance
vector_store = VectorStore()