"""
Interactive Gemini API Tester for SocioSync.
Run this script to test the Gemini connection directly from PowerShell:
    python test_gemini.py
"""
import os
import sys

# Load environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    import django
    django.setup()
    from django.conf import settings
    from ai.client import GeminiAIClient
    from pydantic import BaseModel
except Exception as e:
    print(f"Error loading Django/GenAI environment: {e}")
    sys.exit(1)


class SimpleReply(BaseModel):
    reply: str
    why_it_works: str


def run_test(custom_key=None, custom_prompt="Give me a hook for an Instagram Reel about coffee"):
    print("=" * 60)
    print("        SocioSync — Google Gemini Live API Tester")
    print("=" * 60)

    if custom_key:
        os.environ["GEMINI_API_KEY"] = custom_key
        settings.GEMINI_API_KEY = custom_key
        print(f"[*] Using Custom API Key: {custom_key[:8]}...{custom_key[-4:]}")
    else:
        current_key = settings.GEMINI_API_KEY.strip()
        print(f"[*] Using Configured .env API Key: {current_key[:8]}...{current_key[-4:]}")

    print(f"[*] Target Model: {settings.GEMINI_MODEL}")
    print(f"[*] Sending Test Prompt: '{custom_prompt}'")
    print("[*] Connecting to Google Gemini API servers...")

    try:
        client = GeminiAIClient()
        result = client.generate_structured(
            prompt=f"Act as SocioSync AI Instagram Manager. Answer this prompt: {custom_prompt}",
            response_schema=SimpleReply,
        )
        print("\n" + "-" * 60)
        print(">>> SUCCESS! 200 OK RECEIVED FROM GOOGLE GEMINI <<<")
        print("-" * 60)
        print(f"Generated Reply : {result.data.get('reply')}")
        print(f"Strategy Reason : {result.data.get('why_it_works')}")
        print(f"Model Engine    : {result.model}")
        print("-" * 60)
        return True
    except Exception as exc:
        print("\n" + "!" * 60)
        print(f">>> GEMINI CONNECTION FAILED: {type(exc).__name__} <<<")
        print(f"Details: {exc}")
        print("!" * 60)
        return False


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Generate a viral hook for selling vintage boots on Instagram Reels"
    key = sys.argv[2] if len(sys.argv) > 2 else None
    run_test(custom_key=key, custom_prompt=prompt)
