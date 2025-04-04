#!/usr/bin/env python3
"""
Simple test script to check if the new Suno API key is loaded correctly.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get and check Suno API key
suno_key = os.getenv("SUNO_API_KEY")
print(f"Suno API Key: {suno_key[:5]}...{suno_key[-5:] if suno_key else 'Not set'}")

# Check if it matches the new key
expected_key = "6a3b6f312e0df45ac694e6b9232a3c20"
if suno_key == expected_key:
    print("✅ API key is correctly set to the new value!")
else:
    print("❌ API key does not match the expected value.")
    print("Make sure your .env file contains SUNO_API_KEY=6a3b6f312e0df45ac694e6b9232a3c20")