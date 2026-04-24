# /// script
# dependencies = ["ray[default]", "python-dotenv"]
# ///
"""
Interactive conversation interface — uses the Ray cluster, same as main.py.

The Ray head must be running on the desktop and the Pi must be connected.
Start them before running this:
    desktop:  ray start --head --port=6379 --dashboard-host=0.0.0.0
    pi:       ray start --address='DESKTOP_LAN_IP:6379' --num-cpus=2 --resources='{"pi": 1}'

Run:
    uv run interface/chat.py "your topic"
    uv run interface/chat.py   # prompts for topic

Enter to cut in with your own message. Ctrl+C to quit.
"""

import os
import queue
import sys
import threading
import time
import ray
from dotenv import load_dotenv

load_dotenv()

TOPIC    = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
QWEN_MODEL   = os.environ["DESKTOP_MODEL"]
PI_MODEL_PATH = os.environ["PI_MODEL_PATH"]

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"

MAX_HISTORY = 6  # recent messages kept in context


@ray.remote(num_gpus=1)
class DesktopModel:
    def __init__(self, topic: str):
        from vllm import LLM, SamplingParams
        self.topic = topic
        self.llm = LLM(
            model=QWEN_MODEL,
            max_model_len=2048,
            gpu_memory_utilization=0.90,
            disable_log_stats=True,
        )
        self.params = SamplingParams(temperature=0.7, max_tokens=150)

    def generate(self, context: str) -> str:
        prompt = (
            "<|im_start|>system\n"
            f"You are in a spoken conversation about: {self.topic}. "
            "Reply in 2-3 sentences. Be direct and conversational.\n"
            "<|im_end|>\n"
            f"<|im_start|>user\n{context}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        outputs = self.llm.generate([prompt], self.params)
        return outputs[0].outputs[0].text.strip()


@ray.remote(resources={"pi": 1})
class PiModel:
    def __init__(self, topic: str):
        from llama_cpp import Llama
        self.topic = topic
        self.llm = Llama(model_path=PI_MODEL_PATH, n_ctx=512, verbose=False)

    def generate(self, context: str) -> str:
        prompt = (
            f"<|system|>\nYou are in a spoken conversation about: {self.topic}. "
            "Reply in 1-2 sentences. Be brief.</s>\n"
            f"<|user|>\n{context}</s>\n"
            "<|assistant|>\n"
        )
        output = self.llm(prompt, max_tokens=80, stop=["</s>", "<|user|>", "<|system|>"])
        return output["choices"][0]["text"].strip()


def start_inject_listener(inject_q: queue.Queue, quit_flag: threading.Event):
    """Reads lines from stdin in the background and queues them as injections."""
    def run():
        while not quit_flag.is_set():
            try:
                line = input()
                if line.strip():
                    inject_q.put(line.strip())
            except EOFError:
                quit_flag.set()

    threading.Thread(target=run, daemon=True).start()


def run(topic: str):
    print(f"\n{DIM}Connecting to Ray cluster...{RESET}")
    ray.init(address="auto")

    print(f"{DIM}Starting models on cluster (this takes a moment)...{RESET}")
    desktop = DesktopModel.remote(topic)
    pi      = PiModel.remote(topic)

    inject_q  = queue.Queue()
    quit_flag = threading.Event()
    start_inject_listener(inject_q, quit_flag)

    print(f"\n{DIM}{'─' * 60}{RESET}")
    print(f"{BOLD}Topic:{RESET} {topic}")
    print(f"{DIM}Type a message and press Enter to interject  |  Ctrl+C to quit{RESET}")
    print(f"{DIM}{'─' * 60}{RESET}\n")

    history = []
    context = f"Let's talk about {topic}."
    turn = 0

    try:
        while not quit_flag.is_set():
            is_desktop = turn % 2 == 0
            actor = desktop if is_desktop else pi
            name  = "Desktop" if is_desktop else "Pi"
            color = CYAN      if is_desktop else YELLOW

            reply = ray.get(actor.generate.remote(context))
            print(f"\n{color}{BOLD}[{name}]{RESET}  {reply}")

            history.append(f"[{name}]: {reply}")
            if len(history) > MAX_HISTORY:
                history.pop(0)

            # Check for a queued user message before the next turn.
            try:
                msg = inject_q.get_nowait()
                print(f"\n{GREEN}{BOLD}[You]{RESET}  {msg}")
                history.append(f"[You (observer)]: {msg}")
            except queue.Empty:
                pass

            context = "\n".join(history)
            turn += 1
            time.sleep(0.3)

    except KeyboardInterrupt:
        pass

    print(f"\n{DIM}{'─' * 60}{RESET}\n")
    ray.shutdown()


def main():
    print(f"\n{BOLD}big-node-little-node  |  chat{RESET}")

    topic = TOPIC or input("Topic: ").strip() or "whether small things can have big impact"

    try:
        run(topic)
    except Exception as e:
        print(f"\n{BOLD}Error:{RESET} {e}")
        print("Is the Ray cluster running? Check the Quickstart section in the README.")
        sys.exit(1)


if __name__ == "__main__":
    main()
