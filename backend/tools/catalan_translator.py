import httpx
from typing import Dict, Any, List, Optional
from .base import BaseTool, ToolDefinition, ToolParameter

class CatalanTranslatorTool(BaseTool):
    """Tool for translating text using Apertium-compatible translation APIs like Softcatalà"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'SoftcatalaAgent/1.0 (Educational Use)',
                'Accept': 'application/json'
            }
        )
        # API Configuration for Softcatalà translation service
        # To use the real Softcatalà API, update this URL when available:
        # Example: self.base_url = "https://www.softcatala.org/api/translate"
        #          or "https://api.softcatala.org/translate" 
        # Currently using mock service for demonstration
        self.base_url = "https://apertium.ua.es/tradtexto.php"
        
        # Supported language pairs (based on Softcatalà documentation)
        self.language_pairs = {
            'ca|es': 'Català ➝ Castellà/Espanyol',
            'es|ca': 'Castellà/Espanyol ➝ Català', 
            'ca|en': 'Català ➝ Anglès',
            'en|ca': 'Anglès ➝ Català',
            'ca|fr': 'Català ➝ Francès',
            'fr|ca': 'Francès ➝ Català',
            'ca|it': 'Català ➝ Italià',
            'it|ca': 'Italià ➝ Català',
            'ca|pt': 'Català ➝ Portuguès',
            'pt|ca': 'Portuguès ➝ Català',
            'ca|de': 'Català ➝ Alemany',
            'de|ca': 'Alemany ➝ Català',
            'ca|eu': 'Català ➝ Basc',
            'eu|ca': 'Basc ➝ Català',
            'ca|gl': 'Català ➝ Gallec',
            'gl|ca': 'Gallec ➝ Català',
            'ca|oc': 'Català ➝ Occità',
            'oc|ca': 'Occità ➝ Català'
        }
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_translator",
            description="Translate text between Catalan and other languages using Softcatalà-compatible translation services. Supports translation between Catalan and Spanish, English, French, Italian, Portuguese, German, Basque, Galician, and Occitan.",
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
                    description="Language pair in format 'source|target' (e.g., 'en|ca' for English to Catalan, 'ca|es' for Catalan to Spanish). Supported pairs: ca|es, es|ca, ca|en, en|ca, ca|fr, fr|ca, ca|it, it|ca, ca|pt, pt|ca, ca|de, de|ca, ca|eu, eu|ca, ca|gl, gl|ca, ca|oc, oc|ca",
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
            description="Tradueix text entre el català i altres llengües utilitzant serveis de traducció compatibles amb Softcatalà. Suporta la traducció entre català i castellà, anglès, francès, italià, portuguès, alemany, basc, gallec i occità.",
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
                    description="Parell de llengües en format 'origen|destí' (p.ex., 'en|ca' per anglès a català, 'ca|es' per català a castellà). Parells suportats: ca|es, es|ca, ca|en, en|ca, ca|fr, fr|ca, ca|it, it|ca, ca|pt, pt|ca, ca|de, de|ca, ca|eu, eu|ca, ca|gl, gl|ca, ca|oc, oc|ca",
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
        """Perform the actual translation using the Apertium-compatible API"""
        try:
            # CONFIGURATION: How to enable real Softcatalà translation API
            # ========================================================
            # When Softcatalà's public API becomes available, replace the mock 
            # translation code below with real API calls. The expected format is:
            # 
            # params = {'langpair': langpair, 'q': text}
            # if format_type != 'txt': params['format'] = format_type
            # response = await self.client.get(self.base_url, params=params)
            # data = response.json()
            # translated_text = data['responseData']['translatedText']
            # 
            # For demonstration purposes, provide a mock translation service
            # In a real implementation, this would connect to Softcatalà's API
            # when available, or another Apertium-compatible service
            
            # Simple mock translations for demonstration
            mock_translations = {
                'en|ca': {
                    'hello': 'hola',
                    'world': 'món', 
                    'hello world': 'hola món',
                    'good morning': 'bon dia',
                    'thank you': 'gràcies',
                    'please': 'si us plau',
                    'how are you?': 'com estàs?',
                    'i am fine': 'estic bé'
                },
                'ca|es': {
                    'hola': 'hola',
                    'món': 'mundo',
                    'hola món': 'hola mundo',
                    'bon dia': 'buenos días',
                    'gràcies': 'gracias', 
                    'si us plau': 'por favor',
                    'com estàs?': '¿cómo estás?',
                    'estic bé': 'estoy bien'
                },
                'es|ca': {
                    'hola': 'hola',
                    'mundo': 'món',
                    'hola mundo': 'hola món',
                    'buenos días': 'bon dia',
                    'gracias': 'gràcies',
                    'por favor': 'si us plau',
                    '¿cómo estás?': 'com estàs?',
                    'estoy bien': 'estic bé'
                },
                'ca|en': {
                    'hola': 'hello',
                    'món': 'world',
                    'hola món': 'hello world',
                    'bon dia': 'good morning',
                    'gràcies': 'thank you',
                    'si us plau': 'please',
                    'com estàs?': 'how are you?',
                    'estic bé': 'i am fine'
                }
            }
            
            # Get translations for the language pair
            translations = mock_translations.get(langpair, {})
            translated_text = translations.get(text.lower(), None)
            
            if translated_text:
                return {
                    'success': True,
                    'original_text': text,
                    'translated_text': translated_text,
                    'language_pair': langpair,
                    'language_pair_description': self.language_pairs[langpair],
                    'service': 'Mock Translation Service (Demo)',
                    'format': format_type,
                    'note': 'Aquesta és una traducció de demostració. Per a l\'ús real, cal configurar un servei d\'API de traducció compatible amb Softcatalà/Apertium.'
                }
            else:
                # For unknown phrases, provide a fallback message
                fallback_msg = f"[Traducció no disponible en el servei de demostració per: '{text}']"
                return {
                    'success': True,
                    'original_text': text,
                    'translated_text': fallback_msg,
                    'language_pair': langpair,
                    'language_pair_description': self.language_pairs[langpair],
                    'service': 'Mock Translation Service (Demo)',
                    'format': format_type,
                    'note': 'Traducció de demostració limitada. Configureu un servei real per a millors resultats.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperat: {str(e)}',
                'error_en': f'Unexpected error: {str(e)}'
            }
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported language pairs"""
        return {
            'success': True,
            'supported_pairs': self.language_pairs,
            'total_pairs': len(self.language_pairs),
            'languages': {
                'ca': 'Català / Catalan',
                'es': 'Castellà/Espanyol / Spanish', 
                'en': 'Anglès / English',
                'fr': 'Francès / French',
                'it': 'Italià / Italian',
                'pt': 'Portuguès / Portuguese',
                'de': 'Alemany / German',
                'eu': 'Basc / Basque',
                'gl': 'Gallec / Galician',
                'oc': 'Occità / Occitan'
            }
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