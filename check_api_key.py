"""
API Key Diagnostic Tool
=======================

This script helps diagnose API key configuration issues.
It checks for API keys in environment variables and .env files.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

def check_api_keys():
    """Check API key configuration."""
    print("=" * 80)
    print("API KEY DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("[OK] .env file found")
        print(f"  Location: {env_file.absolute()}")
    else:
        print("[WARNING] .env file NOT found")
        print("  Create a .env file in the project root with your API keys")
        print("  See ENV_TEMPLATE.txt for an example")
    print()
    
    # Check OpenAI API Key
    print("OpenAI API Key:")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        # Show first 7 and last 4 characters for security
        masked_key = f"{openai_key[:7]}...{openai_key[-4:]}" if len(openai_key) > 11 else "***"
        print(f"  [OK] Found: {masked_key}")
        print(f"  Length: {len(openai_key)} characters")
        
        # Check if it looks valid (OpenAI keys typically start with 'sk-')
        if openai_key.startswith("sk-"):
            print("  [OK] Format looks correct (starts with 'sk-')")
        else:
            print("  [WARNING] OpenAI keys typically start with 'sk-'")
    else:
        print("  [ERROR] NOT FOUND")
        print("  Set OPENAI_API_KEY in your .env file or environment variables")
    print()
    
    # Check other common API keys
    other_keys = {
        "ANTHROPIC_API_KEY": "Anthropic",
        "COHERE_API_KEY": "Cohere",
        "MISTRAL_API_KEY": "MistralAI",
    }
    
    print("Other API Keys:")
    for key_name, provider in other_keys.items():
        key_value = os.getenv(key_name)
        if key_value:
            masked_key = f"{key_value[:7]}...{key_value[-4:]}" if len(key_value) > 11 else "***"
            print(f"  [OK] {provider}: {masked_key}")
        else:
            print(f"  [-] {provider}: Not set")
    print()
    
    # Check Neo4j credentials
    print("Neo4j Configuration:")
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    
    print(f"  URI: {neo4j_uri}")
    print(f"  User: {neo4j_user}")
    if neo4j_password:
        print(f"  Password: {'*' * len(neo4j_password)} (set)")
    else:
        print("  Password: NOT SET")
    print()
    
    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if not openai_key:
        print("\n[WARNING] OPENAI_API_KEY is not set!")
        print("\nTo fix this:")
        print("1. Create a .env file in the project root (if it doesn't exist)")
        print("2. Add the following line:")
        print("   OPENAI_API_KEY=your_actual_api_key_here")
        print("3. Get your API key from: https://platform.openai.com/api-keys")
        print("4. Restart your terminal/IDE after creating/updating .env")
    else:
        print("\n[OK] OpenAI API key is configured")
        print("\nIf you're still getting 403 errors:")
        print("1. Verify your API key is correct at: https://platform.openai.com/api-keys")
        print("2. Check that your API key hasn't expired")
        print("3. Ensure you have sufficient credits/quota in your OpenAI account")
        print("4. Verify the key has the correct permissions")
        print("5. Try regenerating the API key if it's been compromised")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_api_keys()
