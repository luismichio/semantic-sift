# 🔍 Semantic-Sift

**The "Sanitation Tier" for high-fidelity agentic workflows.**

Semantic-Sift is a standalone [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server designed to preserve signal and incinerate noise. It provides a hybrid compression engine that "Sifts" meaningful semantics from natural language and "Sieves" structural junk from technical logs.

---

## 🧠 Why Semantic-Sift?

In a world of 128k+ context windows, the bottleneck isn't size—it's **Signal-to-Noise Ratio (SNR)**.
- **Problem**: Raw logs and verbose conversation history drown the agent's attention, leading to "Lost in the Middle" syndrome and high token costs.
- **Solution**: A local, sovereign middleware that distill data *before* it enters the context window.

---

## 🛠️ Hybrid Engine

### 1. The Sieve (Structural)
**Fast Heuristic Distillation.**
Perfect for terminal outputs, Vercel logs, and build artifacts.
- Removes timestamps, UUIDs, and ephemeral session data.
- Collapses repetitive progress bars and noise.
- **Tool**: `sift_logs`

### 2. The Sift (Semantic)
**AI-Powered Context Pruning.**
Powered by **LLMLingua-2**, it uses a BERT-based model to identify and keep instruction-carrying tokens while discarding verbal filler.
- Preserves core meaning at 20-80% compression rates.
- Keeps entity structure and questions intact.
- **Tool**: `sift_chat`

### 3. Telemetry Tier (Efficiency Tracking)
**Quantifiable Signal-to-Noise Ratio.**
Semantic-Sift tracks its own efficiency persistently across sessions.
- Monitors character savings and compression ratios.
- Tracks processing latency to ensure real-time performance.
- **Tool**: `get_sift_stats`

### 4. Automated Onboarding (One-Click Setup)
**Zero-Configuration Guidelines.**
Automatically injects sifting best practices into your agent instruction files.
- Detects `AGENTS.md`, `.clinerules`, or `.cursorrules`.
- Provides a full environment diagnostic report (Python, CUDA, GPU).
- **Tool**: `sift_onboard`

### 5. Context Advisory (Smart Recommendations)
**Actionable Intelligence on SNR.**
Analyzes text to determine if it's "noisy" enough to require sifting.
- Calculates an "Estimated Noise %" based on heuristics.
- Recommends the specific tool (`sift_logs` vs `sift_chat`) to use.
- **Tool**: `sift_analyze`

### 6. Intelligence Tier (Re-ranking & Caching)
**Relevance-First Sifting.**
Prioritizes and optimizes sifting operations for speed and accuracy.
- **Re-ranking**: Ranks multiple text chunks by relevance using BGE-Reranker. (`sift_rank`)
- **Semantic Caching**: Automatically stores results to make repeat sifts instantaneous.
- **Tool**: `sift_rank`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PyTorch (Installed automatically via `requirements.txt`)

### Installation & Setup

1. **Clone & Setup Environment**
   ```bash
   git clone https://github.com/luismichio/semantic-sift.git
   cd semantic-sift
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. **Run the Server**
   ```bash
   python server.py
   ```

### Registering in MCP Config
Add this to your `claude_desktop_config.json` or equivalent:

```json
{
  "mcpServers": {
    "semantic-sift": {
      "command": "python",
      "args": ["/path/to/semantic-sift/server.py"]
    }
  }
}
```

---

## 📖 Philosophy: The Studio of Two
Semantic-Sift is a product of the **Studio of Two** philosophy: *We build Systems, not Patches.* 

It is designed to be a "Sovereign Sidecar"—operating entirely on your local machine to protect your privacy and your wallet.

## 📄 License
MIT. See `LICENSE` for details.
