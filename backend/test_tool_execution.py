#!/usr/bin/env python3
"""
Comprehensive test script to debug LangChain agent tool execution issues.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append('/workspace/backend')

from langchain_agent import LangChainAgent
from tools.catalan_synonyms import CatalanSynonymsTool
from tools.catalan_spell_checker import CatalanSpellCheckerTool

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/workspace/backend/tool_execution_debug.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_tool_direct_execution():
    """Test direct tool execution without agent."""
    logger.info("=" * 60)
    logger.info("TESTING DIRECT TOOL EXECUTION")
    logger.info("=" * 60)
    
    # Test Catalan synonyms tool
    synonyms_tool = CatalanSynonymsTool()
    logger.info(f"Tool definition: {synonyms_tool.definition}")
    
    try:
        result = await synonyms_tool.execute(action="search", word="hola")
        logger.info(f"Direct tool execution result: {result}")
        return True
    except Exception as e:
        logger.error(f"Direct tool execution failed: {e}")
        logger.exception("Full traceback:")
        return False


async def test_langchain_wrapper():
    """Test LangChain tool wrapper."""
    logger.info("=" * 60) 
    logger.info("TESTING LANGCHAIN TOOL WRAPPER")
    logger.info("=" * 60)
    
    from tools.langchain_tools import LangChainToolWrapper
    
    # Create and test wrapper
    synonyms_tool = CatalanSynonymsTool()
    wrapped_tool = LangChainToolWrapper(synonyms_tool)
    
    logger.info(f"Wrapped tool name: {wrapped_tool.name}")
    logger.info(f"Wrapped tool description: {wrapped_tool.description}")
    logger.info(f"Wrapped tool schema: {wrapped_tool.args_schema}")
    
    try:
        result = await wrapped_tool._arun(action="search", word="hola")
        logger.info(f"Wrapped tool execution result: {result}")
        return True
    except Exception as e:
        logger.error(f"Wrapped tool execution failed: {e}")
        logger.exception("Full traceback:")
        return False


async def test_agent_with_tools():
    """Test agent initialization and tool availability."""
    logger.info("=" * 60)
    logger.info("TESTING AGENT WITH TOOLS")
    logger.info("=" * 60)
    
    # Create tools
    synonyms_tool = CatalanSynonymsTool()
    spell_checker_tool = CatalanSpellCheckerTool()
    
    try:
        # Initialize agent with tools
        agent = LangChainAgent(
            tools=[synonyms_tool, spell_checker_tool], 
            agent_type="softcatala_english"
        )
        
        logger.info(f"Agent initialized successfully")
        logger.info(f"Agent executor type: {type(agent.agent_executor)}")
        logger.info(f"Number of tools: {len(agent.tools)}")
        
        # Check health
        health = await agent.check_health()
        logger.info(f"Agent health: {health}")
        
        return True
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}")
        logger.exception("Full traceback:")
        return False


async def test_agent_streaming():
    """Test agent streaming with tool-triggering message."""
    logger.info("=" * 60)
    logger.info("TESTING AGENT STREAMING WITH TOOL USAGE")
    logger.info("=" * 60)
    
    # Create tools
    synonyms_tool = CatalanSynonymsTool()
    spell_checker_tool = CatalanSpellCheckerTool()
    
    try:
        # Initialize agent
        agent = LangChainAgent(
            tools=[synonyms_tool, spell_checker_tool], 
            agent_type="softcatala_english"
        )
        
        # Test message that should trigger tool usage
        test_messages = [
            {
                "role": "user",
                "content": "Necessito sinònims per a la paraula 'casa'. Pots ajudar-me?"
            }
        ]
        
        logger.info("Starting agent streaming test...")
        
        chunks_received = []
        tool_calls_found = []
        tool_results_found = []
        
        async for chunk in agent.chat_stream(test_messages, "test_session"):
            chunks_received.append(chunk)
            logger.info(f"Received chunk: {chunk}")
            
            if chunk.get("type") == "tool_call":
                tool_calls_found.append(chunk)
                logger.info(f"🔧 TOOL CALL DETECTED: {chunk}")
            elif chunk.get("type") == "tool_result":
                tool_results_found.append(chunk)
                logger.info(f"🔧 TOOL RESULT DETECTED: {chunk}")
        
        logger.info(f"Total chunks received: {len(chunks_received)}")
        logger.info(f"Tool calls found: {len(tool_calls_found)}")
        logger.info(f"Tool results found: {len(tool_results_found)}")
        
        if tool_calls_found:
            logger.info("✅ Tool calls were detected!")
            for tool_call in tool_calls_found:
                logger.info(f"  - Tool: {tool_call.get('tool')}, Input: {tool_call.get('input')}")
        else:
            logger.warning("❌ No tool calls detected!")
            
        if tool_results_found:
            logger.info("✅ Tool results were found!")
            for tool_result in tool_results_found:
                logger.info(f"  - Tool: {tool_result.get('tool')}, Result: {tool_result.get('result')}")
        else:
            logger.warning("❌ No tool results found!")
        
        return len(tool_calls_found) > 0 or len(tool_results_found) > 0
        
    except Exception as e:
        logger.error(f"Agent streaming test failed: {e}")
        logger.exception("Full traceback:")
        return False


async def test_model_tool_compatibility():
    """Test if the current model supports tool calling."""
    logger.info("=" * 60)
    logger.info("TESTING MODEL TOOL CALLING COMPATIBILITY")
    logger.info("=" * 60)
    
    try:
        from models.model_manager import ModelManager
        
        model_manager = ModelManager()
        default_model = model_manager.get_default_model()
        
        logger.info(f"Default model: {default_model}")
        logger.info(f"Model type: {type(default_model)}")
        logger.info(f"Has bind_tools method: {hasattr(default_model, 'bind_tools')}")
        logger.info(f"Has with_structured_output method: {hasattr(default_model, 'with_structured_output')}")
        
        # Check available models
        available_models = model_manager.list_available_models()
        logger.info(f"Available models: {available_models}")
        
        return True
    except Exception as e:
        logger.error(f"Model compatibility test failed: {e}")
        logger.exception("Full traceback:")
        return False


async def main():
    """Run all tests."""
    logger.info("🚀 Starting comprehensive tool execution debug tests")
    logger.info(f"🚀 Test started at: {datetime.now().isoformat()}")
    
    # Set environment variables if not present
    if not os.getenv("OLLAMA_URL"):
        os.environ["OLLAMA_URL"] = "http://localhost:11434"
        logger.info("Set default OLLAMA_URL")
    
    test_results = {}
    
    # Run tests
    tests = [
        ("Direct Tool Execution", test_tool_direct_execution),
        ("LangChain Tool Wrapper", test_langchain_wrapper),
        ("Agent with Tools", test_agent_with_tools),
        ("Model Tool Compatibility", test_model_tool_compatibility),
        ("Agent Streaming", test_agent_streaming),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"🧪 Test {test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"🧪 Test {test_name}: ❌ FAILED with exception: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Tool execution should be working.")
    else:
        logger.warning("⚠️  Some tests failed. There are issues with tool execution.")
    
    logger.info(f"🚀 Test completed at: {datetime.now().isoformat()}")
    logger.info("🚀 Detailed logs saved to tool_execution_debug.log")


if __name__ == "__main__":
    asyncio.run(main())