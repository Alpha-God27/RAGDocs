"""API endpoints for RAGDocs."""
from fastapi import APIRouter, Header, HTTPException
from typing import Optional, List
from app.schemas import (
    ValidateKeyResponse,
    IndexUrlRequest,
    IndexUrlResponse,
    DocsListResponse,
    AskRequest,
    AskResponse,
)
import os
import re
import bs4
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from importlib import import_module
from typing import Any


def _build_ollama_embeddings(model_name: str) -> Any:
    """Import OllamaEmbeddings at runtime to avoid linter/env import errors."""
    try:
        module = import_module("langchain_ollama")
        Emb = getattr(module, "OllamaEmbeddings")
        return Emb(model=model_name)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=(
                "Ollama embeddings backend is not available. Ensure "
                "langchain_ollama is installed and Ollama is running."
            ),
        ) from exc


router = APIRouter(prefix="/api", tags=["api"])


CHROMA_ROOT = os.path.join("app", "data", "chroma")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RETRIEVE_TOP_K = 4


def ensure_dirs() -> None:
    os.makedirs(CHROMA_ROOT, exist_ok=True)


def slugify_label(label: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", label).strip("_").lower()


def get_persist_dir_for_label(label: str) -> str:
    ensure_dirs()
    return os.path.join(CHROMA_ROOT, slugify_label(label))


def validate_openrouter_key_or_raise(api_key: Optional[str]) -> None:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing OpenRouter API key",
        )
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenRouter API key",
            )
    except requests.RequestException:
        # Avoid long chained exception suggestion to keep lints quiet
        raise HTTPException(status_code=502, detail="OpenRouter unreachable")


@router.post("/validate_key", response_model=ValidateKeyResponse)
def validate_key(authorization: Optional[str] = Header(default=None)):
    api_key = None
    if authorization and authorization.lower().startswith("bearer "):
        api_key = authorization.split(" ", 1)[1].strip()
    validate_openrouter_key_or_raise(api_key)
    return ValidateKeyResponse()


@router.post("/index_url", response_model=IndexUrlResponse)
def index_url(
    payload: IndexUrlRequest,
    authorization: Optional[str] = Header(default=None),
):
    # Validate key now even though chat uses it later, per requirements.
    api_key = None
    if authorization and authorization.lower().startswith("bearer "):
        api_key = authorization.split(" ", 1)[1].strip()
    validate_openrouter_key_or_raise(api_key)

    loader = WebBaseLoader(
        web_paths=(payload.url,),
        bs_kwargs={
            "parse_only": bs4.SoupStrainer(
                class_=(
                    "post-content",
                    "post-title",
                    "post-header",
                ),
            ),
        },
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splits = splitter.split_documents(docs)

    persist_dir = get_persist_dir_for_label(payload.label)

    embeddings = _build_ollama_embeddings(EMBED_MODEL)
    _ = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_dir,
    )

    return IndexUrlResponse(label=payload.label, persist_dir=persist_dir)


@router.get("/docs", response_model=DocsListResponse)
def list_docs():
    ensure_dirs()
    labels: List[str] = []
    for name in sorted(os.listdir(CHROMA_ROOT)):
        path = os.path.join(CHROMA_ROOT, name)
        if os.path.isdir(path):
            labels.append(name)
    return DocsListResponse(labels=labels)


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    authorization: Optional[str] = Header(default=None),
):
    api_key = None
    if authorization and authorization.lower().startswith("bearer "):
        api_key = authorization.split(" ", 1)[1].strip()
    validate_openrouter_key_or_raise(api_key)

    persist_dir = get_persist_dir_for_label(payload.label)
    if not os.path.isdir(persist_dir):
        raise HTTPException(status_code=404, detail="Document not indexed")

    embeddings = _build_ollama_embeddings(EMBED_MODEL)
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )
    retriever = vectordb.as_retriever(
        search_kwargs={"k": RETRIEVE_TOP_K}
    )
    docs = retriever.get_relevant_documents(payload.question)
    context = "\n\n".join(d.page_content for d in docs)

    system_prompt = (
        "You are a helpful assistant. Answer the user using ONLY the provided "
        "context. If the answer is not in the context, say you don't know. "
        "Keep answers concise."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {payload.question}"

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": payload.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=60,
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"OpenRouter error: {resp.text}",
            )
        data = resp.json()
        answer = data.get("choices", [{}])[0].get(
            "message", {}
        ).get("content", "")
        return AskResponse(answer=answer or "")
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="OpenRouter unreachable")

