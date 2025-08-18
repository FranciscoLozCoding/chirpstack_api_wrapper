#!/usr/bin/env python3
"""
Script to run Chirpstack API Wrapper integration tests.

This script will run the integration tests against a running Chirpstack server.
Make sure the server is running on localhost:8081 before executing.
"""

import sys
import subprocess
import os

def main():
    """Run integration tests."""
    print("🚀 Starting Chirpstack API Wrapper Integration Tests")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("test/test_integration.py"):
        print("❌ Error: test_integration.py not found!")
        print("   Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ Error: pytest not installed!")
        print("   Install it with: pip install pytest")
        sys.exit(1)
    
    print("✅ pytest found")
    print("✅ Integration test file found")
    print()
    print("📋 Test Configuration:")
    print("   - Server: localhost:8081")
    print("   - Username: admin")
    print("   - Password: admin")
    print("   - All test records will be marked with 'test' tag")
    print()
    
    # Confirm with user
    response = input("⚠️  This will create test records on your Chirpstack server. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Tests cancelled by user")
        sys.exit(0)
    
    print()
    print("🔍 Running integration tests...")
    print()
    
    # Run the integration tests
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "test/test_integration.py",
            "-v",
            "--tb=short",
            "--cov=chirpstack_api_wrapper",
            "--cov-report=html:htmlcov-integration",
            "--cov-report=term-missing"
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print()
            print("✅ All integration tests passed!")
            print("📊 Coverage report generated in htmlcov-integration/")
        else:
            print()
            print("❌ Some integration tests failed!")
            print("   Check the output above for details.")
            sys.exit(result.returncode)
            
    except KeyboardInterrupt:
        print()
        print("❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

