"""Quick test for LLM connection."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import get_settings
from app.core.llm_client import LLMClient


def main():
    print("=" * 70)
    print("Testing LLM Connection")
    print("=" * 70)

    settings = get_settings()

    print(f"\nConfiguration:")
    print(f"  Provider: {settings.llm.provider}")
    print(f"  Base URL: {settings.llm.base_url}")
    print(f"  Model: {settings.llm.model}")
    print(f"  Timeout: {settings.llm.timeout}s")

    llm_client = LLMClient(settings.llm)

    print(f"\n1. Testing connection...")
    is_connected = llm_client.is_connected()

    if is_connected:
        print(f"   [PASS] Connected successfully!")

        print(f"\n2. Testing simple completion...")
        try:
            response = llm_client.complete(
                prompt="Say 'Hello from AI Suite' and nothing else.",
                max_tokens=50,
                temperature=0.1,
            )
            print(f"   [PASS] Completion successful!")
            print(f"   Response: {response}")

            print(f"\n[SUCCESS] LLM is working!")
            return 0

        except Exception as e:
            print(f"   [FAIL] Completion failed: {e}")
            return 1
    else:
        print(f"   [FAIL] Could not connect to LLM server")
        print(f"   Check that the server is running at {settings.llm.base_url}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
