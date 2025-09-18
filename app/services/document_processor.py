"""
Document processing service for RAGDocs.
Handles web scraping, text extraction, and text chunking.
"""

import re
import logging
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse, urlunparse
import httpx
from bs4 import BeautifulSoup
import html2text
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing operations including web scraping and text chunking."""
    
    def __init__(self):
        self.request_timeout = settings.request_timeout
        self.max_content_length = settings.max_content_length
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # Crawling configuration
        self.max_pages_per_site = 10  # Limit to prevent excessive crawling
        self.crawl_depth = 2  # How deep to crawl from the starting URL
        
        # Configure html2text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # Don't wrap lines
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL and extract readable text.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing extracted text and metadata
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If content is too large or invalid
        """
        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                # Check content length
                content_length = len(response.content)
                if content_length > self.max_content_length:
                    raise ValueError(f"Content too large: {content_length} bytes (max: {self.max_content_length})")
                
                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else urlparse(url).netloc
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                
                # Convert to markdown-like text
                html_content = str(soup)
                text_content = self.html_converter.handle(html_content)
                
                # Clean up the text
                text_content = self._clean_text(text_content)
                
                return {
                    "url": str(response.url),
                    "title": title_text,
                    "content": text_content,
                    "content_length": len(text_content),
                    "original_url": url
                }
                
        except httpx.TimeoutException:
            raise ValueError(f"Request timeout while fetching {url}")
        except httpx.HTTPError as e:
            raise ValueError(f"HTTP error while fetching {url}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing {url}: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove markdown artifacts that aren't useful
        text = re.sub(r'\[\s*\]\(\s*\)', '', text)  # Empty links
        
        # Clean up common web artifacts
        text = re.sub(r'\b(Cookie|Privacy Policy|Terms of Service)\b.*\n?', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks suitable for embedding.
        
        Args:
            text: The text to chunk
            metadata: Additional metadata to include with each chunk
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        if not text or not text.strip():
            return []
        
        # Split by paragraphs first to maintain context
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": metadata or {},
                        "chunk_id": len(chunks)
                    })
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text
                
                # If paragraph itself is too long, split it
                if len(paragraph) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(paragraph)
                    for sub_chunk in sub_chunks:
                        if current_chunk and len(current_chunk) + len(sub_chunk) + 2 > self.chunk_size:
                            chunks.append({
                                "text": current_chunk.strip(),
                                "metadata": metadata or {},
                                "chunk_id": len(chunks)
                            })
                            current_chunk = ""
                        
                        if current_chunk:
                            current_chunk += "\n\n" + sub_chunk
                        else:
                            current_chunk = sub_chunk
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": metadata or {},
                "chunk_id": len(chunks)
            })
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get text for overlap between chunks."""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to find a good break point (sentence or paragraph end)
        overlap_start = len(text) - self.chunk_overlap
        
        # Look for sentence boundaries
        for i in range(overlap_start, len(text)):
            if text[i] in '.!?\n':
                return text[i+1:].strip()
        
        # Fallback to character split
        return text[-self.chunk_overlap:]
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split a long paragraph into smaller chunks."""
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    word_chunk = ""
                    for word in words:
                        if len(word_chunk) + len(word) + 1 > self.chunk_size:
                            if word_chunk:
                                chunks.append(word_chunk.strip())
                            word_chunk = word
                        else:
                            if word_chunk:
                                word_chunk += " " + word
                            else:
                                word_chunk = word
                    if word_chunk:
                        current_chunk = word_chunk
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def discover_related_pages(self, base_url: str, enable_crawling: bool = True) -> List[str]:
        """
        Discover related documentation pages from a base URL.
        
        Args:
            base_url: The starting URL to crawl from
            enable_crawling: Whether to enable multi-page crawling
            
        Returns:
            List of discovered URLs
        """
        if not enable_crawling:
            return [base_url]
        
        try:
            discovered_urls = set([base_url])
            base_domain = urlparse(base_url).netloc
            base_path = urlparse(base_url).path
            
            # Extract base path pattern (e.g., /tutorial/ from /tutorial/first-steps/)
            path_parts = [p for p in base_path.split('/') if p]
            if path_parts:
                base_section = '/' + path_parts[0] + '/'
            else:
                base_section = '/'
            
            # Get initial page to find navigation links
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(base_url, follow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find navigation or menu links that are likely documentation pages
                nav_selectors = [
                    'nav a',  # Navigation links
                    '.sidebar a',  # Sidebar links
                    '.toc a',  # Table of contents
                    '.menu a',  # Menu links
                    'aside a',  # Aside navigation
                    '[class*="nav"] a',  # Any element with "nav" in class
                    '[class*="menu"] a',  # Any element with "menu" in class
                    '[class*="sidebar"] a',  # Any element with "sidebar" in class
                ]
                
                found_links = set()
                for selector in nav_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            found_links.add(href)
                
                # Process and filter links
                for href in found_links:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # Only include links from the same domain
                    if parsed.netloc != base_domain:
                        continue
                    
                    # Only include links that are in the same section or subsections
                    if not (parsed.path.startswith(base_section) or 
                           parsed.path == '/' or 
                           any(section in parsed.path.lower() for section in 
                               ['doc', 'guide', 'tutorial', 'reference', 'api'])):
                        continue
                    
                    # Remove fragments and clean URL
                    clean_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path, 
                        parsed.params, parsed.query, ''
                    ))
                    
                    # Avoid common non-content pages
                    if any(exclude in clean_url.lower() for exclude in 
                          ['#', 'javascript:', 'mailto:', '.pdf', '.zip', '.tar',
                           'github.com', 'twitter.com', 'edit', 'search']):
                        continue
                    
                    discovered_urls.add(clean_url)
                    
                    # Limit to prevent excessive crawling
                    if len(discovered_urls) >= self.max_pages_per_site:
                        break
            
            logger.info(f"Discovered {len(discovered_urls)} related pages for {base_url}")
            return list(discovered_urls)
            
        except Exception as e:
            logger.warning(f"Error discovering related pages for {base_url}: {e}")
            return [base_url]  # Fallback to just the original URL
    
    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape content from multiple URLs efficiently.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped document data
        """
        documents = []
        
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Scraping page {i+1}/{len(urls)}: {url}")
                    doc_data = await self._scrape_single_url(client, url)
                    
                    # Add page info to distinguish between pages
                    doc_data['page_number'] = i + 1
                    doc_data['total_pages'] = len(urls)
                    doc_data['is_multi_page'] = len(urls) > 1
                    
                    documents.append(doc_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
        
        logger.info(f"Successfully scraped {len(documents)} out of {len(urls)} pages")
        return documents
    
    async def _scrape_single_url(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """
        Scrape a single URL using an existing HTTP client.
        
        Args:
            client: HTTP client instance
            url: URL to scrape
            
        Returns:
            Document data dictionary
        """
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        # Check content length
        content_length = len(response.content)
        if content_length > self.max_content_length:
            raise ValueError(f"Content too large: {content_length} bytes (max: {self.max_content_length})")
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else urlparse(url).netloc
        
        # Try to extract a more specific page title from headings
        main_heading = soup.find(['h1', 'h2']) 
        if main_heading and main_heading.get_text().strip():
            page_title = main_heading.get_text().strip()
            title_text = f"{page_title} - {title_text}"
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Convert to markdown-like text
        html_content = str(soup)
        text_content = self.html_converter.handle(html_content)
        
        # Clean up the text
        text_content = self._clean_text(text_content)
        
        return {
            "url": str(response.url),
            "title": title_text,
            "content": text_content,
            "content_length": len(text_content),
            "original_url": url
        }


# Create a singleton instance
document_processor = DocumentProcessor()