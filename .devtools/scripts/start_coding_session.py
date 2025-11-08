#!/usr/bin/env python3
"""
Start a new coding session with OpenRouter integration.
This script:
1. Verifies the OpenRouter setup
2. Tests all available keys
3. Sets up the development environment
4. Provides a quick test of the integration
"""
from __future__ import annotations

import os
import sys
import time
from typing import List, Dict

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ai.openrouter_adapter import generate
from ai.openrouter_key_manager import get_manager


def test_keys() -> None:
    """Test all available API keys and report their status."""
    print("\n=== Testing OpenRouter Keys ===")
    km = get_manager()
    
    if not km.keys:
        print("❌ No API keys found!")
        print("Please create ai/openrouter_keys.json with your API keys")
        sys.exit(1)
    
    print(f"📝 Found {len(km.keys)} API keys")
    
    # Simple test message
    messages = [{"role": "user", "content": "Say hi!"}]
    
    working_keys = 0
    for i, key in enumerate(km.keys, 1):
        print(f"\nTesting key {i}/{len(km.keys)}: {key[:10]}...")
        km.state["current_index"] = km.keys.index(key)  # Force use this key
        
        try:
            resp = generate(messages, max_tokens=20)
            if resp.get("choices") and resp["choices"][0].get("message"):
                print(f"✅ Key {i} works! Response: {resp['choices'][0]['message']['content']}")
                working_keys += 1
            else:
                print(f"⚠️  Key {i} returned unexpected response format")
        except Exception as e:
            print(f"❌ Key {i} failed: {e}")
    
    print(f"\n=== Key Test Summary ===")
    print(f"Total keys: {len(km.keys)}")
    print(f"Working keys: {working_keys}")
    print(f"Success rate: {working_keys/len(km.keys)*100:.1f}%")


def setup_environment() -> None:
    """Setup the development environment."""
    print("\n=== Setting Up Environment ===")
    
    # Check project structure
    for dir_path in [
        "ai",
        "backend",
        "frontend",
        "scripts",
        "tests",
    ]:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path):
            print(f"✅ {dir_path}/ exists")
        else:
            print(f"❌ {dir_path}/ missing!")


def main() -> None:
    print("=== QUANTUM FORGE Development Environment ===")
    print(f"Project root: {project_root}")
    
    # Test OpenRouter integration
    test_keys()
    
    # Verify environment
    setup_environment()
    
    print("\n=== Ready to Code! ===")
    print("Tips:")
    print("1. Keys marked as quota-limited will automatically reset after 24 hours")
    print("2. Use ai.openrouter_adapter.generate() for AI completions")
    print("3. Key rotation and retries are handled automatically")
    print("4. Check ai/openrouter_keys_state.json for key status")


if __name__ == "__main__":
    main()