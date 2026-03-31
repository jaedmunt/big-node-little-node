import os
from dotenv import load_dotenv
from llama_cpp import Llama

load_dotenv()

MODEL_PATH = os.environ["PI_MODEL_PATH"]


def main():
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=512,
        verbose=False,
    )

    prompt = (
        "<|system|>\nYou are a helpful assistant.</s>\n"
        "<|user|>\nWrite one short paragraph about why small language models are useful.</s>\n"
        "<|assistant|>\n"
    )

    output = llm(prompt, max_tokens=128, stop=["</s>", "<|user|>"])
    print(output["choices"][0]["text"].strip())


if __name__ == "__main__":
    main()
