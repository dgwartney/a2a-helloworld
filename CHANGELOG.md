# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `--preferred-transport` CLI argument and `A2A_PREFERRED_TRANSPORT` environment variable to select the transport binding at runtime (`HTTP+JSON`, `JSONRPC`, `GRPC`)
- JSON-RPC transport support via `A2AStarletteApplication`
- `--protocol-version` CLI argument and `A2A_PROTOCOL_VERSION` environment variable to set the A2A protocol version advertised in the agent card
- `--agent-url` CLI argument (overrides `A2A_AGENT_URL` environment variable) to set the agent card URL
- Startup configuration summary printed to stdout when the agent starts
- Shared `protocol.py` module with constants for known protocol versions and supported transports
- Client auto-selects transport based on the agent card's `preferredTransport` field
- Client supports legacy transport aliases (`JSON-RPC`, `gRPC`) for backward compatibility
- Protocol version validation (X.Y format) with warnings for unknown versions
- Apache License 2.0
- This changelog

### Changed
- CLI entry points renamed from `a2a-agent`/`a2a-client` to `agent`/`client`
- Transport name strings now use `TransportProtocol` enum values from the `a2a-sdk` for consistency with the SDK's `ClientFactory`

## [0.1.0] - 2026-03-15

### Added
- Initial Hello World agent returning "Hello World" for any input message
- HTTP+JSON transport binding via `A2ARESTFastAPIApplication`
- Test client using `ClientFactory` with `TransportProtocol.http_json`
- Agent card served at `/.well-known/agent-card.json`
- `A2A_AGENT_URL` environment variable for configuring the agent card URL
- Containerfile for building with Podman/Docker
- `pyproject.toml` with `hatchling` build backend
