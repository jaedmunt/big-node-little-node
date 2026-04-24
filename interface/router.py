# /// script
# dependencies = ["ray[default]", "fastapi", "uvicorn[standard]", "python-dotenv"]
# ///
"""
Bridges the Ray cluster to two OpenAI-compatible HTTP endpoints so any
standard client (Rig.rs, curl, etc.) can call the models without knowing
about Ray.

Start the Ray cluster first, then:
    python interface/router.py

Endpoints:
    Desktop (vLLM)      → http://localhost:8100/v1
    Pi (llama-cpp)      → http://localhost:8101/v1

Set these in .env:
    DESKTOP_ENDPOINT=http://localhost:8100/v1
    PI_ENDPOINT=http://localhost:8101/v1
"""

import os
import time
import threading
import uuid
import ray
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

QWEN_MODEL    = os.environ["DESKTOP_MODEL"]
PI_MODEL_PATH = os.environ["PI_MODEL_PATH"]

PORTS_FILE = os.path.join(os.path.dirname(__file__), ".ports")


def find_free_port(preferred: int) → int:
    """Use the preferred port if free, otherwise let the OS pick one."""
    import socket
    with socket.socket() as s:
        try:
            s.bind(("", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


DESKTOP_PORT = find_free_port(int(os.getenv("DESKTOP_ROUTER_PORT", "8100")))
PI_PORT      = find_free_port(int(os.getenv("PI_ROUTER_PORT",      "8101")))


@ray.remote(num_gpus=1)
class DesktopActor:
    def __init__(self):
        from vllm import LLM
        self.llm = LLM(
            model=QWEN_MODEL,
            max_model_len=2048,
            gpu_memory_utilization=0.90,
            disable_log_stats=True,
        )

    def generate(self, messages: list, max_tokens: int) → str:
        prompt = ""
        for m in messages:
            if m["role"] == "system":
                prompt += f"<|im_start|>system\n{m['content']}<|im_end|>\n"
            elif m["role"] == "user":
                prompt += f"<|im_start|>user\n{m['content']}<|im_end|>\n"
            elif m["role"] == "assistant":
                prompt += f"<|im_start|>assistant\n{m['content']}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"

        from vllm import SamplingParams
        out = self.llm.generate([prompt], SamplingParams(temperature=0.7, max_tokens=max_tokens))
        return out[0].outputs[0].text.strip()


@ray.remote(resources={"pi": 1})
class PiActor:
    def __init__(self):
        from llama_cpp import Llama
        self.llm = Llama(model_path=PI_MODEL_PATH, n_ctx=512, verbose=False)

    def generate(self, messages: list, max_tokens: int) → str:
        prompt = ""
        for m in messages:
            if m["role"] == "system":
                prompt += f"<|system|>\n{m['content']}</s>\n"
            elif m["role"] == "user":
                prompt += f"<|user|>\n{m['content']}</s>\n"
            elif m["role"] == "assistant":
                prompt += f"<|assistant|>\n{m['content']}</s>\n"
        prompt += "<|assistant|>\n"

        out = self.llm(prompt, max_tokens=max_tokens, stop=["</s>", "<|user|>", "<|system|>"])
        return out["choices"][0]["text"].strip()


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = ""
    messages: list[ChatMessage]
    max_tokens: int = 150
    temperature: float = 0.7


def make_app(actor, model_name: str) → FastAPI:
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest):
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        text = ray.get(actor.generate.remote(messages, req.max_tokens))
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    @app.get("/v1/models")
    async def models():
        return {"object": "list", "data": [{"id": model_name, "object": "model"}]}

    return app


def main():
    print("Connecting to Ray cluster...")
    ray.init(address="auto")

    print("Starting actors (first run loads the models — takes a moment)...")
    desktop_actor = DesktopActor.remote()
    pi_actor      = PiActor.remote()

    desktop_app = make_app(desktop_actor, QWEN_MODEL)
    pi_app      = make_app(pi_actor, "tinyllama")

    # Write chosen ports so clients (Rig.rs etc.) can discover them automatically.
    with open(PORTS_FILE, "w") as f:
        f.write(f"desktop=http://localhost:{DESKTOP_PORT}/v1\n")
        f.write(f"pi=http://localhost:{PI_PORT}/v1\n")

    print(f"\nRouter ready:")
    print(f"  Desktop  http://localhost:{DESKTOP_PORT}/v1")
    print(f"  Pi       http://localhost:{PI_PORT}/v1")
    print(f"\n  Ports written to interface/.ports")
    print(f"  Override anytime via DESKTOP_ROUTER_PORT / PI_ROUTER_PORT in .env\n")

    threads = [
        threading.Thread(
            target=uvicorn.run,
            kwargs={"app": desktop_app, "host": "0.0.0.0", "port": DESKTOP_PORT, "log_level": "error"},
            daemon=True,
        ),
        threading.Thread(
            target=uvicorn.run,
            kwargs={"app": pi_app, "host": "0.0.0.0", "port": PI_PORT, "log_level": "error"},
            daemon=True,
        ),
    ]

    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nShutting down.")
        ray.shutdown()


if __name__ == "__main__":
    main()
