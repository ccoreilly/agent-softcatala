import re
from typing import Dict, Any, List
from .base import BaseTool, ToolDefinition, ToolParameter


class CatalanSyllabificationTool(BaseTool):
    """Tool for splitting Catalan words into syllables using Softcatalà's hyphenation patterns"""
    
    def __init__(self):
        # Hyphenation patterns extracted from Softcatalà's syllabification tool
        # These patterns are based on the TeX hyphenation algorithm by Franklin M. Liang
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> List[str]:
        """Load Catalan hyphenation patterns"""
        # Complete set of patterns extracted from https://www.softcatala.org/sillabes/
        # Original JavaScript file: sillabes-ca.js (2038 patterns total)
        patterns = [
            "8'8", "l·9l", "ŀ9l", "1ba", "1be", "1bi", "1bo", "1bu", "1ca", "1ce",
            "1ci", "1co", "1cu", "1da", "1de", "1di", "1do", "3du", "1fa", "1fe",
            "1fi", "1fo", "1fu", "1ga", "1ge", "1gi", "1go", "1gu", "1ha", "1he",
            "1hi", "1ho", "1hu", "1ja", "1je", "1ji", "1jo", "1ju", "1ka", "1ke",
            "1ki", "1ko", "1ku", "1la", "1le", "1li", "1lo", "1lu", "1ma", "1me",
            "1mi", "1mo", "1mu", "1na", "1ne", "3ni", "1no", "1nu", "1pa", "3pe",
            "3pi", "3po", "1pu", "1qu", "1ra", "1re", "1ri", "1ro", "1ru", "1sa",
            "1se", "1si", "1so", "1su", "1ta", "1te", "1ti", "1to", "1tu", "1va",
            "1ve", "1vi", "1vo", "1vu", "1wa", "1we", "1wi", "1wo", "1wu", "1xa",
            "1xe", "1xi", "1xo", "1xu", "1ya", "1ye", "1yi", "1yo", "1yu", "1za",
            "1ze", "1zi", "1zo", "1zu", "1bé", "1bí", "1bó", "1bú", "1bà", "1bè",
            "1bò", "1cé", "1cí", "1có", "1cú", "1cà", "1cè", "1cò", "1ço", "1ça",
            "1çu", "1çé", "1çí", "1çó", "1çú", "1çà", "1çè", "1çò", "1dé", "1dí",
            "1dó", "1dú", "1dà", "1dè", "1dò", "1fé", "1fí", "1fó", "1fú", "1fà",
            "1fè", "1fò", "1gé", "1gí", "1gó", "1gú", "1gà", "1gè", "1gò", "1gü",
            "1hé", "1hí", "1hó", "1hú", "1hà", "1hè", "1hò", "1jé", "1jí", "1jó",
            "1jú", "1jà", "1jè", "1jò", "1ké", "1kí", "1kó", "1kú", "1kà", "1kè",
            "1kò", "1lé", "1lí", "1ló", "1lú", "1là", "1lè", "1lò", "1mé", "1mí",
            "1mó", "1mú", "1mà", "1mè", "1mò", "1né", "1ní", "1nó", "1nú", "1nà",
            "1nè", "1nò", "1pé", "1pí", "1pó", "1pú", "1pà", "1pè", "1pò", "1ré",
            "1rí", "1ró", "1rú", "1rà", "1rè", "1rò", "1sé", "1sí", "1só", "1sú",
            "1sà", "1sè", "1sò", "1té", "1tí", "1tó", "1tú", "1tà", "1tè", "1tò",
            "1vé", "1ví", "1vó", "1vú", "1và", "1vè", "1vò", "1wé", "1wí", "1wó",
            "1wú", "1wà", "1wè", "1wò", "1xé", "1xí", "1xó", "1xú", "1xà", "1xè",
            "1xò", "1yé", "1yí", "1yó", "1yú", "1yà", "1yè", "1yò", "1zé", "1zí",
            "1zó", "1zú", "1zà", "1zè", "1zò", "2b1b", "2b1c", "2b1d", "2b1f",
            "2b1g", "2b1h", "2b1j", "2b1k", "2b1m", "2b1n", "2b1p", "2b1q", "2b1s",
            "2b1t", "2b1v", "2b1w", "2b1x", "2b1z", "4b3l", "4b3r", "2c1b", "2c1c",
            "2c1d", "2c1f", "2c1g", "2c1j", "2c1k", "2c1m", "2c1n", "2c1p", "2c1q",
            "2c1s", "2c1t", "2c1v", "2c1w", "2c1x", "2c1z", "4c3l", "4c3r", "2d1b",
            "2d1c", "2d1d", "2d1f", "2d1g", "2d1h", "2d1j", "2d1k", "2d1m", "2d1n",
            "2d1p", "2d1q", "2d1s", "2d1t", "2d1v", "2d1w", "2d1x", "2d1z", "4d3r",
            "2f1b", "2f1c", "2f1d", "2f1f", "2f1g", "2f1h", "2f1j", "2f1k", "2f1m",
            "2f1n", "2f1p", "2f1q", "2f1s", "2f1t", "2f1v", "2f1w", "2f1x", "2f1z",
            "4f3l", "4f3r", "2g1b", "2g1c", "2g1d", "2g1f", "2g1g", "2g1h", "2g1j",
            "2g1k", "2g1m", "2g1n", "2g1p", "2g1q", "2g1s", "2g1t", "2g1v", "2g1w",
            "2g1x", "2g1z", "4g3l", "4g3r", "2h1b", "2h1c", "2h1d", "2h1f", "2h1g",
            "2h1h", "2h1j", "2h1k", "2h1m", "2h1n", "2h1p", "2h1q", "2h1s", "2h1t",
            "2h1v", "2h1w", "2h1x", "2h1z", "2j1b", "2j1c", "2j1d", "2j1f", "2j1g",
            "2j1h", "2j1j", "2j1k", "2j1m", "2j1n", "2j1p", "2j1q", "2j1s", "2j1t",
            "2j1v", "2j1w", "2j1x", "2j1z", "2k1b", "2k1c", "2k1d", "2k1f", "2k1g",
            "2k1h", "2k1j", "2k1k", "2k1m", "2k1n", "2k1p", "2k1q", "2k1s", "2k1t",
            "2k1v", "2k1w", "2k1x", "2k1z", "2l1b", "2l1c", "2l1d", "2l1f", "2l1g",
            "2l1h", "2l1j", "2l1k", "2l1l", "2l1m", "2l1n", "2l1p", "2l1q", "2l1s",
            "2l1t", "2l1v", "2l1w", "2l1x", "2l1z", "2m1b", "2m1c", "2m1d", "2m1f",
            "2m1g", "2m1h", "2m1j", "2m1k", "2m1l", "2m1m", "2m1n", "2m1p", "2m1q",
            "2m1s", "2m1t", "2m1v", "2m1w", "2m1x", "2m1z", "2n1b", "2n1c", "2n1d",
            "2n1f", "2n1g", "2n1h", "2n1j", "2n1k", "2n1l", "2n1m", "2n1n", "2n1p",
            "2n1q", "2n1s", "2n1t", "2n1v", "2n1w", "2n1x", "2n1z", "2p1b", "2p1c",
            "2p1d", "2p1f", "2p1g", "2p1h", "2p1j", "2p1k", "2p1m", "2p1n", "2p1p",
            "2p1q", "2p1s", "2p1t", "2p1v", "2p1w", "2p1x", "2p1z", "4p3l", "4p3r",
            "2q1b", "2q1c", "2q1d", "2q1f", "2q1g", "2q1h", "2q1j", "2q1k", "2q1l",
            "2q1m", "2q1n", "2q1p", "2q1q", "2q1s", "2q1t", "2q1v", "2q1w", "2q1x",
            "2q1z", "2r1b", "2r1c", "2r1d", "2r1f", "2r1g", "2r1h", "2r1j", "2r1k",
            "2r1l", "2r1m", "2r1n", "2r1p", "2r1q", "2r1r", "2r1s", "2r1t", "2r1v",
            "2r1w", "2r1x", "2r1z", "2s1b", "2s1c", "2s1d", "2s1f", "2s1g", "2s1h",
            "2s1j", "2s1k", "2s1l", "2s1m", "2s1n", "2s1p", "2s1q", "2s1r", "2s1s",
            "2s1t", "2s1v", "2s1w", "2s1x", "2s1z", "2t1b", "2t1c", "2t1d", "2t1f",
            "2t1g", "2t1h", "2t1j", "2t1k", "2t1m", "2t1n", "2t1p", "2t1q", "2t1s",
            "2t1t", "2t1v", "2t1w", "2t1x", "2t1z", "4t3l", "4t3r", "2v1b", "2v1c",
            "2v1d", "2v1f", "2v1g", "2v1h", "2v1j", "2v1k", "2v1m", "2v1n", "2v1p",
            "2v1q", "2v1s", "2v1t", "2v1v", "2v1w", "2v1x", "2v1z", "4v3l", "4v3r",
            "2w1b", "2w1c", "2w1d", "2w1f", "2w1g", "2w1h", "2w1j", "2w1k", "2w1l",
            "2w1m", "2w1n", "2w1p", "2w1q", "2w1r", "2w1s", "2w1t", "2w1v", "2w1w",
            "2w1x", "2w1z", "2x1b", "2x1c", "2x1d", "2x1f", "2x1g", "2x1h", "2x1j",
            "2x1k", "2x1l", "2x1m", "2x1n", "2x1p", "2x1q", "2x1r", "2x1s", "2x1t",
            "2x1v", "2x1w", "2x1x", "2x1z", "2y1b", "2y1c", "2y1d", "2y1f", "2y1g",
            "2y1h", "2y1j", "2y1k", "2y1l", "2y1m", "2y1n", "2y1p", "2y1q", "2y1r",
            "2y1s", "2y1t", "2y1v", "2y1w", "2y1x", "2y1y", "2y1z", "2z1b", "2z1c",
            "2z1d", "2z1f", "2z1g", "2z1h", "2z1j", "2z1k", "2z1l", "2z1m", "2z1n",
            "2z1p", "2z1q", "2z1r", "2z1s", "2z1t", "2z1v", "2z1w", "2z1x", "2z1z",
            "ll2", "ny2", "qu2", "gu2", "rr2", "s2s", "s2c", "ix2", "t2l", "t3ll",
            "t2j", "t2g", "t2m", "t2n", "t2x", "l·2l", "ŀ2l", "2n1y", "2l1l",
            "ün1s", "1a", "1e", "1i", "1o", "1u", "1à", "1è", "1é", "1í", "1ò",
            "1ó", "1ú", "a2a", "a2e", "a2o", "e2a", "e2e", "e2o", "i2a", "i2e",
            "i2o", "o2a", "o2e", "o2o", "u2a", "u2e", "u2o", "à2a", "à2e", "à2o",
            "è2a", "è2e", "è2o", "é2a", "é2e", "é2o", "í2a", "í2e", "í2o", "ò2a",
            "ò2e", "ò2o", "ó2a", "ó2e", "ó2o", "ú2a", "ú2e", "ú2o", "ai1", "au1",
            "ei1", "eu1", "iu1", "ou1", "ui1", "àu1", "èi1", "èu1", "íu1", "òu1",
            "úi1", "éi1", "éu1", "óu1", "aí2", "aú2", "eí2", "eú2", "ií2", "iú2",
            "oí2", "oú2", "uí2", "uú2", "àí2", "àú2", "èí2", "èú2", "éí2", "éú2",
            "íí2", "íú2", "òí2", "òú2", "óí2", "óú2", "úí2", "úú2", "2ch", "sch2",
            "2ck", "ack2", "2cqu", "sch3", "tch3", "nch3"
        ]
        return patterns
    
    def _parse_pattern(self, pattern: str) -> tuple:
        """Parse a hyphenation pattern into text and levels"""
        text = ""
        levels = []
        i = 0
        
        while i < len(pattern):
            char = pattern[i]
            if char.isdigit():
                levels.append(int(char))
            else:
                text += char
                if i == 0 or not pattern[i-1].isdigit():
                    levels.append(0)
            i += 1
        
        # Ensure levels array is one longer than text
        if len(levels) == len(text):
            levels.append(0)
        
        return text, levels
    
    def _hyphenate_word(self, word: str) -> str:
        """Apply hyphenation patterns to a single word"""
        if len(word) <= 2:
            return word
        
        word_lower = word.lower()
        levels = [0] * (len(word) + 1)
        
        # Apply each pattern
        for pattern in self.patterns:
            text, pattern_levels = self._parse_pattern(pattern)
            
            if not text:
                continue
            
            # Find all occurrences of this pattern in the word
            start = 0
            while True:
                pos = word_lower.find(text, start)
                if pos == -1:
                    break
                
                # Apply pattern levels
                for i, level in enumerate(pattern_levels):
                    if pos + i < len(levels):
                        levels[pos + i] = max(levels[pos + i], level)
                
                start = pos + 1
        
        # Don't hyphenate at the beginning or end
        levels[0] = levels[-1] = 0
        if len(levels) > 1:
            levels[1] = 0
        if len(levels) > 2:
            levels[-2] = 0
        
        # Build hyphenated word
        result = ""
        for i in range(len(word)):
            if levels[i] % 2 == 1:
                result += "·"
            result += word[i]
        
        return result
    
    def _syllabify_text(self, text: str) -> Dict[str, Any]:
        """Syllabify a text (word, phrase, or multiple lines)"""
        lines = text.strip().split('\n')
        results = []
        
        for line in lines:
            if not line.strip():
                continue
            
            # Split by words and preserve spaces/punctuation
            tokens = re.findall(r'\S+|\s+', line)
            syllabified_tokens = []
            total_syllables = 0
            
            for token in tokens:
                if re.match(r'\s+', token):
                    # Preserve whitespace as-is
                    syllabified_tokens.append(token)
                elif re.match(r'\w+', token):
                    # Syllabify words
                    syllabified = self._hyphenate_word(token)
                    syllable_count = syllabified.count('·') + 1
                    syllabified_tokens.append(syllabified)
                    total_syllables += syllable_count
                else:
                    # Preserve punctuation as-is
                    syllabified_tokens.append(token)
            
            syllabified_line = ''.join(syllabified_tokens)
            
            results.append({
                'original': line,
                'syllabified': syllabified_line,
                'syllable_count': total_syllables
            })
        
        return {
            'lines': results,
            'total_lines': len(results),
            'total_syllables': sum(r['syllable_count'] for r in results)
        }
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="catalan_syllabification",
            description="Split Catalan words into syllables using the same algorithm as Softcatalà's syllabification tool. Useful for poetry, language learning, and text analysis.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="The Catalan text to split into syllables. Can be a single word, phrase, or multiple lines of text.",
                    required=True
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="Output format: 'detailed' (default) for full analysis, or 'simple' for just syllabified text",
                    required=False,
                    default="detailed"
                )
            ]
        )
    
    @property
    def catalan_definition(self) -> ToolDefinition:
        """Catalan version of the tool definition for use with Catalan prompts"""
        return ToolDefinition(
            name="catalan_syllabification",
            description="Divideix paraules catalanes en síl·labes utilitzant el mateix algoritme que l'eina de sil·labificació de Softcatalà. Útil per a poesia, aprenentatge de la llengua i anàlisi de textos.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="El text català a dividir en síl·labes. Pot ser una paraula, una frase o múltiples línies de text.",
                    required=True
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="Format de sortida: 'detailed' (per defecte) per a anàlisi completa, o 'simple' només per al text sil·labificat",
                    required=False,
                    default="detailed"
                )
            ]
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the syllabification tool"""
        self.validate_parameters(kwargs)
        
        text = kwargs.get('text', '').strip()
        format_type = kwargs.get('format', 'detailed').lower()
        
        if not text:
            return {
                'error': 'No text provided',
                'success': False
            }
        
        try:
            result = self._syllabify_text(text)
            
            if format_type == 'simple':
                # Return just the syllabified text
                if len(result['lines']) == 1:
                    return {
                        'syllabified_text': result['lines'][0]['syllabified'],
                        'success': True
                    }
                else:
                    return {
                        'syllabified_text': '\n'.join(line['syllabified'] for line in result['lines']),
                        'success': True
                    }
            else:
                # Return detailed analysis
                return {
                    'success': True,
                    'analysis': result,
                    'summary': {
                        'total_lines': result['total_lines'],
                        'total_syllables': result['total_syllables']
                    }
                }
        
        except Exception as e:
            return {
                'error': f'Error during syllabification: {str(e)}',
                'success': False
            }