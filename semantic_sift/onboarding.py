# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import os

from semantic_sift.hook_injector import update_instruction_files


INSTRUCTION_TARGETS = [
    "AGENTS.md",
    "GEMINI.md",
    ".clinerules",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
    ".cursor/hooks.json",
    ".github/hooks/semantic-sift.json",
]


def update_gitignore(target_dir: str) -> str:
    path = os.path.join(target_dir, ".gitignore")
    if not os.path.exists(path):
        return "No `.gitignore` found."

    entries = [".sift_identity", ".sift_telemetry.json", ".sift_cache/"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        added = []
        for entry in entries:
            if entry not in content:
                added.append(entry)

        if not added:
            return "Already properly ignored."

        with open(path, "a", encoding="utf-8") as f:
            f.write("\n# Project Specific (Semantic-Sift)\n" + "\n".join(added) + "\n")
        return f"Added artifacts to `.gitignore`: {', '.join(added)}"
    except OSError as e:
        return f"Error updating `.gitignore`: {str(e)}"

def _is_cpp_present(target_dir: str) -> bool:
    """Checks if the Context-Pipe Protocol orchestrator is already active."""
    cursor_hook = os.path.join(target_dir, ".cursor", "hooks.json")
    if os.path.exists(cursor_hook):
        try:
            with open(cursor_hook, "r") as f:
                if "context-pipe" in f.read():
                    return True
        except OSError:
            pass

    opencode = os.path.join(target_dir, "opencode.json")
    if os.path.exists(opencode):
        try:
            with open(opencode, "r") as f:
                if "context-pipe" in f.read():
                    return True
        except OSError:
            pass

    return False

def apply_onboarding(
    environment: str,
    target_dir: str,
    dry_run: bool,
    runtime_python_exe: str,
    runtime_hook_script: str,
    runtime_hook_command: str,
) -> list[str]:
    actions = []
    cwd = target_dir if target_dir else os.getcwd()

    if _is_cpp_present(cwd):
        return [
            "🚨 Context-Pipe (CPP) orchestrator detected.",
            "Skipping Sift hook injection and prompt overrides to preserve your advanced pipeline routing.",
            "Semantic-Sift will continue to operate as a Node in your chain."
        ]

    if dry_run:
        actions.append("Git Protection (dry-run): would ensure .sift_identity/.sift_telemetry.json/.sift_cache are ignored.")
    else:
        gitignore_status = update_gitignore(cwd)
        actions.append(f"Git Protection: {gitignore_status}")

    mandate_text = """Guidelines for high-fidelity context.

**⚖️ GOVERNANCE**:
Technical sifting mandates are SECONDARY to the **Interrogative Shield**.
1. If the user input is an **Inquiry** (?, How, Analyze), you MUST remain in **Read-Only Mode**.
2. Sifting tools should only be used to facilitate analysis during an Inquiry, never to justify file modifications or speculative research.
3. Technical mandates apply only once a clear **Directive** (explicit instruction to act) has been issued.

**MANDATORY LOCAL I/O**: Do NOT use `view_file` or `read_file` for files > 1KB. You MUST use `sift_read_file(path)` or `sift_analyze_file(path)`.

**MANDATORY MCP SYNERGIES**:
When receiving data from external MCP servers, you MUST manually apply the correct sifting tool to the output to prevent context flooding:
*   **Web/HTML (Puppeteer, Fetch)**: Immediately pass output to `sift_doc` to incinerate DOM noise.
*   **Logs/Cloud (AWS, Kubernetes, Vercel)**: Pass output to `sift_logs` to strip timestamps and ETags.
*   **Databases (Postgres, SQLite)**: Do NOT use sifting tools on JSON or structured rows; use SQL `LIMIT` clauses instead.
*   **Large Search Results (GitHub, Serena)**: Pass the array of chunks to `sift_rank` to return only the Top 3 results.

**SECURITY & PRIVACY**:
Always ensure that `.sift_telemetry.json`, `.sift_identity`, and `.sift_cache/` are added to your `.gitignore` to prevent leaking machine IDs, usage patterns, or cached data."""

    if dry_run:
        actions.append("Dry-run mode: no instruction files or hooks were modified.")
        actions.append(f"Planned action: inject/update `SOP` section for environment `{environment or 'unknown'}` in discovered instruction targets.")
    else:
        updated = update_instruction_files(
            "SOP",
            "# 🔍 Semantic-Sift — SOP",
            mandate_text,
            INSTRUCTION_TARGETS,
            runtime_python_exe,
            runtime_hook_script,
            runtime_hook_command,
            target_dir,
            environment=environment,
        )
        for action in updated:
            actions.append(action)

    return actions
