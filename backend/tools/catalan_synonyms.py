import httpx
from typing import Dict, Any, List
from .base import BaseTool, ToolDefinition, ToolParameter

class CatalanSynonymsTool(BaseTool):
    """Tool for searching Catalan synonyms using the Softcatalà dictionary API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'SoftcatalaAgent/1.0 (Educational Use)',
                'Accept': 'application/json'
            }
        )
        self.base_url = "https://api.softcatala.org/sinonims/v1/api"
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_synonyms",
            description="Search for synonyms, antonyms and related words in the Catalan language dictionary. Supports word search, autocomplete, and word index lookup.",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform: 'search' (get synonyms for a word), 'autocomplete' (get word suggestions), or 'index' (get words starting with prefix)",
                    required=True
                ),
                ToolParameter(
                    name="word",
                    type="string", 
                    description="The Catalan word to search for synonyms, autocomplete suggestions, or use as prefix for index lookup",
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
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the synonyms search"""
        self.validate_parameters(kwargs)
        
        action = kwargs["action"].lower()
        word = kwargs["word"].strip()
        max_results = kwargs.get("max_results", 10)
        
        if not word:
            return {
                "error": "Word parameter cannot be empty",
                "status": "error"
            }
        
        try:
            if action == "search":
                return await self._search_synonyms(word)
            elif action == "autocomplete":
                return await self._autocomplete(word, max_results)
            elif action == "index":
                return await self._get_index(word, max_results)
            else:
                return {
                    "error": f"Invalid action '{action}'. Use 'search', 'autocomplete', or 'index'",
                    "status": "error"
                }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _search_synonyms(self, word: str) -> Dict[str, Any]:
        """Search for synonyms of a word"""
        url = f"{self.base_url}/search/{word}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 404:
                return {
                    "word": word,
                    "message": f"No synonyms found for '{word}'",
                    "results": [],
                    "status": "not_found"
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Process the response to extract key information
            processed_results = self._process_search_results(data)
            
            return {
                "word": word,
                "searched_word": data.get("searchedWord", word),
                "canonical_lemma": data.get("canonicalLemma", ""),
                "alternatives": data.get("alternatives", []),
                "results": processed_results,
                "status": "success"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "word": word,
                "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                "status": "error"
            }
    
    async def _autocomplete(self, prefix: str, max_results: int) -> Dict[str, Any]:
        """Get autocomplete suggestions for a word prefix"""
        url = f"{self.base_url}/autocomplete/{prefix}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 404:
                return {
                    "prefix": prefix,
                    "words": [],
                    "status": "not_found"
                }
            
            response.raise_for_status()
            data = response.json()
            
            words = data.get("words", [])[:max_results]
            
            return {
                "prefix": prefix,
                "start_with": data.get("startWith", prefix),
                "words": words,
                "count": len(words),
                "status": "success"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "prefix": prefix,
                "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                "status": "error"
            }
    
    async def _get_index(self, prefix: str, max_results: int) -> Dict[str, Any]:
        """Get words from the index starting with a prefix"""
        url = f"{self.base_url}/index/{prefix}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 404:
                return {
                    "prefix": prefix,
                    "words": [],
                    "status": "not_found"
                }
            
            response.raise_for_status()
            data = response.json()
            
            words = data.get("words", [])[:max_results]
            
            return {
                "prefix": prefix,
                "start_with": data.get("startWith", prefix),
                "words": words,
                "count": len(words),
                "status": "success"
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "prefix": prefix,
                "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                "status": "error"
            }
    
    def _process_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and simplify the search results"""
        results = []
        
        for result in data.get("results", []):
            lemma = result.get("lemma", "")
            grammar_category = result.get("grammarCategory", "")
            feminine_lemma = result.get("feminineLemma", "")
            
            # Process synonym entries
            synonyms = []
            for entry in result.get("synonymEntries", []):
                synonym_words = []
                for word_obj in entry.get("synonimWords", []):
                    word_info = {
                        "word": word_obj.get("wordString", ""),
                        "comment": word_obj.get("wordComment", ""),
                        "feminine_form": word_obj.get("feminineForm", ""),
                        "has_link": word_obj.get("link", False)
                    }
                    synonym_words.append(word_info)
                
                if synonym_words:
                    synonyms.append({
                        "words": synonym_words,
                        "comment": entry.get("comment", ""),
                        "grammar_category": entry.get("grammarCategory", grammar_category)
                    })
            
            # Process antonym entries
            antonyms = []
            for entry in result.get("antonymEntries", []):
                antonym_words = []
                for word_obj in entry.get("antonymWords", []):
                    word_info = {
                        "word": word_obj.get("wordString", ""),
                        "comment": word_obj.get("wordComment", ""),
                        "feminine_form": word_obj.get("feminineForm", ""),
                        "has_link": word_obj.get("link", False)
                    }
                    antonym_words.append(word_info)
                
                if antonym_words:
                    antonyms.append({
                        "words": antonym_words,
                        "comment": entry.get("comment", ""),
                        "grammar_category": entry.get("grammarCategory", grammar_category)
                    })
            
            result_info = {
                "lemma": lemma,
                "feminine_lemma": feminine_lemma,
                "grammar_category": grammar_category,
                "synonyms": synonyms,
                "antonyms": antonyms
            }
            results.append(result_info)
        
        return results
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()