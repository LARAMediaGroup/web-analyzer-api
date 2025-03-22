#!/usr/bin/env python3
"""
Dependency checker for Web Analyzer Service

This script verifies that all required dependencies are installed correctly.
"""

import importlib
import sys
import os
import subprocess

# List of required modules
REQUIRED_MODULES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "python-multipart",
    "python-docx",
    "nltk",
    "beautifulsoup4",
    "python-jose",
    "passlib",
    "python-dotenv",
    "aiofiles",
    "jinja2",
    "requests",
    "numpy"
]

# NLTK data requirements
NLTK_REQUIREMENTS = [
    "punkt",
    "stopwords",
    "averaged_perceptron_tagger",
    "maxent_ne_chunker",
    "words"
]

def check_python_version():
    """Check that Python version is compatible."""
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python 3.8+ required. Found: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version}")
    return True

def check_modules():
    """Check that all required Python modules are installed."""
    missing_modules = []
    
    for module_name in REQUIRED_MODULES:
        try:
            # Try to import the module
            importlib.import_module(module_name.replace('-', '_').split('>=')[0])
            print(f"✅ {module_name} is installed")
        except ImportError:
            missing_modules.append(module_name)
            print(f"❌ {module_name} is missing")
    
    return len(missing_modules) == 0

def check_nltk_data():
    """Check that required NLTK data is downloaded."""
    import nltk
    
    missing_data = []
    
    for data_name in NLTK_REQUIREMENTS:
        try:
            # Check if the data exists
            nltk.data.find(f"{data_name}")
            print(f"✅ NLTK data '{data_name}' is downloaded")
        except LookupError:
            missing_data.append(data_name)
            print(f"❌ NLTK data '{data_name}' is missing")
    
    return len(missing_data) == 0

def check_environment_variables():
    """Check essential environment variables."""
    env_vars = [
        "SECRET_KEY",
        "DEBUG",
        "MAX_WORKERS",
        "NLTK_DATA"
    ]
    
    missing_vars = []
    
    for var in env_vars:
        if var not in os.environ:
            print(f"❌ Environment variable {var} is not set")
            missing_vars.append(var)
        else:
            print(f"✅ Environment variable {var} is set")
    
    if missing_vars:
        print("\nℹ️ Missing environment variables can be set in .env file or in your environment.")
        print("ℹ️ See .env.example for required variables.")
    
    return len(missing_vars) == 0

def main():
    """Main function to check all dependencies."""
    print("=== Web Analyzer Service Dependency Check ===\n")
    
    python_ok = check_python_version()
    print("")
    
    modules_ok = check_modules()
    print("")
    
    nltk_ok = check_nltk_data()
    print("")
    
    env_ok = check_environment_variables()
    print("\n=== Summary ===")
    
    all_ok = python_ok and modules_ok and nltk_ok
    
    if all_ok:
        print("✅ All dependencies are correctly installed.")
        print("✅ The service should start without issues.")
    else:
        print("❌ Some dependencies are missing. Please fix the issues above.")
        print("❌ The service might not work correctly.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())