import httpx
from typing import Dict, Any, List
from .base import BaseTool, ToolDefinition, ToolParameter

class CatalanSpellCheckerTool(BaseTool):
    """Tool for checking Catalan text for spelling and grammatical errors using the Softcatalà corrector API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'SoftcatalaAgent/1.0 (Educational Use)',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        self.base_url = "https://api.softcatala.org/corrector-dev/v2/check"
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_spell_checker",
            description="Check Catalan text for spelling, grammar, and style errors. Supports both standard Catalan and Valencian dialects. Returns detailed error information with suggestions for corrections.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="The Catalan text to check for spelling and grammatical errors",
                    required=True
                ),
                ToolParameter(
                    name="dialect",
                    type="string",
                    description="Catalan dialect to use: 'general' for standard Catalan or 'valencia' for Valencian. If not specified, the tool will automatically detect the appropriate dialect.",
                    required=False,
                    default="auto"
                )
            ]
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the spell checking"""
        self.validate_parameters(kwargs)
        
        text = kwargs["text"]
        dialect = kwargs.get("dialect", "auto")
        
        # Determine language code based on dialect
        if dialect == "valencia":
            language_code = "ca-ES-valencia"
        elif dialect == "general":
            language_code = "ca-ES"
        else:  # auto detection
            # Use general Catalan as default, let the API detect specifics
            language_code = "ca-ES"
        
        try:
            # Prepare request data
            data = {
                "language": language_code,
                "text": text
            }
            
            # Make API request
            response = await self.client.post(
                self.base_url,
                data=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Process the response
            return await self._process_response(result, text, language_code)
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"API request failed with status {e.response.status_code}: {e.response.text}",
                "text": text
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Network error occurred: {str(e)}",
                "text": text
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "text": text
            }
    
    async def _process_response(self, result: Dict[str, Any], original_text: str, language_code: str) -> Dict[str, Any]:
        """Process the API response and format it for the agent"""
        
        matches = result.get("matches", [])
        language_info = result.get("language", {})
        
        # Extract error information
        errors = []
        for match in matches:
            error_info = {
                "message": match.get("message", ""),
                "short_message": match.get("shortMessage", ""),
                "offset": match.get("offset", 0),
                "length": match.get("length", 0),
                "context": match.get("context", {}).get("text", ""),
                "suggestions": [r["value"] for r in match.get("replacements", [])],
                "rule_id": match.get("rule", {}).get("id", ""),
                "category": match.get("rule", {}).get("category", {}).get("name", ""),
                "issue_type": match.get("rule", {}).get("issueType", "")
            }
            errors.append(error_info)
        
        # Determine detected dialect
        detected_dialect = "general"
        detected_language_code = language_info.get("code", language_code)
        if "valencia" in detected_language_code.lower():
            detected_dialect = "valencia"
        
        # Count error types
        spelling_errors = len([e for e in errors if "spelling" in e["issue_type"].lower() or "ortogràfic" in e["category"].lower()])
        grammar_errors = len([e for e in errors if "grammar" in e["issue_type"].lower() or "gramàtic" in e["category"].lower()])
        style_errors = len([e for e in errors if "style" in e["issue_type"].lower() or "estil" in e["category"].lower()])
        other_errors = len(errors) - spelling_errors - grammar_errors - style_errors
        
        return {
            "success": True,
            "text": original_text,
            "detected_language": language_info.get("name", "Catalan"),
            "detected_dialect": detected_dialect,
            "language_confidence": language_info.get("detectedLanguage", {}).get("confidence", 0.0),
            "total_errors": len(errors),
            "error_summary": {
                "spelling": spelling_errors,
                "grammar": grammar_errors,
                "style": style_errors,
                "other": other_errors
            },
            "errors": errors,
            "is_correct": len(errors) == 0,
            "software_info": {
                "name": result.get("software", {}).get("name", "LanguageTool"),
                "version": result.get("software", {}).get("version", "Unknown")
            }
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()