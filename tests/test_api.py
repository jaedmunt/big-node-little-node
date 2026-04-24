"""
Checks that the local model servers are reachable and returning sensible output.
No cloud API — hits the vLLM and llama-cpp endpoints directly.

Requires both servers to be running:
    desktop:  vllm serve $DESKTOP_MODEL --port 8000
    pi:       python -m llama_cpp.server --model $PI_MODEL_PATH --host 0.0.0.0 --port 8000

Run: python tests/test_api.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    print("pip install openai")
    sys.exit(1)

DESKTOP_ENDPOINT = os.getenv("DESKTOP_ENDPOINT", "http://localhost:8000/v1")
DESKTOP_MODEL    = os.getenv("DESKTOP_MODEL",    "Qwen/Qwen2.5-7B-Instruct-AWQ")
PI_ENDPOINT      = os.getenv("PI_ENDPOINT",      "http://YOUR_PI_IP:8000/v1")
PI_MODEL         = os.getenv("PI_MODEL_NAME",    "tinyllama")


def check(client: OpenAI, model: str, label: str):
    print(f"  {label} ... ", end="", flush=True)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with one word: ready"}],
        max_tokens=8,
        temperature=0.0,
    )
    text = resp.choices[0].message.content.strip()
    assert len(text) > 0
    print(f"ok  ({text!r})")


def test_desktop():
    client = OpenAI(base_url=DESKTOP_ENDPOINT, api_key="not-needed")
    check(client, DESKTOP_MODEL, f"Desktop ({DESKTOP_ENDPOINT})")


def test_pi():
    client = OpenAI(base_url=PI_ENDPOINT, api_key="not-needed")
    check(client, PI_MODEL, f"Pi      ({PI_ENDPOINT})")


if __name__ == "__main__":
    print("\nPinging local model servers\n")
    failed = []

    for name, fn in [("desktop", test_desktop), ("pi", test_pi)]:
        try:
            fn()
        except Exception as e:
            print(f"  FAIL  ({e})")
            failed.append(name)

    print()
    if failed:
        print(f"Not reachable: {', '.join(failed)}")
        print("Make sure the servers are running — see .env.example for the commands.")
        sys.exit(1)
    else:
        print("Both endpoints up.")
