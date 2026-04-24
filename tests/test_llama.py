"""
Standalone llama-cpp test — no Ray required.
Run this on the Pi (or the desktop if the model file is available locally).
PI_MODEL_PATH must be set in .env.

Run: python tests/test_llama.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from llama_cpp import Llama
except ImportError:
    print("pip install llama-cpp-python")
    sys.exit(1)

MODEL_PATH = os.environ.get("PI_MODEL_PATH", "")
if not MODEL_PATH:
    print("Set PI_MODEL_PATH in .env")
    sys.exit(1)


def test_basic_generation():
    print(f"Loading {MODEL_PATH} ...")
    llm = Llama(model_path=MODEL_PATH, n_ctx=256, verbose=False)

    prompt = (
        "<|system|>\nYou are a helpful assistant.</s>\n"
        "<|user|>\nWhat is 2 + 2? One word.<|im_end|></s>\n"
        "<|assistant|>\n"
    )

    print("test_basic_generation ... ", end="", flush=True)
    output = llm(prompt, max_tokens=16, stop=["</s>", "<|user|>"])
    text = output["choices"][0]["text"].strip()
    assert len(text) > 0
    print(f"ok  ({text!r})")


def test_longer_response():
    print("test_longer_response  ... ", end="", flush=True)
    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)

    prompt = (
        "<|system|>\nYou are a helpful assistant. Be brief.</s>\n"
        "<|user|>\nName two benefits of small language models.</s>\n"
        "<|assistant|>\n"
    )
    output = llm(prompt, max_tokens=64, stop=["</s>", "<|user|>"])
    text = output["choices"][0]["text"].strip()
    assert len(text) > 10
    print(f"ok  ({len(text)} chars)")


if __name__ == "__main__":
    print("\nRunning standalone llama-cpp tests (no Ray)\n")
    test_basic_generation()
    test_longer_response()
    print("\nAll passed.")
