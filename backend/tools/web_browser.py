import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
from .base import BaseTool, ToolDefinition, ToolParameter

class WebBrowserTool(BaseTool):
    """Tool for browsing web pages and extracting content"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_browser",
            description="Browse web pages and extract text content from URLs",
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="The URL to browse and extract content from",
                    required=True
                ),
                ToolParameter(
                    name="extract_links",
                    type="boolean",
                    description="Whether to extract links from the page",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="max_content_length",
                    type="integer",
                    description="Maximum length of content to extract",
                    required=False,
                    default=5000
                )
            ]
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute web browsing"""
        self.validate_parameters(kwargs)
        
        url = kwargs["url"]
        extract_links = kwargs.get("extract_links", False)
        max_content_length = kwargs.get("max_content_length", 5000)
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = soup.title.string if soup.title else "No title"
            
            # Extract main content
            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            result = {
                "url": url,
                "title": title.strip(),
                "content": content,
                "status": "success"
            }
            
            # Extract links if requested
            if extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    text = link.get_text().strip()
                    if href.startswith('http') and text:
                        links.append({"url": href, "text": text})
                result["links"] = links[:20]  # Limit to 20 links
            
            return result
            
        except httpx.HTTPStatusError as e:
            return {
                "url": url,
                "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                "status": "error"
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status": "error"
            }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()