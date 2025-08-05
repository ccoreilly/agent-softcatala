#!/usr/bin/env python3
"""Test script for Z.AI integration with GLM-4.5-flash model."""

import os
import sys
import asyncio
sys.path.append('backend')

from backend.models.model_manager import ModelManager, ModelProvider


async def test_zai_integration():
    """Test provider integration."""
    print("Testing Provider Integration...")
    print("=" * 50)
    
    # Check environment variables for all providers
    zhipu_key = os.getenv("ZHIPUAI_API_KEY")
    zhipu_base_url = os.getenv("ZHIPUAI_BASE_URL")
    openai_key = os.getenv("OPENAI_KEY")
    ollama_url = os.getenv("OLLAMA_URL")
    
    print("Provider Configuration:")
    print(f"  Zhipu AI: {'✓' if zhipu_key else '✗'} {'(set)' if zhipu_key else '(not set)'}")
    print(f"  OpenAI: {'✓' if openai_key else '✗'} {'(set)' if openai_key else '(not set)'}")
    print(f"  Ollama: {'✓' if ollama_url else '✗'} {'(set)' if ollama_url else '(not set)'}")
    print()
    
    if not zhipu_key and not openai_key and not ollama_url:
        print("❌ No provider configuration found!")
        print("Please set at least one provider:")
        print("  - export ZHIPUAI_API_KEY=your_zhipu_key (for Zhipu AI)")
        print("  - export OPENAI_KEY=your_openai_key (for OpenAI)")
        print("  - export OLLAMA_URL=http://localhost:11434 (for Ollama)")
        return False
    
    try:
        # Initialize model manager
        manager = ModelManager()
        
        # Check if any provider is available
        available_providers = list(manager.providers.keys())
        if not available_providers:
            print("❌ No providers initialized!")
            return False
        
        print(f"✓ Available providers: {', '.join([p.value for p in available_providers])}")
        
        # Prefer OpenAI if available, then Zhipu
        if ModelProvider.OPENAI in manager.providers:
            provider = manager.providers[ModelProvider.OPENAI]
            print("✓ Using OpenAI provider")
            test_model = "gpt-4.1-mini"
            test_message = "Say 'Hello from OpenAI GPT-4.1-mini!' in response."
        elif ModelProvider.ZHIPU not in manager.providers:
            print("❌ Z.AI/Zhipu provider not initialized!")
            return False
        else:
            provider = manager.providers[ModelProvider.ZHIPU]
            print("✓ Using Z.AI/Zhipu provider")
            test_model = "glm-4.5-flash"
            test_message = "Say 'Hello from Z.AI GLM-4.5-flash!' in response."
        
        # List available models
        models = provider.list_models()
        print(f"✓ Available models: {len(models)} models")
        print(f"  - Default model: {test_model}")
        print(f"  - Available: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}")
        print()
        
        # Test health check
        print("Testing health check...")
        health = await provider.health_check()
        
        if health.get("status") == "healthy":
            print("✓ Health check passed")
            print(f"  - Provider: {health.get('provider', 'N/A')}")
            print(f"  - Endpoint: {health.get('endpoint', 'N/A')}")
            print(f"  - Default model: {health.get('default_model', 'N/A')}")
        else:
            print("❌ Health check failed")
            print(f"  - Error: {health.get('error', 'Unknown error')}")
            return False
        
        print()
        
        # Test model creation
        print("Testing model creation...")
        model = provider.get_model(test_model, temperature=0.7)
        print(f"✓ {test_model} model created successfully")
        
        # Test simple completion
        print(f"\nTesting chat completion with {test_model}...")
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content=test_message)]
        
        try:
            response = await model.agenerate([messages])
            if response and response.generations:
                content = response.generations[0][0].text
                print(f"✓ Response received: {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                print("❌ Empty response received")
                return False
        except Exception as e:
            print(f"❌ Chat completion failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Provider integration test completed successfully!")
        print(f"✓ {test_model} is working correctly")
        print("✓ Provider configuration working")
        print("✓ All functionality verified")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("Provider Integration Test")
    print("Checking available language model providers...")
    print()
    
    success = asyncio.run(test_zai_integration())
    
    if success:
        print("\n🚀 Ready to use the configured language model provider!")
        sys.exit(0)
    else:
        print("\n💡 Setup instructions:")
        print("Configure at least one provider:")
        print("1. For Z.AI/Zhipu: Get API key from open.bigmodel.cn")
        print("   export ZHIPUAI_API_KEY=your_api_key")
        print("2. For OpenAI: Get API key from platform.openai.com")
        print("   export OPENAI_KEY=your_api_key")
        print("3. For Ollama: Install locally and set URL")
        print("   export OLLAMA_URL=http://localhost:11434")
        print("4. Run this test again")
        sys.exit(1)


if __name__ == "__main__":
    main()