#!/usr/bin/env python3
"""
Local testing script for Google Cloud Function.
This script helps test the Cloud Function locally before deployment.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Set Cloud Function environment flag for testing
os.environ['GOOGLE_CLOUD_FUNCTION'] = '1'

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import functions_framework
        import mangum
        import fastapi
        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install -r requirements-cloudfunction.txt")
        return False

def start_local_server():
    """Start the local Functions Framework server."""
    print("🚀 Starting local Functions Framework server...")
    print("📍 Server will be available at: http://localhost:8080")
    print("📋 API Documentation: http://localhost:8080/docs")
    print("❤️  Health Check: http://localhost:8080/health")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        # Start the Functions Framework development server
        result = subprocess.run([
            sys.executable, "-m", "functions_framework",
            "--target", "fiscal_code_api",
            "--port", "8080",
            "--debug"
        ])
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except FileNotFoundError:
        print("❌ functions-framework not found")
        print("💡 Install with: pip install functions-framework")
        return False

def test_endpoints():
    """Test the deployed function endpoints."""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Cloud Function endpoints...")
    print("-" * 50)
    
    tests = [
        {
            "name": "Health Check",
            "method": "GET",
            "url": f"{base_url}/health",
            "expected_key": "status"
        },
        {
            "name": "API Information",
            "method": "GET", 
            "url": f"{base_url}/api",
            "expected_key": "name"
        },
        {
            "name": "Fiscal Code Validation",
            "method": "POST",
            "url": f"{base_url}/fiscal-code/validate",
            "data": {"code": "CCCFBA85D03L219P"},
            "expected_key": "valid"
        },
        {
            "name": "VAT Number Validation",
            "method": "POST",
            "url": f"{base_url}/vat/validate", 
            "data": {"partita_iva": "01234567890"},
            "expected_key": "valid"
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            else:
                response = requests.post(
                    test["url"], 
                    json=test.get("data", {}),
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                if test["expected_key"] in data:
                    print(f"✅ {test['name']}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test['name']}: Missing key '{test['expected_key']}'")
                    print(f"   Response: {data}")
            else:
                print(f"❌ {test['name']}: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ {test['name']}: Connection error - {e}")
        except Exception as e:
            print(f"❌ {test['name']}: Unexpected error - {e}")
    
    print("-" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your function is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

def wait_for_server(base_url="http://localhost:8080", timeout=30):
    """Wait for the server to be ready."""
    print("⏳ Waiting for server to start...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"   Still waiting... ({i}s elapsed)")
    
    print("❌ Server did not start within timeout period")
    return False

def main():
    """Main testing function."""
    print("🔧 Google Cloud Function Local Testing")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found! Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Start local server (interactive)")
    print("2. Start server and run tests")
    print("3. Test running server (assumes server is already running)")
    print("4. Validate main.py syntax only")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        # Interactive server
        start_local_server()
        
    elif choice == "2":
        # Start server in background and test
        print("🚀 Starting server for testing...")
        
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, "-m", "functions_framework",
            "--target", "fiscal_code_api",
            "--port", "8080"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to be ready
            if wait_for_server():
                # Run tests
                test_endpoints()
            else:
                print("❌ Could not start server for testing")
        finally:
            # Clean up
            server_process.terminate()
            server_process.wait()
            print("🛑 Test server stopped")
            
    elif choice == "3":
        # Test existing server
        print("🧪 Testing existing server at http://localhost:8080")
        if wait_for_server(timeout=5):
            test_endpoints()
        else:
            print("❌ No server found at http://localhost:8080")
            print("💡 Start the server first with: python main.py")
            
    elif choice == "4":
        # Syntax validation only
        print("🔍 Validating main.py syntax...")
        try:
            import py_compile
            py_compile.compile("main.py", doraise=True)
            print("✅ main.py syntax is valid")
        except py_compile.PyCompileError as e:
            print(f"❌ Syntax error in main.py: {e}")
            sys.exit(1)
            
    else:
        print("❌ Invalid choice")
        sys.exit(1)

if __name__ == "__main__":
    main()