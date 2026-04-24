.PHONY: run chat router rig webui test-api test-vllm test-llama

# Interactive launcher — choose your interface
run:
	uv run run.py

# Start the interactive Python chat (talks to Ray directly)
chat:
	uv run interface/chat.py $(TOPIC)

# Start the router (exposes Ray actors as HTTP endpoints for Rig.rs / WebUI)
router:
	uv run interface/router.py

# Build and run the Rig.rs client (requires router to be running)
rig:
	cargo run --manifest-path interface/Cargo.toml -- $(TOPIC)

# Start Open WebUI in Docker (requires router to be running)
webui:
	bash interface/webui.sh

# Tests
test-api:
	uv run tests/test_api.py

test-vllm:
	uv run tests/test_vllm.py

test-llama:
	uv run tests/test_llama.py
