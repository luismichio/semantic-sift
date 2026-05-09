# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import json
import os
import re
import sys


def build_runtime_hook_command() -> tuple[str, str, str]:
    python_exe = os.path.abspath(sys.executable)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Canonical hook script location (sift_hook.py root stub removed in v0.3.0)
    hook_script = os.path.abspath(os.path.join(repo_root, "semantic_sift", "hook.py"))
    if not os.path.exists(hook_script):
        raise RuntimeError(
            f"Semantic-Sift startup failed: hook script not found at '{hook_script}'. "
            "Ensure semantic_sift/hook.py is present in the installed package."
        )
    cmd_str = f'"{python_exe}" "{hook_script}"'
    return python_exe, hook_script, cmd_str


def get_windsurf_gateway_command() -> str:
    if sys.platform == "win32":
        return (
            'pwsh -NoProfile -Command "$p=$env:WINDSURF_TOOL_ARGS; '
            "if (Test-Path $p) { "
            "if ((Get-Item $p).Length -gt 1024) { "
            '[Console]::Error.WriteLine("[BLOCKED by Semantic-Sift] File > 1KB. Use sift_read_file instead."); '
            'exit 2 } }"'
        )

    return (
        'SIZE=$(stat -c %s "$WINDSURF_TOOL_ARGS" 2>/dev/null || stat -f %z "$WINDSURF_TOOL_ARGS" 2>/dev/null || wc -c < "$WINDSURF_TOOL_ARGS" 2>/dev/null); '
        'if [ "$SIZE" -gt 1024 ] 2>/dev/null; then '
        'echo "[BLOCKED by Semantic-Sift] File > 1KB. Use sift_read_file instead." > /dev/stderr; '
        "exit 2; fi"
    )


def discover_agent_configs(target_dir: str) -> list[str]:
    found_paths = []
    agent_dirs = [".codex/agents", ".cursor/agents", ".junie/agents", ".agents"]

    for d in agent_dirs:
        full_dir = os.path.join(target_dir, d)
        if os.path.exists(full_dir):
            for f in os.listdir(full_dir):
                if f.endswith((".toml", ".md")):
                    found_paths.append(os.path.join(full_dir, f))

    for root, _, files in os.walk(target_dir):
        depth = root[len(target_dir) :].count(os.sep)
        if depth > 3:
            continue
        if "AGENTS.md" in files and root != target_dir:
            found_paths.append(os.path.join(root, "AGENTS.md"))

    return found_paths


