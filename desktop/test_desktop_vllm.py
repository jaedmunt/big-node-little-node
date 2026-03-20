from vllm import LLM, SamplingParams


def main():
    llm = LLM(
        model="Qwen/Qwen2.5-7B-Instruct-AWQ",
        max_model_len=2048,
        gpu_memory_utilization=0.90,
        disable_log_stats=True,
    )

    params = SamplingParams(
        temperature=0.2,
        max_tokens=128,
    )

    outputs = llm.generate(
        ["Write one short paragraph about why quantization helps inference."],
        params,
    )

    print(outputs[0].outputs[0].text)


if __name__ == "__main__":
    main()
