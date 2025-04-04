#!/usr/bin/env python3
"""
Comprehensive Debugging Script for AI Music Video Generator
"""
import os
import sys
import json
import traceback
from dotenv import load_dotenv

# Import required libraries
try:
    import requests
    from anthropic import Anthropic
    from openai import OpenAI
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install dependencies with: pip install requests anthropic openai python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

def check_environment():
    """Check environment setup and configuration"""
    print("=== Environment Configuration ===")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")
    
    # Check required environment variables
    required_vars = [
        "SUNO_API_KEY", 
        "ANTHROPIC_API_KEY", 
        "OPENAI_API_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        print(f"{var}: {'✓ Set' if value else '✗ Not Set'}")
        if not value:
            print(f"  → Please set {var} in your .env file")

def test_suno_api():
    """Comprehensive test of Suno API"""
    print("\n=== Suno API Connectivity Test ===")
    api_key = os.getenv("SUNO_API_KEY")
    
    if not api_key:
        print("Suno API Key is not set!")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test generation endpoint
    generation_payload = {
        "prompt": "API Connection Test Song",
        "style": "test",
        "title": "Test Song",
        "customMode": True,
        "instrumental": True,
        "model": "V3_5"
    }
    
    try:
        # First, try the main generation endpoint
        response = requests.post(
            "https://apibox.erweima.ai/api/v1/generate", 
            headers=headers, 
            json=generation_payload,
            timeout=30
        )
        
        print("Generation Request Status Code:", response.status_code)
        
        # Parse and print response
        try:
            response_json = response.json()
            print("Generation Response:")
            print(json.dumps(response_json, indent=2))
        except ValueError:
            print("Could not parse JSON response")
            print("Raw Response:", response.text)
        
        return response.status_code == 200
    
    except requests.exceptions.RequestException as e:
        print("Suno API Connection Error:")
        print(traceback.format_exc())
        return False

def test_anthropic_api():
    """Test Anthropic Claude API"""
    print("\n=== Anthropic Claude API Test ===")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Anthropic API Key is not set!")
        return False
    
    try:
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Write a very short poem about testing APIs."}
            ]
        )
        
        print("Claude Response:")
        print(response.content[0].text)
        return True
    
    except Exception as e:
        print("Anthropic API Error:")
        print(traceback.format_exc())
        return False

def test_openai_api():
    """Test OpenAI DALL-E Image Generation"""
    print("\n=== OpenAI DALL-E API Test ===")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("OpenAI API Key is not set!")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.images.generate(
            model="dall-e-3",
            prompt="A simple test image of a sunset",
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        print("OpenAI Image Generation URL:", image_url)
        return True
    
    except Exception as e:
        print("OpenAI API Error:")
        print(traceback.format_exc())
        return False

def main():
    """Run comprehensive API and system checks"""
    print("=== AI Music Video Generator - System Diagnostic ===")
    
    # Check environment setup
    check_environment()
    
    # Test individual APIs
    tests = [
        ("Suno API", test_suno_api),
        ("Anthropic Claude API", test_anthropic_api),
        ("OpenAI DALL-E API", test_openai_api)
    ]
    
    # Run tests and track results
    results = {}
    for name, test_func in tests:
        print(f"\nRunning {name} Test...")
        results[name] = test_func()
    
    # Summarize results
    print("\n=== Test Summary ===")
    for name, result in results.items():
        print(f"{name}: {'✓ Passed' if result else '✗ Failed'}")
    
    # Final recommendation
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print("\n⚠️ Some API tests failed. Please check the following:")
        for name in failed_tests:
            print(f"- Verify your {name} credentials")
            print(f"- Ensure you have a valid subscription")
            print(f"- Check network connectivity")
    else:
        print("\n✅ All API tests passed successfully!")

if __name__ == "__main__":
    main()