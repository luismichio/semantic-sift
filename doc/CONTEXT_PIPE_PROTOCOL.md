# The Context-Pipe Protocol (CPP)

## Overview
The **Context-Pipe Protocol (CPP)** is a standard for modular, high-performance context engineering. It allows AI tools to be connected as a series of "Streams," ensuring that data is refined and noise is eliminated *before* it reaches the LLM's context window.

By following the Unix philosophy—**"Everything is a stream"**—CPP enables seamless interoperability between tools built in different languages (Rust, Python, Node.js) and across different platforms (IDE Hooks, CLI, Native Apps).

---

## The Three Rules of the Pipe

### 1. Standard I/O (The Stream)
Every tool in the pipe must support `stdin` for input and `stdout` for output. 
- **Upstream tools** (Ingestors) emit raw text or Markdown.
- **Middleware tools** (Filters/Sifters) process the stream.
- **Downstream tools** (Consumers) receive the refined signal.

### 2. The Native Execution Signature (The Bypass)
To prevent **Double-Sifting** (infinite loops or data destruction by reactive hooks), any tool that performs native context distillation MUST append the following signature to its output:
`--- [Semantic-Sift: Native Execution] ---`

When a "Blind Hook" (like Cursor or VS Code) sees this signature, it must instantly pass the data through without further modification.

### 3. Dynamic Discovery (Lazy Orchestration)
Orchestrators (like `semantic-sift`) should not force heavy dependencies. They should dynamically discover available "Upstream" nodes at runtime by checking the system `PATH` or local library registry.

---

## Integration Examples

### Tier 0: Terminal Piping (Manual)
Developers can manually stream tools to clean logs or summarize files.
```bash
# Extract code -> Summarize logic -> Save to file
serena get-body MyClass | sift-core semantic --rate 0.3 > summary.txt
```

### Tier 1: Subconscious Interception (The Hook)
The `pipe_hook.py` serves as the universal "Polyfill" for the pipe. It intercepts tools that don't natively support CPP and applies the distillation automatically.

### Tier 2: Native Adoption (High-Performance)
Tools like `context-mode` can integrate the pipe natively to bypass hook overhead and improve precision.

**Node.js Example (context-mode integration):**
```javascript
const { spawnSync } = require('child_process');

function searchAndStream(query) {
    const rawResults = performSearch(query);
    
    // Pipe results through the local Sift Sidecar
    const sifted = spawnSync('sift-core', ['logs'], { input: rawResults });
    
    // Return clean data with the Native Signature
    return sifted.stdout.toString() + "\n--- [Semantic-Sift: Native Execution] ---";
}
```

---

## Why Use the Context-Pipe?

1.  **Context Protection by Design**: Clean data at the source. Never flood the window.
2.  **Language Agnostic**: Connect a Rust search engine to a Python neural distiller via a Node.js agent.
3.  **Resource Efficiency**: Install one "Refinery" (`sift-core`) and use it across every tool on your machine.
4.  **Zero Bloat**: No need to bundle 1GB of PDF parsers in every tool; just pipe to a tool that already has them.

---
*Building High-Fidelity Infrastructure for the Studio of Two.*
