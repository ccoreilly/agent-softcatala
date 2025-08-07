#!/usr/bin/env python3
"""
Simple test script for the updated Catalan Translator Tool
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from tools.catalan_translator import CatalanTranslatorTool

async def test_translator():
    """Test the translator tool with various language pairs"""
    
    tool = CatalanTranslatorTool()
    
    # Test cases: (text, langpair, expected_api)
    test_cases = [
        ("Hello world", "en|cat", "neuronal"),  # English to Catalan - should use neuronal
        ("Hola món", "cat|spa", "apertium"),   # Catalan to Spanish - should use apertium
        ("Buenos días", "spa|cat_valencia", "apertium"),  # Spanish to Valencian - should use apertium
        ("Bon dia", "cat|fr", "neuronal"),     # Catalan to French - should use neuronal 
        ("Guten Tag", "deu|cat", "neuronal"),  # German to Catalan - should use neuronal (only available)
    ]
    
    print("=== Catalan Translator Tool Test ===\n")
    
    # Test language pair generation
    print("Generated language pairs:")
    for langpair, description in list(tool.language_pairs.items())[:10]:  # Show first 10
        print(f"  {langpair}: {description}")
    print(f"  ... and {len(tool.language_pairs) - 10} more pairs\n")
    
    # Test API selection logic
    print("Testing API selection logic:")
    for text, langpair, expected_api in test_cases:
        should_use_neuronal = tool._should_use_neuronal(langpair)
        actual_api = "neuronal" if should_use_neuronal else "apertium"
        status = "✓" if actual_api == expected_api else "✗"
        print(f"  {status} {langpair}: Expected {expected_api}, got {actual_api}")
    
    print(f"\nTotal supported language pairs: {len(tool.language_pairs)}")
    
    # Test tool definition
    definition = tool.definition
    print(f"\nTool definition:")
    print(f"  Name: {definition.name}")
    print(f"  Description: {definition.description[:100]}...")
    print(f"  Parameters: {len(definition.parameters)}")
    
    # Test parameter validation
    print(f"\nTesting parameter validation:")
    try:
        # This should fail validation
        result = await tool.execute(text="", langpair="invalid|pair")
        if not result['success']:
            print("  ✓ Empty text validation works")
        else:
            print("  ✗ Empty text validation failed")
    except Exception as e:
        print(f"  ✗ Validation error: {e}")
    
    try:
        # This should fail validation
        result = await tool.execute(text="Hello", langpair="invalid|pair")
        if not result['success']:
            print("  ✓ Invalid language pair validation works")
        else:
            print("  ✗ Invalid language pair validation failed")
    except Exception as e:
        print(f"  ✗ Validation error: {e}")
    
    print("\n=== Test completed ===")
    print("Note: This test only validates the tool logic, not actual API calls.")
    print("To test real API calls, use the tool with valid text and language pairs.")

if __name__ == "__main__":
    asyncio.run(test_translator())