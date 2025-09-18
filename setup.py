#!/usr/bin/env python3
"""
RAGDocs Setup Script
Automated setup for the RAGDocs application
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Please upgrade your Python installation.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_directories():
    """Create necessary directories."""
    directories = [
        "app/data",
        "app/data/vector_store"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create a sample .env file if it doesn't exist."""
    env_content = """# RAGDocs Configuration
APP_NAME=RAGDocs
DEBUG=True

# OpenRouter Configuration
OPENROUTER_API_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=60

# Embedding Model Configuration
EMBEDDING_MODEL=text-embedding-ada-002

# LLM Model Configuration
DEFAULT_LLM_MODEL=openai/gpt-3.5-turbo

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVE_DOCS=4

# Vector Database Configuration
VECTOR_STORE_PATH=./app/data/vector_store

# Web Scraping Configuration
REQUEST_TIMEOUT=30
MAX_CONTENT_LENGTH=1000000
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
    else:
        print("ℹ️  .env file already exists, skipping creation")

def main():
    """Main setup function."""
    print("🚀 RAGDocs Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies. Please check your pip installation.")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating necessary directories...")
    create_directories()
    
    # Create .env file
    print("\n⚙️  Setting up configuration...")
    create_env_file()
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 RAGDocs setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Get your OpenRouter API key from: https://openrouter.ai/")
    print("2. Start the application:")
    print("   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    print("3. Open your browser to: http://127.0.0.1:8000")
    print("4. Configure your API key in the application")
    print("5. Add some documents and start querying!")
    print("\n📖 For more information, see README.md")

if __name__ == "__main__":
    main()