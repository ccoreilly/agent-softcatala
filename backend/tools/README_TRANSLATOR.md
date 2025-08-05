# Eina de Traducció Catalana (Catalan Translation Tool)

## Descripció

Aquest és un nou tool per a l'agent que permet traduir text entre el català i altres llengües utilitzant serveis de traducció compatibles amb Softcatalà. L'eina està dissenyada per utilitzar APIs compatibles amb el format Apertium, seguint els estàndards utilitzats per Softcatalà.

## Característiques

- **Suport multilingüe**: Traducció entre català i castellà, anglès, francès, italià, portuguès, alemany, basc, gallec i occità
- **Interfície bilingüe**: Instruccions disponibles en català i anglès
- **Format flexible**: Suport per text pla i HTML
- **Gestió d'errors robusta**: Missatges d'error en català i anglès
- **Fàcil configuració**: Preparat per integrar-se amb l'API real de Softcatalà quan estigui disponible

## Parells de llengües suportats

- `ca|es` - Català ➝ Castellà/Espanyol
- `es|ca` - Castellà/Espanyol ➝ Català
- `ca|en` - Català ➝ Anglès
- `en|ca` - Anglès ➝ Català
- `ca|fr` - Català ➝ Francès
- `fr|ca` - Francès ➝ Català
- `ca|it` - Català ➝ Italià
- `it|ca` - Italià ➝ Català
- `ca|pt` - Català ➝ Portuguès
- `pt|ca` - Portuguès ➝ Català
- `ca|de` - Català ➝ Alemany
- `de|ca` - Alemany ➝ Català
- `ca|eu` - Català ➝ Basc
- `eu|ca` - Basc ➝ Català
- `ca|gl` - Català ➝ Gallec
- `gl|ca` - Gallec ➝ Català
- `ca|oc` - Català ➝ Occità
- `oc|ca` - Occità ➝ Català

## Ús de l'eina

### Paràmetres

1. **text** (obligatori): El text a traduir
2. **langpair** (obligatori): Parell de llengües en format 'origen|destí' (p.ex., 'en|ca')
3. **format** (opcional): Format de sortida ('txt' per defecte, 'html' disponible)

### Exemple d'ús

```python
from tools.catalan_translator import CatalanTranslatorTool

tool = CatalanTranslatorTool()
result = await tool.execute(
    text="Hello world",
    langpair="en|ca"
)
print(result['translated_text'])  # Output: "hola món"
```

## Configuració per a l'API real de Softcatalà

Actualment, l'eina utilitza un servei de demostració. Per activar la traducció real:

### 1. Actualitzar l'endpoint de l'API

Al fitxer `catalan_translator.py`, modifiqueu:

```python
# Canvieu aquesta línia:
self.base_url = "https://apertium.ua.es/tradtexto.php"

# Per aquesta (quan estigui disponible):
self.base_url = "https://www.softcatala.org/api/translate"
# o
self.base_url = "https://api.softcatala.org/translate"
```

### 2. Activar les crides reals a l'API

Dins del mètode `_translate()`, reemplaceu el codi de demostració per:

```python
# Preparar paràmetres per la crida a l'API
params = {
    'langpair': langpair,
    'q': text
}

if format_type != 'txt':
    params['format'] = format_type

# Fer la petició a l'API
response = await self.client.get(self.base_url, params=params)

if response.status_code == 200:
    data = response.json()
    if 'responseData' in data and 'translatedText' in data['responseData']:
        translated_text = data['responseData']['translatedText']
        return {
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'language_pair': langpair,
            'language_pair_description': self.language_pairs[langpair],
            'service': 'Softcatalà Translation Service',
            'format': format_type
        }
```

## Format de l'API (Compatible amb Apertium)

L'eina està dissenyada per funcionar amb APIs que segueixin el format estàndard d'Apertium:

### Petició
```
GET /translate?langpair=en|ca&q=Hello+world&format=txt
```

### Resposta esperada
```json
{
    "responseData": {
        "translatedText": "Hola món"
    },
    "responseStatus": 200,
    "responseDetails": null
}
```

## Integració amb l'agent

L'eina s'ha integrat automàticament a l'agent principal:

1. **Importat** a `main.py`
2. **Inicialitzat** com `catalan_translator_tool`
3. **Afegit** a la llista d'eines de l'agent
4. **Activat** per defecte

## Funcionalitats avançades

### Gestió de llengües
```python
# Obtenir llista de parells suportats
langs = await tool.get_supported_languages()
print(langs['supported_pairs'])
```

### Validació de paràmetres
L'eina valida automàticament:
- Text no buit
- Parell de llengües vàlid
- Format de sortida correcte

### Gestió d'errors
Retorna missatges d'error en català i anglès:
```python
{
    'success': False,
    'error': 'Parell de llengües no suportat: xx|yy',
    'error_en': 'Unsupported language pair: xx|yy'
}
```

## Desenvolupament futur

Quan l'API pública de Softcatalà estigui disponible, l'eina es pot actualitzar fàcilment per:

1. Suportar més parells de llengües
2. Utilitzar el traductor neuronal de Softcatalà
3. Afegir opcions de configuració avançades
4. Implementar cache de traduccions
5. Suportar traducció de fitxers

## Notes tècniques

- **HTTP Client**: Utilitza `httpx` per peticions asíncrones
- **Timeout**: 30 segons per petició
- **Headers**: Inclou User-Agent identificatiu
- **Compatibilitat**: Dissenyat per APIs compatibles amb Apertium
- **Fallback**: Inclou traduccions de demostració per proves