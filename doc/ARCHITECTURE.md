# Semantic-Sift: Architecture & Philosophy

## 🧠 Core Philosophy
Semantic-Sift is built on the **"Studio of Two"** principle: We build **Systems, not Patches**. 

In the modern agentic workspace, the primary bottleneck is not processing power, but **Signal-to-Noise Ratio (SNR)** within the LLM's context window. Semantic-Sift acts as a high-fidelity "Sanitation Tier" that ensures the agent only "sees" the meaningful essence of data.

---

## 🏗️ Architectural Overview

Semantic-Sift is a standalone, protocol-compliant **MCP (Model Context Protocol) Server** written in Python. It provides a hybrid approach to data reduction:

### 1. The Sieve (Structural Distillation)
- **Mechanism**: Rule-based heuristic filtering (Regex).
- **Target**: Technical logs (Vercel, GitHub, Console), build outputs, and boilerplate-heavy data.
- **Logic**: 
    - Removes ephemeral noise (Timestamps, UUIDs, Session IDs).
    - Collapses repetitive patterns (Progress bars, "Building..." lines).
    - Strips low-entropy technical metadata.
- **Goal**: ~40-60% reduction with zero semantic risk and near-zero latency.

### 2. The Sift (Semantic Compression)
- **Mechanism**: Model-based compression using **LLMLingua-2** (Prompt Compression).
- **Target**: Natural language conversation logs, long MDX pages, and PDF transcripts.
- **Logic**: Uses a lightweight BERT-based model (`microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`) to calculate token importance. It removes linguistic filler while preserving instruction-carrying tokens and core semantic entities.
- **Goal**: ~20-80% reduction (configurable) while maintaining the 95%+ fidelity of the original meaning.

---

## 🛠️ Technical Stack

- **Kernel**: Python 3.13 (Native performance for AI libraries).
- **Communication**: FastMCP (Standardized I/O for AI Agents).
- **AI Core**: PyTorch + Hugging Face Transformers.
- **Model**: LLMLingua-2 (MeetingBank fine-tuned).

---

## 🚀 Deployment Models

### 1. Developer Mode (Current)
Running as a standalone process on the developer machine.
`python server.py`

### 2. The Sidecar (Target)
Frozen into a standalone binary via **PyInstaller/Nuitka** and bundled inside the **Meechi (Tauri) App**.
- **Path**: `src-tauri/binaries/semantic-sift-[platform]`
- **Activation**: Auto-boot on application start via the Tauri Command API.

---

## 🔒 Security & Privacy
- **Local Sovereignty**: All sifting occurs on the local machine. No data is sent to external APIs for compression.
- **Local Model weights**: Models are cached locally in the user's home directory.

---

## 🌟 Future Roadmap
- **WebGPU Port**: Transitioning from PyTorch to `llmlingua-2-js` (ONNX) for browser-native execution.
- **Docling Integration**: Tiered PDF parsing that sifts documents before they ground the agent.
