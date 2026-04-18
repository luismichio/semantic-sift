# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Heuristic Orchestration**: Refactored `sift_orchestrate` to use keyword-based heuristic matching, allowing it to identify tool categories (e.g., `mcp-server-postgres` matches `postgres`).
- **Expanded Synergies**: Added 15+ new specialized collaboration rules for **Slack**, **Notion**, **AWS**, **Postgres**, **Puppeteer**, **Jira**, **Linear**, and more.
- **Super-Agnostic Orchestration**: Upgraded `sift_orchestrate` to automatically discover tools from **Continue**, **Zed**, **GitHub Copilot**, **OpenCode**, and **Antigravity** across Windows and macOS.
- **Custom Configuration**: `sift_orchestrate` now accepts `custom_tools` and `custom_paths` for tailored environment discovery.
- **Intelligence Tier**: New `sift_rank` tool using **BGE-Reranker** (`BAAI/bge-reranker-base`) to prioritize the most relevant text chunks from multiple documents before sifting.
- **Persistent Semantic Cache**: Implemented a local disk cache (`.sift_cache/`) that stores sifting results. Repeat calls for the same text and parameters now have near-zero latency (~1ms).
- **Context Advisory**: New `sift_analyze` tool that evaluates context quality (SNR) and recommends appropriate sifting actions based on noise heuristics and document length.
- **Automated Onboarding**: New `sift_onboard` tool that automatically injects Semantic-Sift usage guidelines into project instruction files (`AGENTS.md`, `.clinerules`, etc.) and provides an environment diagnostic report.
- **GPU Acceleration**: Migrated to Python 3.12 environment (`venv312`) to enable CUDA 12.1 support for RTX 2070 Super.
- **Device-Aware Resilience**: Added automatic torch device detection (CUDA/CPU) to prevent crashes when GPU support is missing.
- **Telemetry Tier**: Implemented a persistent telemetry system (`.sift_telemetry.json`) that tracks compression ratios, character savings, and processing latency across sessions.
- **get_sift_stats**: New MCP tool to query session-based or global performance metrics.
- **MCP Configuration**: Integrated `context-mode`, `serena`, and `github` MCP servers into the workspace via `.gemini/settings.json`.
- **Serena Project Configuration**: Added `.serena/project.yml` and `.serena/project.local.yml` for local agent orchestration.
- **Agent Guidelines**: Created `AGENTS.md` to define project-specific standards and philosophy.

## [1.0.0] - 2026-04-13

### Added
- **Initial Release**: The birth of the "Sanitation Tier" for agentic workflows.
- **Server Core**: Implemented as a standalone Python FastMCP server.
- **sift_logs**: Heuristic tool for stripping structural noise from technical logs (Timestamps, UUIDs, verbose build output).
- **sift_chat**: Semantic compression tool powered by **LLMLingua-2** (using the `microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank` model).
- **sift_doc**: Hybrid tool for condensing long MDX/PDF text by combining log-sifting and chat-sifting logic. Enhanced with structural token protection.
- **sift_extraction**: A dedicated refinery tool for Docling/LiteParse outputs. Strips document debris (headers/footers) while preserving Markdown structure for high-quality RAG indexing.
- **The Refinery Loop**: Defined a new architectural pattern for piping data from Docling extraction through Semantic-Sift before landing in LlamaIndex.
- **Documentation**: Initial `ARCHITECTURE.md` detailing the "Studio of Two" philosophy and the RAG synergy model.

### Fixed
- Corrected Hugging Face model identifier for LLMLingua-2 from `-instruct` to `-meetingbank`.

### Security
- **Local Sovereignty**: All processing is performed locally; no data is sent to external APIs for compression.
