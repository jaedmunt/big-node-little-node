# big-node-little-node
Serving two nodes (desktop PC with nvidia RTX 3060 and raspberry pi 4) with [Ray](https://docs.ray.io/en/latest/index.html) and [vLLM](https://docs.vllm.ai/en/latest/)/[Llama-cpp](https://github.com/ggml-org/llama.cpp). For fun!

This is a toy project with a few initial goals, beginning with simple scaffolding, serving and and testing the models. These may/will expand. I will document the steps taken and choices, so you can do the same for your machines. 

Goals:
- [ ] We want to use Ray to run two models on some consumer hardware:
  - A desktop PC 
  - A Raspberry Pi 4B

- [ ] Output text and render on in each terminal 
- [ ] Connect webui and try each model

- [ ] Rig the models to converse with each other and have a conversation about a topic

## Hardware and network

- [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)

<div style="display: inline-block; background-color: blue; padding: 10px; width: 50%;">
  <img src="https://assets.raspberrypi.com/static/blueprint-labelled-97975f4b1159239a8e248d180be87e3e.svg" alt="Raspberry Pi 4 Tech Specs" style="display: block; margin: auto; width: 60%;">

```text
Broadcom BCM2711, Quad core Cortex-A72 (ARM v8) 64-bit SoC @ 1.8GHz
1GB, 2GB, 4GB or 8GB LPDDR4-3200 SDRAM (depending on model)
2.4 GHz and 5.0 GHz IEEE 802.11ac wireless, Bluetooth 5.0, BLE
Gigabit Ethernet
2 USB 3.0 ports; 2 USB 2.0 ports.
Raspberry Pi standard 40 pin GPIO header (fully backwards compatible with previous boards)
2 × micro-HDMI® ports (up to 4kp60 supported)
2-lane MIPI DSI display port
2-lane MIPI CSI camera port
4-pole stereo audio and composite video port
H.265 (4kp60 decode), H264 (1080p60 decode, 1080p30 encode)
OpenGL ES 3.1, Vulkan 1.0
Micro-SD card slot for loading operating system and data storage
5V DC via USB-C connector (minimum 3A*)
5V DC via GPIO header (minimum 3A*)
Power over Ethernet (PoE) enabled (requires separate PoE HAT)
Operating temperature: 0 – 50 degrees C ambient
```
</div>   




- Desktop PC - home build
