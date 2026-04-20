import os
import time
import json
import telemetry_core
from server import apply_heuristic_sieve

# Mock large noisy data for benchmarking
SCENARIOS = {
    "Vercel Build Logs": (
        "2026-04-19T20:30:01Z [1/534] Building...\n"
        "2026-04-19T20:30:02Z [2/534] Compiling components...\n"
        "2026-04-19T20:30:03Z [3/534] Resolving dependencies...\n"
        "  12.5 MB  node_modules/react/dist/index.js\n"
        "  500 bytes  .gitignore\n"
        "2026-04-19T20:30:05Z Build successful in 4.2s\n"
    ) * 50, # Inflate to make it a "Stress Test"
    
    "NPM Install Progress": (
        "npm install --save semantic-sift\n"
        "........................................\n"
        "added 124 packages in 5s\n"
        "34 packages are looking for funding\n"
        "run `npm fund` for details\n"
    ) * 100
}

def run_benchmark():
    print("==========================================")
    print("🚀 SEMANTIC-SIFT: PERFORMANCE BENCHMARK")
    print("==========================================")
    print()

    total_raw_tokens = 0
    total_sifted_tokens = 0

    for name, content in SCENARIOS.items():
        raw_len = len(content)
        raw_tokens = telemetry_core.estimate_tokens(content)
        
        start_t = time.time()
        sifted = apply_heuristic_sieve(content)
        latency = (time.time() - start_t) * 1000
        
        sifted_len = len(sifted)
        sifted_tokens = telemetry_core.estimate_tokens(sifted)
        
        total_raw_tokens += raw_tokens
        total_sifted_tokens += sifted_tokens

        savings_pct = (1 - (sifted_tokens / raw_tokens)) * 100 if raw_tokens > 0 else 0

        print(f"Scenario: {name}")
        print(f"- Raw: {raw_tokens:,} tokens ({raw_len:,} chars)")
        print(f"- Sifted: {sifted_tokens:,} tokens ({sifted_len:,} chars)")
        print(f"- 🚀 Reduction: {savings_pct:.1f}%")
        print(f"- Latency: {latency:.2f}ms")
        print()

        # Send Pulse to Global Registry (Tagged as Benchmark)
        telemetry_core.send_telemetry_pulse(
            tool_name=f"benchmark_{name.lower().replace(' ', '_')}",
            original=raw_len,
            final=sifted_len,
            latency=latency,
            tier_override="Benchmark"
        )

    print("==========================================")
    final_savings = (1 - (total_sifted_tokens / total_raw_tokens)) * 100 if total_raw_tokens > 0 else 0
    print(f"🏆 TOTAL BENCHMARK SAVINGS: {final_savings:.1f}%")
    print(f"📡 All data sent to registry with [Tier: Benchmark]")
    print("==========================================")

if __name__ == "__main__":
    run_benchmark()
