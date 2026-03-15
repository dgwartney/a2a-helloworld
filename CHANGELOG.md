# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-03-15

### Added
- Initial Hello World agent returning "Hello World" for any input message
- HTTP+JSON transport binding via `A2ARESTFastAPIApplication`
- JSON-RPC transport binding via `A2AStarletteApplication`
- Runtime transport selection via `--preferred-transport` CLI argument and `A2A_PREFERRED_TRANSPORT` environment variable
- `--protocol-version` CLI argument and `A2A_PROTOCOL_VERSION` environment variable to set the A2A protocol version advertised in the agent card
- `--agent-url` CLI argument (overrides `A2A_AGENT_URL` environment variable) to set the agent card URL
- Protocol version validation (X.Y format) with warnings for unknown versions
- Startup configuration summary printed to stdout when the agent starts
- Shared `protocol.py` module with constants for known protocol versions and supported transports
- Client auto-selects transport based on the agent card's `preferredTransport` field
- Client supports legacy transport aliases (`JSON-RPC`, `gRPC`) for backward compatibility
- Agent card served at `/.well-known/agent-card.json`
- CLI entry points: `agent` and `client`
- Containerfile for building with Podman/Docker
- `pyproject.toml` with `hatchling` build backend
- MIT License
