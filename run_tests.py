#!/usr/bin/env python3
"""
Simple test runner for Best Friend AI Companion.
This script can run basic tests even when heavy dependencies are missing.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_basic_tests():
    """Run basic tests that don't require heavy dependencies."""
    print("🧪 Running basic tests...")
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Try to run minimal tests
    try:
        import pytest
        print("✅ Pytest available")
        
        # Run minimal tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_minimal.py", "-v"
        ], capture_output=True, text=True)
        
        print("📋 Test Results:")
        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except ImportError as e:
        print(f"❌ Pytest not available: {e}")
        return False

def check_dependencies():
    """Check what dependencies are available."""
    print("🔍 Checking dependencies...")
    
    dependencies = [
        'flask', 'flask_sqlalchemy', 'flask_login', 'flask_limiter',
        'flask_wtf', 'flask_migrate', 'psycopg2', 'redis', 'pgvector',
        'faster_whisper', 'cryptography', 'bcrypt'
    ]
    
    available = []
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            available.append(dep)
        except ImportError:
            missing.append(dep)
    
    print(f"✅ Available: {', '.join(available)}")
    print(f"❌ Missing: {', '.join(missing)}")
    
    return len(missing) == 0

def main():
    """Main test runner."""
    print("🚀 Best Friend AI Companion - Test Runner")
    print("=" * 50)
    
    # Check dependencies
    all_deps_available = check_dependencies()
    
    print("\n" + "=" * 50)
    
    # Run basic tests
    basic_tests_passed = run_basic_tests()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   Dependencies: {'✅ All Available' if all_deps_available else '⚠️  Some Missing'}")
    print(f"   Basic Tests: {'✅ Passed' if basic_tests_passed else '❌ Failed'}")
    
    if all_deps_available:
        print("\n🎯 Full test suite should be available!")
        print("   Run: pytest tests/ --cov=app --cov-report=xml")
    else:
        print("\n⚠️  Some dependencies are missing.")
        print("   Install with: pip install -r requirements.txt")
        print("   Or run in Docker environment where all deps are available.")
    
    return 0 if basic_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
