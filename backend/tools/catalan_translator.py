import httpx
from typing import Dict, Any, List, Optional
from .base import BaseTool, ToolDefinition, ToolParameter

class CatalanTranslatorTool(BaseTool):
    """Tool for translating text using Apertium-compatible translation APIs like Softcatalà"""
    
    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'SoftcatalaAgent/1.0 (Educational Use)',
                'Accept': 'application/json'
            }
        )
        # API endpoints
        self.apertium_url = "https://www.softcatala.org/api/traductor/translate"
        self.neuronal_url = "https://api.softcatala.org/v2/nmt/translate/"
        self.apertium_key = "NmQ3NmMyNThmM2JjNWQxMjkxN2N"
        
        # Language codes mapping
        self.language_names = {
            'en': 'anglès',
            'deu': 'alemany', 
            'cat': 'català',
            'spa': 'castellà',
            'oc_aran': 'occità/aranès',
            'oci': 'occità/llenguadoc',
            'ron': 'romanès',
            'arg': 'aragonès',
            'fr': 'francès',
            'pt': 'portuguès',
            'nld': 'neerlandès',
            'ita': 'italià',
            'jpn': 'japonès',
            'glg': 'gallec',
            'eus': 'basc',
            'cat_valencia': 'català valencià'
        }
        
        # Languages supported by neuronal translator
        self.neuronal_langs = ["en", "deu", "ita", "nld", "fr", "pt", "jpn", "glg", "oci", "eus"]
        
        # Languages with both translators available
        self.langs_with_both = ["en", "fr", "pt"]
        
        # Languages only available on neuronal
        self.langs_only_neuronal = ["deu", "ita", "nld", "jpn", "glg", "oci", "eus"]
        
        # Generate supported language pairs
        self.language_pairs = self._generate_language_pairs()
    
    def _generate_language_pairs(self) -> Dict[str, str]:
        """Generate supported language pairs based on API capabilities"""
        pairs = {}
        
        # All supported languages can translate to/from Catalan
        for lang_code, lang_name in self.language_names.items():
            if lang_code == 'cat':
                continue
            if lang_code == 'cat_valencia':
                # Special case: Valencian Catalan is only a target language
                pairs['spa|cat_valencia'] = 'Castellà ➝ Català valencià'
                continue
                
            # From Catalan to other language
            pairs[f'cat|{lang_code}'] = f'Català ➝ {lang_name.title()}'
            # From other language to Catalan
            pairs[f'{lang_code}|cat'] = f'{lang_name.title()} ➝ Català'
        
        return pairs
    
    def _should_use_neuronal(self, langpair: str) -> bool:
        """Determine whether to use neuronal or apertium API based on language pair"""
        source, target = langpair.split('|')
        
        # If either language is only available on neuronal, use neuronal
        if source in self.langs_only_neuronal or target in self.langs_only_neuronal:
            return True
            
        # For languages with both translators, prefer neuronal (better quality)
        if source in self.langs_with_both or target in self.langs_with_both:
            return True
            
        # Default to apertium for other cases
        return False
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_translator",
            description="Translate text between Catalan and other languages using Softcatalà translation services (Apertium and Neuronal APIs). Supports translation between Catalan and: Spanish, English, French, Italian, Portuguese, German, Dutch, Japanese, Galician, Basque, Occitan (Aranese and Languedoc), Romanian, and Aragonese. Also supports Spanish to Valencian Catalan.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="The text to translate",
                    required=True
                ),
                ToolParameter(
                    name="langpair",
                    type="string", 
                    description="Language pair in format 'source|target' (e.g., 'en|cat' for English to Catalan, 'cat|spa' for Catalan to Spanish). Use language codes: cat (Catalan), spa (Spanish), en (English), fr (French), pt (Portuguese), deu (German), ita (Italian), nld (Dutch), jpn (Japanese), glg (Galician), eus (Basque), oci (Occitan/Languedoc), oc_aran (Occitan/Aranese), ron (Romanian), arg (Aragonese), cat_valencia (Valencian Catalan - target only from Spanish)",
                    required=True
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="Output format: 'txt' for plain text (default), 'html' for HTML formatting",
                    required=False,
                    default="txt"
                )
            ]
        )
    
    @property
    def catalan_definition(self) -> ToolDefinition:
        """Catalan version of the tool definition for use with Catalan prompts"""
        return ToolDefinition(
            name="catalan_translator",
            description="Tradueix text entre el català i altres llengües utilitzant els serveis de traducció de Softcatalà (APIs Apertium i Neuronal). Suporta la traducció entre català i: castellà, anglès, francès, italià, portuguès, alemany, neerlandès, japonès, gallec, basc, occità (aranès i llenguadocià), romanès i aragonès. També suporta castellà a català valencià.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="El text a traduir",
                    required=True
                ),
                ToolParameter(
                    name="langpair", 
                    type="string",
                    description="Parell de llengües en format 'origen|destí' (p.ex., 'en|cat' per anglès a català, 'cat|spa' per català a castellà). Codis de llengua: cat (català), spa (castellà), en (anglès), fr (francès), pt (portuguès), deu (alemany), ita (italià), nld (neerlandès), jpn (japonès), glg (gallec), eus (basc), oci (occità/llenguadoc), oc_aran (occità/aranès), ron (romanès), arg (aragonès), cat_valencia (català valencià - només destí des del castellà)",
                    required=True
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="Format de sortida: 'txt' per text pla (per defecte), 'html' per format HTML",
                    required=False,
                    default="txt"
                )
            ]
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the translation request"""
        try:
            # Validate parameters
            self.validate_parameters(kwargs)
            
            text = kwargs.get('text', '').strip()
            langpair = kwargs.get('langpair', '').strip()
            format_type = kwargs.get('format', 'txt').strip()
            
            if not text:
                return {
                    'success': False,
                    'error': 'El text a traduir no pot estar buit',
                    'error_en': 'Text to translate cannot be empty'
                }
            
            if not langpair:
                return {
                    'success': False,
                    'error': 'Cal especificar el parell de llengües',
                    'error_en': 'Language pair must be specified'
                }
                
            if langpair not in self.language_pairs:
                available_pairs = ', '.join(sorted(self.language_pairs.keys()))
                return {
                    'success': False,
                    'error': f'Parell de llengües no suportat: {langpair}. Parells disponibles: {available_pairs}',
                    'error_en': f'Unsupported language pair: {langpair}. Available pairs: {available_pairs}',
                    'supported_pairs': self.language_pairs
                }
            
            # Perform translation
            result = await self._translate(text, langpair, format_type)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en la traducció: {str(e)}',
                'error_en': f'Translation error: {str(e)}'
            }
    
    async def _translate(self, text: str, langpair: str, format_type: str) -> Dict[str, Any]:
        """Perform the actual translation using Softcatalà's APIs"""
        try:
            use_neuronal = self._should_use_neuronal(langpair)
            
            if use_neuronal:
                return await self._translate_neuronal(text, langpair, format_type)
            else:
                return await self._translate_apertium(text, langpair, format_type)
                
        except Exception as e:
            self.logger.error(f"Error en la traducció: {str(e)}")
            return {
                'success': False,
                'error': f'Error inesperat: {str(e)}',
                'error_en': f'Unexpected error: {str(e)}'
            }
    
    async def _translate_apertium(self, text: str, langpair: str, format_type: str) -> Dict[str, Any]:
        """Translate using the Apertium API"""
        try:
            data = {
                'langpair': langpair,
                'q': text,
                'markUnknown': 'false',
                'key': self.apertium_key
            }
            
            self.logger.info(f"Apertium API request: {data}")

            if format_type != 'txt':
                data['format'] = format_type
                
            response = await self.client.post(self.apertium_url, data=data)
            response.raise_for_status()
            
            response_data = response.json()

            self.logger.info(f"Apertium API response: {response_data}")

            if 'responseData' in response_data and 'translatedText' in response_data['responseData']:
                translated_text = response_data['responseData']['translatedText']
                
                return {
                    'success': True,
                    'original_text': text,
                    'translated_text': translated_text,
                    'language_pair': langpair,
                    'language_pair_description': self.language_pairs.get(langpair, langpair),
                    'service': 'Softcatalà Apertium API',
                    'format': format_type
                }
            else:
                return {
                    'success': False,
                    'error': 'Format de resposta API inesperat',
                    'error_en': 'Unexpected API response format',
                    'response': response_data
                }
                
        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'error': f'Error HTTP de l\'API: {e.response.status_code}',
                'error_en': f'API HTTP error: {e.response.status_code}',
                'details': e.response.text if hasattr(e.response, 'text') else str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error de l\'API Apertium: {str(e)}',
                'error_en': f'Apertium API error: {str(e)}'
            }
    
    async def _translate_neuronal(self, text: str, langpair: str, format_type: str) -> Dict[str, Any]:
        """Translate using the Neuronal API"""
        try:
            data = {
                'langpair': langpair,
                'q': text,
                'savetext': 'false'
            }
            
            self.logger.info(f"Neuronal API request: {data}")

            response = await self.client.post(self.neuronal_url, data=data)
            response.raise_for_status()
            
            response_data = response.json()

            self.logger.debug(f"Neuronal API response: {response_data}")
            
            if 'responseData' in response_data and 'translatedText' in response_data['responseData']:
                translated_text = response_data['responseData']['translatedText']
                
                return {
                    'success': True,
                    'original_text': text,
                    'translated_text': translated_text,
                    'language_pair': langpair,
                    'language_pair_description': self.language_pairs.get(langpair, langpair),
                    'service': 'Softcatalà Neuronal API',
                    'format': format_type
                }
            else:
                return {
                    'success': False,
                    'error': 'Format de resposta API inesperat',
                    'error_en': 'Unexpected API response format',
                    'response': response_data
                }
                
        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'error': f'Error HTTP de l\'API: {e.response.status_code}',
                'error_en': f'API HTTP error: {e.response.status_code}',
                'details': e.response.text if hasattr(e.response, 'text') else str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error de l\'API Neuronal: {str(e)}',
                'error_en': f'Neuronal API error: {str(e)}'
            }
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported language pairs"""
        return {
            'success': True,
            'supported_pairs': self.language_pairs,
            'total_pairs': len(self.language_pairs),
            'languages': self.language_names,
            'neuronal_supported': self.neuronal_langs,
            'both_translators': self.langs_with_both,
            'neuronal_only': self.langs_only_neuronal
        }
    
    def __del__(self):
        """Clean up the HTTP client"""
        try:
            if hasattr(self, 'client'):
                # Note: In async context, you'd want to call await self.client.aclose()
                # but __del__ is synchronous, so we just pass
                pass
        except:
            pass