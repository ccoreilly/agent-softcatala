#!/usr/bin/env python3
"""
Verification script to check if the test setup is working correctly.
This helps identify issues before running CI.
"""

import sys
import os
import subprocess
import tempfile
import venv

def create_temp_venv():
    """Create a temporary virtual environment for testing."""
    temp_dir = tempfile.mkdtemp()
    venv_path = os.path.join(temp_dir, 'test_venv')
    
    print(f"Creating temporary virtual environment at {venv_path}")
    venv.create(venv_path, with_pip=True)
    
    return venv_path

def run_command(cmd, cwd=None, env=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            env=env,
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Error: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 Verifying Backend Test Setup")
    print("=" * 40)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Check if required files exist
    required_files = [
        'requirements.txt',
        'requirements-dev.txt',
        'pytest.ini',
        'tests/test_api.py',
        'tests/test_integration.py',
        'tests/test_health.py',
        'tests/conftest.py'
    ]
    
    print("📁 Checking required files...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            return False
    
    # Check Python syntax of all test files
    print("\n🐍 Checking Python syntax...")
    test_files = [
        'tests/test_api.py',
        'tests/test_integration.py', 
        'tests/test_health.py',
        'tests/conftest.py'
    ]
    
    for test_file in test_files:
        if run_command(f'python3 -m py_compile {test_file}'):
            print(f"✅ {test_file} syntax OK")
        else:
            print(f"❌ {test_file} syntax ERROR")
            return False
    
    # Check main application files
    print("\n📦 Checking main application syntax...")
    main_files = ['main.py', 'langchain_agent.py', 'agent.py']
    for main_file in main_files:
        if os.path.exists(main_file):
            if run_command(f'python3 -m py_compile {main_file}'):
                print(f"✅ {main_file} syntax OK")
            else:
                print(f"❌ {main_file} syntax ERROR")
                return False
    
    # Check requirements files format
    print("\n📋 Checking requirements files...")
    for req_file in ['requirements.txt', 'requirements-dev.txt']:
        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()
                # Basic check for valid format
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '==' not in line and not line.startswith('-'):
                        print(f"⚠️  {req_file}:{i} - Potentially invalid format: {line}")
            print(f"✅ {req_file} format OK")
        except Exception as e:
            print(f"❌ Error reading {req_file}: {e}")
            return False
    
    print("\n🎯 Basic verification complete!")
    print("✅ All checks passed - setup looks good for CI")
    
    print("\n💡 To run tests manually:")
    print("   ./run_tests.sh")
    print("   or")
    print("   python3 -m pytest tests/ -v")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)