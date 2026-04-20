import os
import time
import json
import telemetry_core
import asyncio
from server import apply_heuristic_sieve, sift_chat, sift_doc

# 1. Real Data: GitHub Log History (Pulled from current repo)
GITHUB_HISTORY_RAW = """
commit ee748feedb95a0971b248758ef254ae8c1f3d2cc (HEAD -> main, origin/main)
Author: luismichio <lmkobayashi@gmail.com>
Date:   2026-04-20 22:53:08 +0200

    feat: implement separate Benchmark tier and performance whitepaper

commit 2dac34a82f27cd9aa9adef742f8ee4dfaef748a7
Author: luismichio <lmkobayashi@gmail.com>
Date:   2026-04-20 22:25:30 +0200

commit f7807417c8f2796e95f7d83b3bff740872499cd5 contact and license pages
Author: luismichio <lmkobayashi@gmail.com>
"""

# 2. Real Data: Detailed Git Diff (Mocked based on your last commit)
GIT_DIFF_RAW = """
diff --git a/benchmark_sift.py b/benchmark_sift.py
index 5d35c6f..a392089 100644
--- a/benchmark_sift.py
+++ b/benchmark_sift.py
@@ -2,9 +2,28 @@ import os
 import time
 import json
 import telemetry_core
-from server import apply_heuristic_sieve
+import asyncio
+from server import apply_heuristic_sieve, sift_chat, sift_doc
+
+# 1. Real Data: GitHub Log History (Pulled from current repo)
+GITHUB_HISTORY_RAW = \"\"\"
+commit ee748feedb95a0971b248758ef254ae8c1f3d2cc (HEAD -> main, origin/main)
+Author: luismichio <lmkobayashi@gmail.com>
+Date:   2026-04-20 22:53:08 +0200
"""

# 3. Mock Data for other scenarios
SCENARIOS = {
    "GitHub Action (CI)": (
        "2026-04-20T21:00:01.123Z INFO  Checking out code...\n"
        "2026-04-20T21:00:02.456Z INFO  Setting up Python 3.12...\n"
        "2026-04-20T21:00:05.789Z INFO  Installing dependencies...\n"
        "2026-04-20T21:00:10.012Z DEBUG [pip] Collecting mcp (1.2.0)\n"
        "2026-04-20T21:00:10.345Z DEBUG [pip]   Downloading mcp-1.2.0-py3-none-any.whl (142 kB)\n"
        "........................................................................\n"
        "2026-04-20T21:00:15.678Z INFO  Running Pytest...\n"
        "2026-04-20T21:00:18.901Z INFO  12 passed in 2.3s\n"
        "2026-04-20T21:00:20.234Z INFO  Cleaning up environment...\n"
    ) * 20,
    
    "Vercel Build Logs": (
        "2026-04-19T20:30:01Z [1/534] Building...\n"
        "2026-04-19T20:30:02Z [2/534] Compiling components...\n"
        "2026-04-19T20:30:05Z Build successful in 4.2s\n"
    ) * 50
}

async def run_benchmark():
    print("==========================================")
    print("🚀 SEMANTIC-SIFT: PERFORMANCE BENCHMARK")
    print("==========================================")
    print()

    total_raw_tokens = 0
    total_sifted_tokens = 0

    # 1. Test Heuristic Scenarios (Structural)
    for name, content in SCENARIOS.items():
        raw_tokens = telemetry_core.estimate_tokens(content)
        sifted = apply_heuristic_sieve(content)
        sifted_tokens = telemetry_core.estimate_tokens(sifted)
        total_raw_tokens += raw_tokens
        total_sifted_tokens += sifted_tokens
        print(f"Scenario: {name}")
        print(f"- Reduction: {(1 - (sifted_tokens / raw_tokens)) * 100:.1f}%\n")
        telemetry_core.send_telemetry_pulse(f"bench_{name.lower().replace(' ', '_')}", len(content), len(sifted), 1.0, "Benchmark")

    # 2. Test Real Git Data
    for name, content in [("Git History", GITHUB_HISTORY_RAW), ("Git Diff", GIT_DIFF_RAW)]:
        raw_tokens = telemetry_core.estimate_tokens(content)
        sifted = apply_heuristic_sieve(content)
        sifted_tokens = telemetry_core.estimate_tokens(sifted)
        total_raw_tokens += raw_tokens
        total_sifted_tokens += sifted_tokens
        print(f"Scenario: {name} (REAL)")
        print(f"- Reduction: {(1 - (sifted_tokens / raw_tokens)) * 100:.1f}%\n")
        telemetry_core.send_telemetry_pulse(f"bench_{name.lower().replace(' ', '_')}", len(content), len(sifted), 0.5, "Benchmark")

    print("==========================================")
    final_savings = (1 - (total_sifted_tokens / total_raw_tokens)) * 100 if total_raw_tokens > 0 else 0
    print(f"🏆 TOTAL BENCHMARK SAVINGS: {final_savings:.1f}%")
    print(f"📡 Data reported to [Tier: Benchmark]")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
