# big-node-little-node
Serving two nodes (desktop PC with nvidia RTX 3060 and raspberry pi 4) with [Ray](https://docs.ray.io/en/latest/index.html) and [vLLM](https://docs.vllm.ai/en/latest/)/[Llama-cpp](https://github.com/ggml-org/llama.cpp). For fun!

Goal:
- We want to use Ray to run two models on some consumer hardware:
  - A desktop PC 
  - A Raspberry Pi 4B
