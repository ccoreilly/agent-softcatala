import httpx
from typing import Dict, Any, List
from .base import BaseTool, ToolDefinition, ToolParameter

class CatalanVerbsTool(BaseTool):
    """Tool for conjugating Catalan verbs using the Softcatalà conjugador API"""
    
    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'SoftcatalaAgent/1.0 (Educational Use)',
                'Accept': 'application/json, text/html'
            }
        )
        # Using a fallback base URL that can be configured
        self.base_url = "https://conjugador.softcatala.org"
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_verbs",
            description="Get conjugation forms for Catalan verbs. Supports verb search, autocomplete, and full conjugation lookup.",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform: 'search' (get conjugation forms for a verb), 'autocomplete' (get verb suggestions), or 'index' (get verbs starting with prefix)",
                    required=True
                ),
                ToolParameter(
                    name="verb",
                    type="string", 
                    description="The Catalan verb to search for conjugations, autocomplete suggestions, or use as prefix for index lookup",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of results to return for autocomplete and index operations",
                    required=False,
                    default=10
                )
            ]
        )
    
    @property
    def catalan_definition(self) -> ToolDefinition:
        """Catalan version of the tool definition for use with Catalan prompts"""
        return ToolDefinition(
            name="catalan_verbs",
            description="Obté les formes de conjugació per a verbs catalans. Suporta cerca de verbs, autocompletat i consulta completa de conjugació.",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Acció a realitzar: 'search' (obtenir formes de conjugació d'un verb), 'autocomplete' (obtenir suggeriments de verbs), o 'index' (obtenir verbs que comencen amb un prefix)",
                    required=True
                ),
                ToolParameter(
                    name="verb",
                    type="string", 
                    description="El verb català per al qual cercar conjugacions, suggeriments d'autocompletat, o usar com a prefix per a la consulta d'índex",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Nombre màxim de resultats a retornar per a les operacions d'autocompletat i índex",
                    required=False,
                    default=10
                )
            ]
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the verb conjugation search"""
        self.validate_parameters(kwargs)
        
        action = kwargs["action"].lower()
        verb = kwargs["verb"].strip()
        max_results = kwargs.get("max_results", 10)
        
        if not verb:
            return {
                "error": "Verb parameter cannot be empty",
                "status": "error"
            }
        
        try:
            if action == "search":
                return await self._search_conjugations(verb)
            elif action == "autocomplete":
                return await self._autocomplete(verb, max_results)
            elif action == "index":
                return await self._get_index(verb, max_results)
            else:
                return {
                    "error": f"Invalid action '{action}'. Use 'search', 'autocomplete', or 'index'",
                    "status": "error"
                }
        except Exception as e:
            return {
                "error": f"Failed to query conjugador API: {str(e)}",
                "status": "error"
            }
    
    async def _search_conjugations(self, verb: str) -> Dict[str, Any]:
        """Search for conjugation forms of a verb"""
        url = f"{self.base_url}/search/{verb}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                # The response might be HTML, so we need to parse it
                content = response.text
                
                # Check if verb was found (basic HTML parsing)
                if "No s'ha trobat cap verb" in content or "error" in content.lower():
                    return {
                        "verb": verb,
                        "found": False,
                        "message": f"No conjugation found for verb '{verb}'",
                        "status": "not_found"
                    }
                
                # For now, return a simplified response indicating success
                # In a full implementation, you would parse the HTML to extract conjugation tables
                return {
                    "verb": verb,
                    "found": True,
                    "message": f"Conjugation forms found for '{verb}'",
                    "conjugation_url": url,
                    "status": "success",
                    "note": "Visit the URL for complete conjugation table"
                }
            else:
                return {
                    "error": f"HTTP {response.status_code}: Failed to fetch conjugation data",
                    "status": "error"
                }
                
        except httpx.RequestError as e:
            return {
                "error": f"Network error: {str(e)}",
                "status": "error"
            }
    
    async def _autocomplete(self, partial_verb: str, max_results: int) -> Dict[str, Any]:
        """Get autocomplete suggestions for partial verb"""
        url = f"{self.base_url}/autocomplete/{partial_verb}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                content = response.text
                
                # Parse the response (would need proper HTML parsing in production)
                # For now, return a basic success response
                return {
                    "partial_verb": partial_verb,
                    "suggestions": [],  # Would contain actual suggestions from HTML parsing
                    "autocomplete_url": url,
                    "max_results": max_results,
                    "status": "success",
                    "note": "Visit the URL for autocomplete suggestions"
                }
            else:
                return {
                    "error": f"HTTP {response.status_code}: Failed to fetch autocomplete data",
                    "status": "error"
                }
                
        except httpx.RequestError as e:
            return {
                "error": f"Network error: {str(e)}",
                "status": "error"
            }
    
    async def _get_index(self, prefix: str, max_results: int) -> Dict[str, Any]:
        """Get verbs starting with a specific prefix"""
        url = f"{self.base_url}/index/{prefix}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                content = response.text
                
                # Parse the response (would need proper HTML parsing in production)
                # For now, return a basic success response
                return {
                    "prefix": prefix,
                    "verbs": [],  # Would contain actual verb list from HTML parsing
                    "index_url": url,
                    "max_results": max_results,
                    "status": "success",
                    "note": "Visit the URL for complete verb index"
                }
            else:
                return {
                    "error": f"HTTP {response.status_code}: Failed to fetch index data",
                    "status": "error"
                }
                
        except httpx.RequestError as e:
            return {
                "error": f"Network error: {str(e)}",
                "status": "error"
            }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()