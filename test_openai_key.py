"""
Test OpenAI API Key
==================

This script tests if your OpenAI API key is valid and working.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def test_openai_key():
    """Test OpenAI API key."""
    print("=" * 80)
    print("TESTING OPENAI API KEY")
    print("=" * 80)
    print()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in environment")
        print("Please set it in your .env file")
        return False
    
    print(f"API Key found: {api_key[:7]}...{api_key[-4:]}")
    print()
    
    try:
        from openai import OpenAI
        
        print("Creating OpenAI client...")
        client = OpenAI(api_key=api_key)
        
        print("Making test API call...")
        print("(This will use a small amount of credits)")
        print()
        
        # Make a simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'API key test successful' and nothing else."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"[SUCCESS] API call successful!")
        print(f"Response: {result}")
        print()
        print("Your OpenAI API key is valid and working correctly.")
        return True
        
    except ImportError:
        print("[ERROR] OpenAI Python package not installed")
        print("Install it with: pip install openai")
        return False
        
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR] API call failed: {error_str}")
        print()
        
        # Check for specific error types
        if "401" in error_str or "authentication" in error_str.lower() or "invalid" in error_str.lower():
            print("This appears to be an authentication error.")
            print("Possible causes:")
            print("1. API key is incorrect or invalid")
            print("2. API key has been revoked or expired")
            print("3. API key doesn't have the required permissions")
            print()
            print("Solutions:")
            print("1. Verify your API key at: https://platform.openai.com/api-keys")
            print("2. Generate a new API key if needed")
            print("3. Update your .env file with the new key")
            print("4. Restart your terminal/IDE after updating")
            
        elif "403" in error_str or "forbidden" in error_str.lower():
            print("This is a 403 Forbidden error.")
            print("Possible causes:")
            print("1. API key doesn't have access to the requested model")
            print("2. Account doesn't have sufficient credits/quota")
            print("3. API key permissions are restricted")
            print("4. Organization/account restrictions")
            print()
            print("Solutions:")
            print("1. Check your account credits: https://platform.openai.com/account/billing")
            print("2. Verify model access: https://platform.openai.com/account/limits")
            print("3. Check API key permissions at: https://platform.openai.com/api-keys")
            print("4. Try using a different model (e.g., gpt-4o-mini)")
            
        elif "429" in error_str or "rate limit" in error_str.lower():
            print("This is a rate limit error.")
            print("Wait a few minutes and try again.")
            
        elif "insufficient_quota" in error_str.lower() or "quota" in error_str.lower():
            print("This is a quota/credits error.")
            print("Your account doesn't have sufficient credits.")
            print("Add credits at: https://platform.openai.com/account/billing")
            
        else:
            print("Check the error message above for details.")
            print("Common issues:")
            print("- Invalid API key")
            print("- Expired API key")
            print("- Insufficient account credits")
            print("- Network/connectivity issues")
        
        return False


if __name__ == "__main__":
    success = test_openai_key()
    print()
    print("=" * 80)
    if success:
        print("TEST PASSED - Your API key is working!")
    else:
        print("TEST FAILED - Please fix the issues above")
    print("=" * 80)