def update_toml_config(path: str, section_id: str, content: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            file_content = f.read()

        block_id = f"# SIFT_SECTION_START:{section_id}"
        block_end = f"# SIFT_SECTION_END:{section_id}"
        full_payload = f"\n{block_id}\n# ---\n# {content}\n{block_end}\n"

        pattern = re.compile(rf"{re.escape(block_id)}.*?{re.escape(block_end)}", re.DOTALL)
        if pattern.search(file_content):
            new_content = pattern.sub(full_payload.strip(), file_content)
        else:
            if "instructions =" in file_content:
                new_content = file_content.replace('instructions = """', f'instructions = """\n{content}\n')
            else:
                new_content = file_content + full_payload

        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(new_content)
        return True
    except (OSError, re.error):
        return False


def merge_hook_json(path: str, hook_key: str, new_hook: dict, version: int | None = None) -> bool:
    data: dict = {"hooks": {}}
    if version:
        data["version"] = version
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    if "hooks" not in data:
        data["hooks"] = {}
    hooks_list = data["hooks"].get(hook_key, [])

    exists = any(h.get("command") == new_hook.get("command") for h in hooks_list)
    if not exists:
        data["hooks"][hook_key] = [new_hook] + hooks_list
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    return False


def update_instruction_files(
    section_id: str,
    header: str,
    content: str,
    instruction_targets: list[str],
    runtime_python_exe: str,
    runtime_hook_script: str,
    runtime_hook_command: str,
    target_dir: str | None = None,
    environment: str | None = None,
) -> list[str]:
    actions = []
    cwd = target_dir if target_dir else os.getcwd()
    python_exe = runtime_python_exe
    hook_script = runtime_hook_script
    cmd_str = runtime_hook_command
    block_id = f"<!-- SIFT_SECTION_START:{section_id} -->"
    block_end = f"<!-- SIFT_SECTION_END:{section_id} -->"
    full_payload = f"\n{block_id}\n---\n\n{header}\n{content}\n{block_end}\n"

    env_lower = environment.lower() if environment else ""

    targets = instruction_targets[:]
    subagent_paths = discover_agent_configs(cwd)
    targets.extend(subagent_paths)

    for target in targets:
        target_path = target if os.path.isabs(target) else os.path.join(cwd, target)
        if os.path.exists(target_path):
            try:
                filename = os.path.basename(target_path)

                if target_path.endswith(".toml"):
                    if update_toml_config(target_path, section_id, content):
                        actions.append(f"Shielded subagent config: `{filename}`.")
                    continue

                if not filename.endswith((".md", ".clinerules", ".cursorrules", ".windsurfrules")):
                    continue

                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    file_content = f.read()

                if any(
                    x in file_content.lower()
                    for x in ["always use view_file", "read the full file", "read entire file"]
                ):
                    actions.append(
                        f"⚠️ WARNING: Found potentially contradictory 'read full file' instructions in `{filename}`. The Sift Mandate override has been appended."
                    )

                pattern = re.compile(rf"{re.escape(block_id)}.*?{re.escape(block_end)}", re.DOTALL)
                if pattern.search(file_content):
                    new_content = pattern.sub(full_payload.strip(), file_content)
                    with open(target_path, "w", encoding="utf-8", errors="replace") as f:
                        f.write(new_content)
                    actions.append(f"Updated `{filename}`.")
                else:
                    with open(target_path, "a", encoding="utf-8", errors="replace") as f:
                        f.write(full_payload)
                    actions.append(f"Injected into `{filename}`.")
            except (OSError, re.error) as e:
                actions.append(f"Error updating `{target_path}`: {str(e)}")

    if "cursor" in env_lower:
        cursor_path = os.path.join(cwd, ".cursor", "hooks.json")
        os.makedirs(os.path.dirname(cursor_path), exist_ok=True)

        if os.path.exists(cursor_path):
            try:
                with open(cursor_path, "r", encoding="utf-8") as f:
                    cursor_data = json.load(f)
                if "hooks" in cursor_data and "beforeMCPExecution" in cursor_data["hooks"]:
                    actions.append(
                        "🚨 ALERT: `beforeMCPExecution` security gateway detected in Cursor hooks. You MUST whitelist `sift_read_file` and `sift_analyze_file` or they will be blocked."
                    )
            except (OSError, json.JSONDecodeError):
                pass

        if merge_hook_json(cursor_path, "postToolUse", {"command": cmd_str}, version=1):
            actions.append("Merged into Cursor hooks.")

    if "vscode" in env_lower or "github" in env_lower:
        vscode_path = os.path.join(cwd, ".github", "hooks", "semantic-sift.json")
        os.makedirs(os.path.dirname(vscode_path), exist_ok=True)
        if merge_hook_json(vscode_path, "PostToolUse", {"type": "command", "command": cmd_str}):
            actions.append("Merged into VS Code hooks.")

    if "gemini" in env_lower:
        gemini_commands_dir = os.path.join(cwd, ".gemini", "commands")
        os.makedirs(gemini_commands_dir, exist_ok=True)
        gemini_command_path = os.path.join(gemini_commands_dir, "sift-stats.toml")

        gemini_command_content = """description = "View Semantic-Sift token savings and telemetry dashboard"
prompt = \"\"\"
!{semantic-sift-stats}
\"\"\"
"""
        if not os.path.exists(gemini_command_path):
            try:
                with open(gemini_command_path, "w", encoding="utf-8") as f:
                    f.write(gemini_command_content)
                actions.append("Injected `/sift-stats` custom command into Gemini CLI.")
            except OSError as e:
                actions.append(f"Error configuring Gemini CLI command: {str(e)}")

    if "opencode" in env_lower:
        opencode_plugin_path = os.path.join(cwd, ".opencode", "plugins", "semantic-sift.ts")
        os.makedirs(os.path.dirname(opencode_plugin_path), exist_ok=True)
        plugin_content = f"""/**
 * Semantic-Sift Native OpenCode Plugin
 */
export const SemanticSiftPlugin = async ({{ $ }}) => {{
  return {{
    hooks: {{
      "tool.execute.after": async (input, output) => {{
        const rawContent = output.result;
        if (typeof rawContent !== 'string' || rawContent.length < 500) return;
        if (rawContent.includes("--- [Semantic-Sift: Native Execution] ---")) return;
        try {{
          const pythonExe = "{python_exe}";
          const siftScript = "{hook_script}";
          const payload = {{ hook_event_name: "AfterTool", tool_name: input.tool, tool_args: input.args, tool_response: {{ llmContent: rawContent }} }};
          const response = await $`${{pythonExe}} ${{siftScript}}`.input(JSON.stringify(payload)).text();
          const siftedData = JSON.parse(response);
          if (siftedData?.tool_response?.llmContent) output.result = siftedData.tool_response.llmContent;
        }} catch (error) {{ console.error("[Semantic-Sift Plugin] failed:", error); }}
      }}
    }}
  }};
}};
export default SemanticSiftPlugin;
"""
        try:
            if not os.path.exists(opencode_plugin_path):
                with open(opencode_plugin_path, "w", encoding="utf-8") as f:
                    f.write(plugin_content)
                actions.append("Configured OpenCode native plugin.")
        except OSError as e:
            actions.append(f"Error configuring OpenCode plugin: {str(e)}")

        opencode_config_path = os.path.join(cwd, "opencode.json")
        if os.path.exists(opencode_config_path):
            try:
                with open(opencode_config_path, "r", encoding="utf-8") as f:
                    opencode_config = json.load(f)

                if "commands" not in opencode_config:
                    opencode_config["commands"] = {}

                if "/sift-onboard" not in opencode_config["commands"]:
                    opencode_config["commands"]["/sift-onboard"] = {
                        "description": "Initialize Semantic-Sift in this project",
                        "action": "run_mcp_tool",
                        "server": "semantic-sift",
                        "tool": "sift_onboard",
                        "args": {"environment": "OpenCode"},
                    }

                if "/sift-stats" not in opencode_config["commands"]:
                    opencode_config["commands"]["/sift-stats"] = {
                        "description": "View Semantic-Sift token savings and telemetry dashboard",
                        "action": "run_mcp_tool",
                        "server": "semantic-sift",
                        "tool": "get_sift_stats",
                        "args": {"scope": "all"},
                    }
                    with open(opencode_config_path, "w", encoding="utf-8") as f:
                        json.dump(opencode_config, f, indent=2)
                    actions.append("Injected `/sift-stats` command into opencode.json.")
            except (OSError, json.JSONDecodeError) as e:
                actions.append(f"Error updating opencode.json commands: {str(e)}")

    if "claude" in env_lower:
        claude_paths = [
            os.path.join(os.path.expanduser("~"), ".claude", "settings.json"),
            os.path.join(cwd, ".claude", "settings.json"),
        ]
        for c_path in claude_paths:
            if os.path.exists(c_path):
                try:
                    with open(c_path, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    c_data = {}

                if "hooks" not in c_data:
                    c_data["hooks"] = {}
                if "PostToolUse" not in c_data["hooks"]:
                    c_data["hooks"]["PostToolUse"] = []

                exists = False
                for pt_hook in c_data["hooks"]["PostToolUse"]:
                    if pt_hook.get("matcher") == "mcp__.*__.*":
                        for inner_hook in pt_hook.get("hooks", []):
                            if inner_hook.get("command") == cmd_str:
                                exists = True
                                break

                if not exists:
                    claude_hook = {
                        "matcher": "mcp__.*__.*",
                        "hooks": [{"type": "command", "command": cmd_str}],
                    }
                    c_data["hooks"]["PostToolUse"] = [claude_hook] + c_data["hooks"]["PostToolUse"]
                    try:
                        with open(c_path, "w", encoding="utf-8") as f:
                            json.dump(c_data, f, indent=2)
                        actions.append(f"Merged into Claude Code hooks at {c_path}.")
                    except OSError as e:
                        actions.append(f"Failed to merge Claude Code hooks: {e}")

    if "qwen" in env_lower:
        qwen_paths = [
            os.path.join(os.path.expanduser("~"), ".qwen", "settings.json"),
            os.path.join(cwd, ".qwen", "settings.json"),
        ]
        for q_path in qwen_paths:
            if os.path.exists(q_path):
                try:
                    with open(q_path, "r", encoding="utf-8") as f:
                        q_data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    q_data = {}

                if "hooks" not in q_data:
                    q_data["hooks"] = {}
                if "PostToolUse" not in q_data["hooks"]:
                    q_data["hooks"]["PostToolUse"] = []

                exists = False
                for pt_hook in q_data["hooks"]["PostToolUse"]:
                    if pt_hook.get("matcher") == "mcp__.*__.*":
                        for inner_hook in pt_hook.get("hooks", []):
                            if inner_hook.get("command") == cmd_str:
                                exists = True
                                break
                if not exists:
                    qwen_hook = {
                        "matcher": "mcp__.*__.*",
                        "hooks": [{"type": "command", "command": cmd_str}],
                    }
                    q_data["hooks"]["PostToolUse"] = [qwen_hook] + q_data["hooks"]["PostToolUse"]
                    try:
                        with open(q_path, "w", encoding="utf-8") as f:
                            json.dump(q_data, f, indent=2)
                        actions.append(f"Merged into Qwen CLI hooks at {q_path}.")
                    except OSError as e:
                        actions.append(f"Failed to merge Qwen CLI hooks: {e}")

    if "windsurf" in env_lower:
        windsurf_paths = [
            os.path.join(os.path.expanduser("~"), ".codeium", "windsurf", "hooks.json"),
            os.path.join(cwd, ".windsurf", "hooks.json"),
        ]
        for w_path in windsurf_paths:
            if os.path.exists(w_path):
                try:
                    with open(w_path, "r", encoding="utf-8") as f:
                        w_data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    w_data = {}
                if "pre_mcp_tool_use" not in w_data:
                    w_data["pre_mcp_tool_use"] = []

                gateway_cmd = get_windsurf_gateway_command()

                exists = any(h.get("command") == gateway_cmd for h in w_data["pre_mcp_tool_use"])
                if not exists:
                    w_data["pre_mcp_tool_use"].insert(
                        0,
                        {
                            "matcher": "mcp__.*__(read_file|view_file)",
                            "type": "command",
                            "command": gateway_cmd,
                        },
                    )
                    try:
                        with open(w_path, "w", encoding="utf-8") as f:
                            json.dump(w_data, f, indent=2)
                        actions.append(f"Injected Security Gateway into Windsurf hooks at {w_path}.")
                    except OSError as e:
                        actions.append(f"Failed to merge Windsurf hooks: {e}")

    if "openclaw" in env_lower:
        openclaw_plugin_path = os.path.join(cwd, ".openclaw", "plugins", "semantic-sift.ts")
        os.makedirs(os.path.dirname(openclaw_plugin_path), exist_ok=True)
        openclaw_plugin_content = f"""/**
 * Semantic-Sift Native OpenClaw Plugin
 */
export default function (api) {{
  api.on("tool:after", async (event, ctx) => {{
    const rawContent = ctx.result;
    if (typeof rawContent !== 'string' || rawContent.length < 500) return;
    if (rawContent.includes("--- [Semantic-Sift: Native Execution] ---")) return;
    try {{
      const pythonExe = "{python_exe}";
      const siftScript = "{hook_script}";
      const payload = {{ hook_event_name: "AfterTool", tool_name: ctx.toolName, tool_response: {{ llmContent: rawContent }} }};

      // Execute Python interceptor
      const {{ execSync }} = require('child_process');
      const response = execSync(`${{pythonExe}} ${{siftScript}}`, {{ input: JSON.stringify(payload), encoding: 'utf-8' }});

      const siftedData = JSON.parse(response);
      if (siftedData?.tool_response?.llmContent) {{
         ctx.result = siftedData.tool_response.llmContent;
      }}
    }} catch (error) {{ console.error("[Semantic-Sift Plugin] failed:", error); }}
  }});
}};
"""
        try:
            if not os.path.exists(openclaw_plugin_path):
                with open(openclaw_plugin_path, "w", encoding="utf-8") as f:
                    f.write(openclaw_plugin_content)
                actions.append("Configured OpenClaw native plugin.")
        except OSError as e:
            actions.append(f"Error configuring OpenClaw plugin: {str(e)}")

    if "kilocode" in env_lower:
        kilo_rule_dir = os.path.join(cwd, ".kilocode", "rules")
        os.makedirs(kilo_rule_dir, exist_ok=True)
        kilo_rule_path = os.path.join(kilo_rule_dir, "context.md")
        if not os.path.exists(kilo_rule_path):
            try:
                with open(kilo_rule_path, "w", encoding="utf-8") as f:
                    f.write(f"# Semantic-Sift Kilo Code Constraints\n\n{content}")
                actions.append("Injected Kilo Code workspace rules.")
            except OSError as e:
                actions.append(f"Error configuring Kilo Code rules: {str(e)}")

    if "cline" in env_lower or "roo" in env_lower:
        cline_hooks_dir = os.path.join(cwd, ".clinerules", "hooks")
        os.makedirs(cline_hooks_dir, exist_ok=True)

        cline_ps1_path = os.path.join(cline_hooks_dir, "PreToolUse.ps1")
        cline_ps1_content = """$inputJson = $input | ConvertFrom-Json
if ($inputJson.preToolUse.toolName -eq 'read_file' -or $inputJson.preToolUse.toolName -eq 'view_file') {
    $filePath = $inputJson.preToolUse.parameters.path
    if (Test-Path $filePath) {
        $size = (Get-Item $filePath).Length
        if ($size -gt 1024) {
            $response = @{ cancel = $true; errorMessage = "[BLOCKED by Semantic-Sift] File > 1KB. Use sift_read_file instead." }
            $response | ConvertTo-Json -Compress | Write-Output
            exit 0
        }
    }
}
$response = @{ cancel = $false }
$response | ConvertTo-Json -Compress | Write-Output
"""
        if not os.path.exists(cline_ps1_path):
            try:
                with open(cline_ps1_path, "w", encoding="utf-8") as f:
                    f.write(cline_ps1_content)
                actions.append("Injected Cline PreToolUse.ps1 hook.")
            except OSError as e:
                actions.append(f"Error configuring Cline PS1 hook: {str(e)}")

        cline_bash_path = os.path.join(cline_hooks_dir, "PreToolUse")
        cline_bash_content = """#!/bin/bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | grep -oP '(?<="toolName":")[^"]*')
if [[ "$TOOL_NAME" == "read_file" ]] || [[ "$TOOL_NAME" == "view_file" ]]; then
    FILE_PATH=$(echo "$INPUT" | grep -oP '(?<="path":")[^"]*')
    if [[ -f "$FILE_PATH" ]]; then
        SIZE=$(wc -c < "$FILE_PATH" 2>/dev/null || stat -f %s "$FILE_PATH" 2>/dev/null || stat -c %s "$FILE_PATH" 2>/dev/null)
        if [[ "$SIZE" -gt 1024 ]]; then
            echo '{"cancel": true, "errorMessage": "[BLOCKED by Semantic-Sift] File > 1KB. Use sift_read_file instead."}'
            exit 0
        fi
    fi
fi
echo '{"cancel": false}'
"""
        if not os.path.exists(cline_bash_path):
            try:
                with open(cline_bash_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(cline_bash_content)
                os.chmod(cline_bash_path, 0o755)  # nosec B103 — hook script must be executable
                actions.append("Injected Cline PreToolUse bash hook.")
            except OSError as e:
                actions.append(f"Error configuring Cline bash hook: {str(e)}")

    if "codex" in env_lower:
        codex_paths = [
            os.path.join(os.path.expanduser("~"), ".codex", "settings.json"),
            os.path.join(cwd, ".codex", "settings.json"),
        ]
        for co_path in codex_paths:
            if os.path.exists(co_path):
                try:
                    with open(co_path, "r", encoding="utf-8") as f:
                        co_data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    co_data = {}

                if "hooks" not in co_data:
                    co_data["hooks"] = {}
                if "PostToolUse" not in co_data["hooks"]:
                    co_data["hooks"]["PostToolUse"] = []

                exists = False
                for pt_hook in co_data["hooks"]["PostToolUse"]:
                    if pt_hook.get("matcher") == "mcp__.*__.*":
                        for inner_hook in pt_hook.get("hooks", []):
                            if inner_hook.get("command") == cmd_str:
                                exists = True
                                break
                if not exists:
                    codex_hook = {
                        "matcher": "mcp__.*__.*",
                        "hooks": [{"type": "command", "command": cmd_str}],
                    }
                    co_data["hooks"]["PostToolUse"] = [codex_hook] + co_data["hooks"]["PostToolUse"]
                    try:
                        with open(co_path, "w", encoding="utf-8") as f:
                            json.dump(co_data, f, indent=2)
                        actions.append(f"Merged into Codex CLI hooks at {co_path}.")
                    except OSError as e:
                        actions.append(f"Failed to merge Codex CLI hooks: {e}")

    return actions
