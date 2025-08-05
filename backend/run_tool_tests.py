#!/usr/bin/env python3
"""
Script to run tool execution tests locally.
Usage: python run_tool_tests.py [--with-api] [--with-zhipu]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🧪 {description}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ PASSED")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Run tool execution tests")
    parser.add_argument("--with-api", action="store_true", help="Run tests that make real API calls")
    parser.add_argument("--with-zhipu", action="store_true", help="Run Zhipu-specific tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🚀 Running tool execution tests")
    print(f"📁 Working directory: {os.getcwd()}")
    
    verbose_flag = "-v" if args.verbose else ""
    results = []
    
    # Core tests (no API calls required)
    core_tests = [
        ("Tool Schema Generation", 
         f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_tool_schema_generation {verbose_flag}"),
        ("Agent Initialization", 
         f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_agent_initialization_with_tools {verbose_flag}"),
        ("Tool Parameter Validation", 
         f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_tool_parameter_validation {verbose_flag}"),
        ("Multiple Tool Types", 
         f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_multiple_tool_types {verbose_flag}"),
        ("Agent Health Check", 
         f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_agent_health_check {verbose_flag}"),
    ]
    
    print("\n📋 Running core tests (no API calls required)...")
    for description, cmd in core_tests:
        success = run_command(cmd, description)
        results.append((description, success))
    
    # API tests (require internet)
    if args.with_api:
        api_tests = [
            ("Direct Tool Execution (API)", 
             f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_direct_tool_execution {verbose_flag}"),
            ("LangChain Wrapper Execution (API)", 
             f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_langchain_wrapper_execution {verbose_flag}"),
        ]
        
        print("\n📋 Running API tests...")
        for description, cmd in api_tests:
            success = run_command(cmd, description)
            results.append((description, success))
    
    # Zhipu tests (require API key)
    if args.with_zhipu:
        if not os.getenv("ZHIPUAI_API_KEY"):
            print("\n⚠️  ZHIPUAI_API_KEY not set, skipping Zhipu tests")
        else:
            zhipu_tests = [
                ("Simple Zhipu Response", 
                 f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_simple_zhipu_response {verbose_flag}"),
                ("Agent Streaming with Zhipu", 
                 f"python3 -m pytest tests/test_tool_execution_integration.py::TestToolExecutionIntegration::test_agent_streaming_with_zhipu {verbose_flag}"),
            ]
            
            print("\n📋 Running Zhipu tests...")
            for description, cmd in zhipu_tests:
                success = run_command(cmd, description)
                results.append((description, success))
    
    # Comprehensive test script
    print("\n📋 Running comprehensive test script...")
    success = run_command("python3 test_tool_execution.py", "Comprehensive Tool Execution Test")
    results.append(("Comprehensive Test", success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)