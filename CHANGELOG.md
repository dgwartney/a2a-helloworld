# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.3.0] - 2026-03-15

### Added
- Interactive chat REPL mode (default when `--message` is omitted)
- REPL commands: `/help`, `/quit`, `/exit`
- ANSI-formatted terminal output for user messages, agent responses, and errors
- Streaming typing indicator (`● typing...`) and completion timing (`✓ done`)
- `--streaming` / `--no-streaming` flag (defaults to non-streaming)
- `--log-file` CLI argument and `A2A_LOG_FILE` environment variable to redirect logs to a file
- `ChatFormatter` class in new `formatter.py` module for ANSI terminal rendering

### Changed
- Client defaults to non-streaming mode (`message:send` endpoint)
- `HelloWorldClient.send_message()` refactored to async generator yielding raw SDK events
- Renamed `HelloWorldCLI` to `HelloWorldChat` with REPL and single-shot mode support
- `--message` uses a sentinel default to distinguish between omitted and explicitly passed

## [0.2.0] - 2026-03-15

### Added
- `--agent-card-only` flag to fetch and print the agent card without sending a message
- `--message` CLI argument for sending a text message to the agent
- `--log-level`, `--log-format` CLI arguments and corresponding environment variables (`A2A_LOG_LEVEL`, `A2A_LOG_FORMAT`)
- Shared `log.py` module with `DEFAULT_LOG_FORMAT` constant
- Named logger instances per module

### Changed
- Refactored logging configuration into a shared module used by both agent and client

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
- Agent card served at `/.well-known/agent-card.json`
- CLI entry points: `agent` and `client`
- Containerfile for building with Podman/Docker
- `pyproject.toml` with `hatchling` build backend
- MIT License
