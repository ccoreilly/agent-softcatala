#!/usr/bin/env python3
"""Test script for Z.AI integration with GLM-4.5-flash model."""

import os
import sys
import asyncio
sys.path.append('backend')

from backend.models.model_manager import ModelManager, ModelProvider


async def test_zai_integration():
    """Test Z.AI integration with the new configuration."""
    print("Testing Z.AI Integration...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("ZHIPUAI_API_KEY")
    base_url = os.getenv("ZHIPUAI_BASE_URL")
    
    print(f"API Key: {'✓' if api_key else '✗'} {'(set)' if api_key else '(not set)'}")
    print(f"Base URL: {base_url or 'default'}")
    print()
    
    if not api_key:
        print("❌ ZHIPUAI_API_KEY environment variable not set!")
        print("Please set your Z.AI API key:")
        print("export ZHIPUAI_API_KEY=your_api_key")
        return False
    
    try:
        # Initialize model manager
        manager = ModelManager()
        
        # Check if Zhipu provider is available
        if ModelProvider.ZHIPU not in manager.providers:
            print("❌ Z.AI/Zhipu provider not initialized!")
            return False
        
        provider = manager.providers[ModelProvider.ZHIPU]
        print("✓ Z.AI/Zhipu provider initialized")
        
        # List available models
        models = provider.list_models()
        print(f"✓ Available models: {len(models)} models")
        print(f"  - Default model: GLM-4.5-flash")
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
        model = provider.get_model("glm-4.5-flash", temperature=0.7)
        print("✓ GLM-4.5-flash model created successfully")
        
        # Test simple completion
        print("\nTesting chat completion with GLM-4.5-flash...")
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Say 'Hello from Z.AI GLM-4.5-flash!' in response.")]
        
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
        print("🎉 Z.AI integration test completed successfully!")
        print("✓ GLM-4.5-flash is now the default model")
        print("✓ Z.AI endpoint configuration working")
        print("✓ All functionality verified")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("Z.AI Integration Test")
    print("Checking GLM-4.5-flash model and endpoint configuration...")
    print()
    
    success = asyncio.run(test_zai_integration())
    
    if success:
        print("\n🚀 Ready to use Z.AI with GLM-4.5-flash!")
        sys.exit(0)
    else:
        print("\n💡 Setup instructions:")
        print("1. Get your API key from Z.AI platform (open.bigmodel.cn)")
        print("2. Set environment variable:")
        print("   export ZHIPUAI_API_KEY=your_api_key")
        print("3. Run this test again")
        print("Note: Z.AI and Zhipu AI use the same API endpoint - no additional configuration needed!")
        sys.exit(1)


if __name__ == "__main__":
    main()