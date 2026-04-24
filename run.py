# /// script
# dependencies = ["python-dotenv"]
# ///
"""
Interactive launcher. Prompts for a topic and which interface to use,
then starts the right processes.

    uv run run.py
    task run
    make run
"""

import os
import signal
import subprocess
import sys
import time

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"


def ask(prompt: str, options: list[str], default: int = 0) -> int:
    for i, opt in enumerate(options):
        marker = f"{GREEN}>{RESET}" if i == default else " "
        print(f"  {marker} {i + 1}. {opt}")
    print()
    raw = input(f"Choice [1-{len(options)}] (default {default + 1}): ").strip()
    if not raw:
        return default
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return idx
    except ValueError:
        pass
    return default


def wait_for_router(timeout: int = 15) -> bool:
    """Poll until interface/.ports exists, meaning the router is ready."""
    ports_file = os.path.join("interface", ".ports")
    for _ in range(timeout):
        if os.path.exists(ports_file):
            return True
        time.sleep(1)
    return False


def main():
    print(f"\n{BOLD}big-node-little-node{RESET}\n")

    topic = input("Topic (or Enter for default): ").strip() \
        or "whether small things can have big impact"

    print(f"\nPick an interface:\n")
    choice = ask(
        "Interface",
        [
            "Python chat  — Ray direct, simplest",
            "Rig.rs       — Rust client via router",
            "Open WebUI   — browser UI via router (Docker required)",
        ],
        default=0,
    )

    router_proc = None

    if choice in (1, 2):
        print(f"\n{DIM}Starting router...{RESET}")
        router_proc = subprocess.Popen(
            ["uv", "run", "interface/router.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_router():
            print("Router didn't come up in time. Is the Ray cluster running?")
            router_proc.terminate()
            sys.exit(1)
        print(f"{GREEN}Router ready.{RESET}\n")

    try:
        if choice == 0:
            subprocess.run(["uv", "run", "interface/chat.py", topic])

        elif choice == 1:
            subprocess.run([
                "cargo", "run", "--manifest-path", "interface/Cargo.toml",
                "--", topic,
            ])

        elif choice == 2:
            subprocess.run(["bash", "interface/webui.sh"])
            print(f"\nOpen WebUI running at {CYAN}http://localhost:3000{RESET}")
            print(f"{DIM}Add the router endpoints under Settings → Connections.{RESET}")
            input("\nPress Enter to stop the router and exit.")

    except KeyboardInterrupt:
        pass
    finally:
        if router_proc:
            router_proc.terminate()


if __name__ == "__main__":
    main()
