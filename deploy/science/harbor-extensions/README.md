# Science ACS evaluation adapter

Shanghai public ACR is consumed by Beijing ACS. UniverseACK selects runtime/verifier images by the controlled single-task environment/tests directory contract; multistep layouts are not supported by this adapter. Both image references require explicit digests.

The current candidate verifier uses public networking by explicit user instruction. Independent verifier containers remain required. Do not infer network isolation.

mini-swe-agent 2.2.8 harness requires litellm 1.106.2, openai 2.54.0 and mcp. The Dockerfile records a clean build recipe from the official runtime digest. Transitive dependency locking is still pending.

No secrets belong here. Registry credentials are loaded by control-plane tooling from workspace private configuration. Every run must use ACS cleanup guard.
