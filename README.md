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

## Hardware, OS 
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

- Raspberry Pi OS (Debian GNU/Linux 13.3 (trixie))
- BCM2711 (4) @ 1.80 GHz *n.b. ARM architecture*
- Broadcom bcm2711-vc5 [Integrated]





```bash
        _,met$$$$$gg.          admin@thunderpi
     ,g$$$$$$$$$$$$$$$P.       ---------------
   ,g$$P""       """Y$$.".     OS: Debian GNU/Linux 13 (trixie) aarch64
  ,$$P'              `$$$.     Host: Raspberry Pi 4 Model B Rev 1.4
',$$P       ,ggs.     `$$b:    Kernel: Linux 6.12.62+rpt-rpi-v8
`d$$'     ,$P"'   .    $$$     Uptime: 1 hour, 35 mins
 $$P      d$'     ,    $$P     Packages: 1712 (dpkg)
 $$:      $$.   -    ,d$$'     Shell: zsh 5.9
 $$;      Y$b._   _,d$P'       Display (DSI-1): 800x480 @ 60 Hz in 7"
 Y$$.    `.`"Y$$$$P"'          WM: labwc (Wayland)
 `$$b      "-.__               Cursor: Adwaita
  `Y$$b                        Terminal: /dev/pts/0
   `Y$$.                       CPU: BCM2711 (4) @ 1.80 GHz
     `$$b.                     GPU: Broadcom bcm2711-vc5 [Integrated]
       `Y$$b.                  Memory: 387.95 MiB / 3.71 GiB (10%)
         `"Y$b._               Swap: 0 B / 2.00 GiB (0%)
             `""""             Disk (/): 10.47 GiB / 28.09 GiB (37%) - ext4
                               Local IP (wlan0):[redacted] 
                               Locale: en_GB.UTF-8

```


Running Raspberry 




- Desktop PC - home build *(trimmed down to just the important bits)*

  - Windows 11 with WSL (Archlinux)
  - NVIDIA GeForce RTX 3060 (11.83 GiB)
  - Intel(R) Core(TM) i5-10500 (12) @ 3.10 GHz

```bash
                  -`                     root@DESKTOP-C0P5MSL
                 .o+`                    --------------------
                `ooo/                    OS: Arch Linux x86_64
               `+oooo:                   Kernel: Linux 6.6.87.2-microsoft-standard-WSL2
              `+oooooo:                  Uptime: 1 hour, 10 mins
              -+oooooo+:                 Packages: 829 (pacman)
            `/:-:++oooo+:                Shell: zsh 5.9
           `/++++/+++++++:               Display (XWAYLAND0): 2560x1440, 60 Hz
          `/++++++++++++++:              Display (XWAYLAND1): 1920x1080 in 24", 60 Hz
         `/+++ooooooooooooo/`            WM: Weston WM (Microsoft Corporation)
        ./ooosssso++osssssso+`           Cursor: Adwaita
       .oossssso-````/ossssss+`          Terminal: nvim
      -osssssso.      :ssssssso.         CPU: Intel(R) Core(TM) i5-10500 (12) @ 3.10 GHz
     :osssssss/        osssso+++.        GPU 1: NVIDIA GeForce RTX 3060 (11.83 GiB) [Discrete]
    /ossssssss/        +ssssooo/-        GPU 2: Intel(R) UHD Graphics 630 (128.00 MiB) [Integrated]
  `/ossssso+/:-        -:/+osssso+-      Memory: 851.17 MiB / 39.10 GiB (2%)
 `+sso+:-`                 `.-/+oso:     Swap: 0 B / 10.00 GiB (0%)
`++:.                           `-/+/    Disk (/): 31.86 GiB / 1006.85 GiB (3%) - ext4
.`                                 `/    Disk (/mnt/c): [redacted] 
                                         Disk (/mnt/d): [redacted]
                                         Disk (/mnt/e): [redacted]
                                         Disk (/mnt/f): 354.65 GiB / 931.50 GiB (38%) - 9p
                                         Local IP (eth0):  [redacted]
                                         Locale: en_US.UTF-8

```

## Networking


