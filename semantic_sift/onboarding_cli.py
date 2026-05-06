# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import os
import sys
import argparse

from semantic_sift.onboarding import apply_onboarding
from semantic_sift.hook_injector import build_runtime_hook_command


def main():
    """Terminal CLI for running Semantic-Sift onboarding."""
    parser = argparse.ArgumentParser(description="Semantic-Sift: Automate project onboarding and hook configuration.")
    parser.add_argument("--env", help="Target environment (e.g., Gemini, Cursor, OpenCode, VSCode, Cline)")
    parser.add_argument("--dir", help="Target project directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Report planned actions without writing files")

    args = parser.parse_args()

    cwd = os.path.abspath(args.dir) if args.dir else os.getcwd()
    env = args.env or os.environ.get("SIFT_CLIENT_ID") or "Generic CLI"

    print("==========================================")
    print(" 🚀 Semantic-Sift: Project Onboarding")
    print("==========================================")
    print(f"Target Directory: {cwd}")
    print(f"Environment:      {env}")
    if args.dry_run:
        print("Mode:             DRY-RUN (No changes will be saved)")
    print("------------------------------------------")

    try:
        python_exe, hook_script, hook_cmd = build_runtime_hook_command()

        actions = apply_onboarding(
            environment=env,
            target_dir=cwd,
            dry_run=args.dry_run,
            runtime_python_exe=python_exe,
            runtime_hook_script=hook_script,
            runtime_hook_command=hook_cmd,
        )

        for action in actions:
            print(f"- {action}")

        print("------------------------------------------")
        if not args.dry_run:
            print("✅ Onboarding complete.")
        else:
            print("💡 Review the actions above. Run without --dry-run to apply.")

    except Exception as e:
        print(f"❌ Error during onboarding: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
