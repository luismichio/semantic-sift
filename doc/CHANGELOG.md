# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
