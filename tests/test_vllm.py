"""
Standalone vLLM test — no Ray required.
Run this on the desktop with the GPU. DESKTOP_MODEL must be set in .env.

Run: python tests/test_vllm.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from vllm import LLM, SamplingParams
except ImportError:
    print("pip install vllm")
    sys.exit(1)

MODEL = os.environ.get("DESKTOP_MODEL", "Qwen/Qwen2.5-7B-Instruct-AWQ")


def test_basic_generation():
    print(f"Loading {MODEL} ... (this takes a moment)")
    llm = LLM(
        model=MODEL,
        max_model_len=512,
        gpu_memory_utilization=0.85,
        disable_log_stats=True,
    )
    params = SamplingParams(temperature=0.1, max_tokens=64)

    prompt = (
        "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
        "<|im_start|>user\nWhat is 2 + 2? One word answer.<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    print("test_basic_generation ... ", end="", flush=True)
    outputs = llm.generate([prompt], params)
    text = outputs[0].outputs[0].text.strip()
    assert len(text) > 0
    print(f"ok  ({text!r})")


if __name__ == "__main__":
    print("\nRunning standalone vLLM test (no Ray)\n")
    test_basic_generation()
    print("\nPassed.")
