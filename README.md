# RAGDocs - Intelligent Document Query System

RAGDocs is a full-stack Retrieval-Augmented Generation (RAG) application that allows users to query external technical documentation and receive accurate answers based on the content of provided URLs.

## ✨ Features

- **🔗 URL-based Document Indexing**: Scrape and index content from any web URL
- **🧠 Intelligent Query Processing**: Advanced RAG system with OpenRouter integration
- **💬 Natural Language Queries**: Ask questions in plain English
- **📱 Modern Web Interface**: Clean, responsive UI built with vanilla JavaScript
- **🔐 Secure API Key Management**: Browser-based secure storage
- **📊 Real-time Document Management**: Add, view, and manage indexed documents
- **⚡ Fast Vector Search**: Efficient similarity search for relevant content retrieval

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- HTML5, CSS3 (with Tailwind CSS)
- Vanilla JavaScript (ES6+)
- Responsive design with modern UI components

**Backend:**
- **FastAPI**: High-performance Python web framework
- **OpenRouter**: LLM and embedding services
- **Custom Vector Store**: In-memory vector similarity search
- **Document Processing**: Web scraping with BeautifulSoup and html2text

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `html2text` - HTML to text conversion
- `pydantic` - Data validation

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   OpenRouter    │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   API           │
│                 │    │                 │    │                 │
│ • UI Components │    │ • API Routes    │    │ • LLM Models    │
│ • State Mgmt    │    │ • Document Proc │    │ • Embeddings    │
│ • API Calls     │    │ • Vector Store  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌─────────────────┐
                       │   Local Storage │
                       │                 │
                       │ • Documents     │
                       │ • Chunks        │
                       │ • Embeddings    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenRouter API Key ([Get one here](https://openrouter.ai/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd RAGDocs
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Open your browser:**
   Navigate to `http://127.0.0.1:8000`

### First-Time Setup

1. **Configure API Key:**
   - Click "Configure" in the sidebar
   - Enter your OpenRouter API key
   - The key is securely stored in your browser

2. **Add Your First Document:**
   - Click "+ Add URL" in the sidebar
   - Enter a descriptive label (e.g., "FastAPI Docs")
   - Paste the URL to index
   - Wait for processing to complete

3. **Start Querying:**
   - Type your question in the chat input
   - Get intelligent responses based on your indexed content

## 📖 User Guide

### Adding Documents

1. Click the **"+ Add URL"** button in the sidebar
2. Fill in the document details:
   - **Label**: A descriptive name for easy identification
   - **URL**: The web page URL to scrape and index
3. Click **"Add Document"** and wait for processing
4. The document will appear in your documents list when ready

### Querying Documents

1. Select a document from the sidebar (or query all documents)
2. Type your question in the chat input
3. Press Enter or click the send button
4. View the AI-generated response with source references

### Managing Documents

- **View Documents**: All indexed documents appear in the sidebar
- **Select Document**: Click on a document to search within it specifically
- **Delete Document**: Click the X button next to any document
- **Clear All**: Use the "Clear All" button to remove all documents

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Settings
APP_NAME=RAGDocs
DEBUG=True

# OpenRouter Configuration
OPENROUTER_API_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=60

# Embedding Model
EMBEDDING_MODEL=text-embedding-ada-002

# LLM Model
DEFAULT_LLM_MODEL=openai/gpt-3.5-turbo

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVE_DOCS=4

# Vector Store
VECTOR_STORE_PATH=./app/data/vector_store

# Web Scraping
REQUEST_TIMEOUT=30
MAX_CONTENT_LENGTH=1000000
```

### Customization Options

- **Chunk Size**: Adjust `CHUNK_SIZE` to control text chunk length
- **Overlap**: Modify `CHUNK_OVERLAP` for better context preservation
- **Models**: Change `DEFAULT_LLM_MODEL` to use different OpenRouter models
- **Timeouts**: Adjust `REQUEST_TIMEOUT` and `OPENROUTER_TIMEOUT` as needed

## 🏛️ Project Structure

```
RAGDocs/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── pydantic/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models for API validation
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py           # API routes for RAG functionality
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py    # Web scraping and text processing
│   │   ├── openrouter_service.py   # OpenRouter API integration
│   │   └── vector_store.py         # Vector storage and similarity search
│   ├── static/
│   │   ├── app.js            # Frontend JavaScript application
│   │   └── styles.css        # CSS styles (if any custom styles)
│   ├── templates/
│   │   └── index.html        # Main HTML template
│   └── data/
│       └── vector_store/     # Persistent vector storage
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

### Core Components

**Document Processor (`document_processor.py`)**
- Web scraping with BeautifulSoup
- HTML to text conversion
- Intelligent text chunking with overlap
- Content cleaning and normalization

**OpenRouter Service (`openrouter_service.py`)**
- API key validation
- Embedding generation (with fallback)
- Chat completion requests
- Error handling and retries

**Vector Store (`vector_store.py`)**
- Document and chunk storage
- Vector similarity search
- Persistent storage management
- Cosine similarity calculations

**API Routes (`chat.py`)**
- RESTful API endpoints
- Request validation
- Error handling
- Response formatting

## 🔌 API Reference

### Health Check
```http
GET /api/health
```

### Validate API Key
```http
POST /api/validate-key
Authorization: Bearer <api_key>
```

### Index Document
```http
POST /api/index-document
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "label": "Document Name",
  "url": "https://example.com/docs"
}
```

### List Documents
```http
GET /api/documents
```

### Query Documents
```http
POST /api/query
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "question": "Your question here",
  "document_id": "optional-document-id",
  "model": "optional-model-name",
  "max_docs": 4
}
```

### Delete Document
```http
DELETE /api/documents/{document_id}
```

## 🐛 Troubleshooting

### Common Issues

**"API key not configured"**
- Solution: Click "Configure" and enter your OpenRouter API key

**"No documents indexed"**
- Solution: Add documents using the "+ Add URL" button

**"Failed to scrape URL"**
- Check if the URL is accessible
- Ensure the website allows scraping
- Verify your internet connection

**"Request timeout"**
- The website might be slow to respond
- Try again later or increase `REQUEST_TIMEOUT` in config

**"Content too large"**
- The webpage content exceeds the size limit
- Increase `MAX_CONTENT_LENGTH` or use a more specific URL

### Debug Mode

Enable debug mode by setting `DEBUG=True` in your environment or config file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) for LLM and embedding services
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework

---

**RAGDocs** - Transform any web content into an intelligent, queryable knowledge base! 🚀


key : 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