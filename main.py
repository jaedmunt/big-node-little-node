import os
import ray
from dotenv import load_dotenv

load_dotenv()

TOPIC = "whether small things can have big impact"
TURNS = 3

QWEN_MODEL = os.environ["DESKTOP_MODEL"]
PI_MODEL_PATH = os.environ["PI_MODEL_PATH"]


@ray.remote(num_gpus=1)
class DesktopModel:
    def __init__(self):
        from vllm import LLM, SamplingParams
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
            f"You are in a spoken conversation about: {TOPIC}. "
            "Reply in 2-3 sentences. Be direct and conversational.\n"
            "<|im_end|>\n"
            f"<|im_start|>user\n{context}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        outputs = self.llm.generate([prompt], self.params)
        return outputs[0].outputs[0].text.strip()


@ray.remote(resources={"pi": 1})
class PiModel:
    def __init__(self):
        from llama_cpp import Llama
        self.llm = Llama(
            model_path=PI_MODEL_PATH,
            n_ctx=512,
            verbose=False,
        )

    def generate(self, context: str) -> str:
        prompt = (
            f"<|system|>\nYou are in a spoken conversation about: {TOPIC}. "
            "Reply in 1-2 sentences. Be brief.</s>\n"
            f"<|user|>\n{context}</s>\n"
            "<|assistant|>\n"
        )
        output = self.llm(prompt, max_tokens=80, stop=["</s>", "<|user|>", "<|system|>"])
        return output["choices"][0]["text"].strip()


def main():
    ray.init()

    print(f"\nTopic: {TOPIC}\n{'=' * 60}\n")

    desktop = DesktopModel.remote()
    pi = PiModel.remote()

    history = []
    seed = f"Let's talk about {TOPIC}."

    for _ in range(TURNS):
        context = seed if not history else "\n".join(history[-4:])
        reply = ray.get(desktop.generate.remote(context))
        history.append(f"[Qwen]: {reply}")
        print(f"[Qwen]:\n{reply}\n")

        context = "\n".join(history[-4:])
        reply = ray.get(pi.generate.remote(context))
        history.append(f"[TinyLlama]: {reply}")
        print(f"[TinyLlama]:\n{reply}\n")
        print("-" * 40)

    print("\nDone.")


if __name__ == "__main__":
    main()
