#!/usr/bin/env python3
"""
Integration tests for the Catalan Translation API endpoints
Tests both Apertium and Neuronal APIs with real API calls
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from tools.catalan_translator import CatalanTranslatorTool

async def test_translation_apis():
    """Test both translation APIs with various language pairs"""
    
    tool = CatalanTranslatorTool()
    
    # Define test cases with expected API usage
    test_cases = [
        # Neuronal API tests (languages that should use neuronal)
        {
            "text": "Hello world",
            "langpair": "en|cat",
            "expected_api": "neuronal",
            "description": "English to Catalan (neuronal)"
        },
        {
            "text": "Good morning",
            "langpair": "en|cat", 
            "expected_api": "neuronal",
            "description": "English to Catalan (neuronal)"
        },
        {
            "text": "Hola món",
            "langpair": "cat|en",
            "expected_api": "neuronal", 
            "description": "Catalan to English (neuronal)"
        },
        {
            "text": "Bonjour le monde",
            "langpair": "fr|cat",
            "expected_api": "neuronal",
            "description": "French to Catalan (neuronal)"
        },
        {
            "text": "Hola món", 
            "langpair": "cat|fr",
            "expected_api": "neuronal",
            "description": "Catalan to French (neuronal)"
        },
        {
            "text": "Guten Tag",
            "langpair": "deu|cat",
            "expected_api": "neuronal",
            "description": "German to Catalan (neuronal only)"
        },
        {
            "text": "Ciao mondo", 
            "langpair": "ita|cat",
            "expected_api": "neuronal",
            "description": "Italian to Catalan (neuronal only)"
        },
        
        # Apertium API tests (languages that should use apertium)
        {
            "text": "Hola món",
            "langpair": "cat|spa", 
            "expected_api": "apertium",
            "description": "Catalan to Spanish (apertium)"
        },
        {
            "text": "Hola mundo",
            "langpair": "spa|cat",
            "expected_api": "apertium", 
            "description": "Spanish to Catalan (apertium)"
        },
        {
            "text": "Bon dia",
            "langpair": "cat|oc_aran",
            "expected_api": "apertium",
            "description": "Catalan to Aranese (apertium)"
        }
    ]
    
    print("=== Catalan Translation API Integration Tests ===\n")
    
    # Track results
    successful_tests = 0
    total_tests = len(test_cases)
    neuronal_tests = 0
    apertium_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{total_tests}: {test_case['description']}")
        print(f"  Text: {test_case['text']}")
        print(f"  Language pair: {test_case['langpair']}")
        print(f"  Expected API: {test_case['expected_api']}")
        
        try:
            # Verify API selection logic
            should_use_neuronal = tool._should_use_neuronal(test_case['langpair'])
            actual_api = "neuronal" if should_use_neuronal else "apertium"
            
            if actual_api != test_case['expected_api']:
                print(f"  ❌ API selection mismatch: expected {test_case['expected_api']}, got {actual_api}")
                continue
            
            # Perform translation
            result = await tool.execute(
                text=test_case['text'],
                langpair=test_case['langpair']
            )
            
            if result.get('success'):
                print(f"  ✅ SUCCESS - Translated: '{result['translated_text']}'")
                print(f"  Service: {result['service']}")
                successful_tests += 1
                
                if test_case['expected_api'] == 'neuronal':
                    neuronal_tests += 1
                else:
                    apertium_tests += 1
                    
            else:
                print(f"  ❌ FAILED - Error: {result.get('error', 'Unknown error')}")
                if 'error_en' in result:
                    print(f"  Error (EN): {result['error_en']}")
                if 'details' in result:
                    print(f"  Details: {result['details']}")
            
        except Exception as e:
            print(f"  ❌ EXCEPTION - {str(e)}")
        
        print()
    
    # Summary
    print("=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Neuronal API tests: {neuronal_tests}")
    print(f"Apertium API tests: {apertium_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

async def test_language_pair_coverage():
    """Test that all supported language pairs work"""
    tool = CatalanTranslatorTool()
    
    print("\n=== Language Pair Coverage Test ===")
    
    # Test a sample from each category
    sample_pairs = [
        # Neuronal only languages
        ("deu", "cat", "Hallo"),  # German
        ("ita", "cat", "Ciao"),   # Italian  
        ("nld", "cat", "Hallo"),  # Dutch
        ("jpn", "cat", "こんにちは"), # Japanese
        ("glg", "cat", "Ola"),    # Galician
        ("eus", "cat", "Kaixo"),  # Basque
        
        # Languages with both translators (prefer neuronal)
        ("en", "cat", "Hello"),   # English
        ("fr", "cat", "Bonjour"), # French
        ("pt", "cat", "Olá"),     # Portuguese
        
        # Apertium languages
        ("spa", "cat", "Hola"),   # Spanish
        ("oc_aran", "cat", "Ola"), # Aranese
        ("arg", "cat", "Ola"),    # Aragonese
        ("ron", "cat", "Salut"),  # Romanian
    ]
    
    successful_pairs = 0
    total_pairs = len(sample_pairs)
    
    for source_lang, target_lang, test_text in sample_pairs:
        langpair = f"{source_lang}|{target_lang}"
        
        if langpair not in tool.language_pairs:
            print(f"  ⚠️  Language pair {langpair} not in supported pairs")
            continue
            
        print(f"Testing {langpair}: '{test_text}'")
        
        try:
            result = await tool.execute(text=test_text, langpair=langpair)
            
            if result.get('success'):
                print(f"  ✅ '{result['translated_text']}' via {result['service']}")
                successful_pairs += 1
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    print(f"\nLanguage pair tests: {successful_pairs}/{total_pairs} successful")
    return successful_pairs == total_pairs

if __name__ == "__main__":
    async def main():
        print("Running Translation API Integration Tests...\n")
        
        # Test main APIs
        api_tests_passed = await test_translation_apis()
        
        # Test language pair coverage
        coverage_tests_passed = await test_language_pair_coverage()
        
        print("\n=== Final Results ===")
        if api_tests_passed and coverage_tests_passed:
            print("🎉 All integration tests passed!")
            sys.exit(0)
        else:
            print("❌ Some integration tests failed!")
            sys.exit(1)
    
    asyncio.run(main())