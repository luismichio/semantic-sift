# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import json
import os
import sys

from telemetry_core import TELEMETRY_FILE, SIFT_CLIENT_ID, SIFT_TIER, SIFT_TELEMETRY_DISABLED

def main():
    """Terminal CLI for viewing Sift telemetry stats."""
    if SIFT_TELEMETRY_DISABLED:
        print("--- Semantic-Sift Telemetry ---")
        print("Status: DISABLED (Privacy Mode)")
        print(f"\n[Identity: {SIFT_CLIENT_ID} | Tier: {SIFT_TIER}]")
        sys.exit(0)

    if not os.path.exists(TELEMETRY_FILE):
        print("--- Semantic-Sift Telemetry ---")
        print("No activity recorded yet.")
        print(f"\n[Identity: {SIFT_CLIENT_ID} | Tier: {SIFT_TIER}]")
        sys.exit(0)

    try:
        with open(TELEMETRY_FILE, "r") as f:
            data = json.load(f)

        total_calls = total_orig_chars = total_final_chars = total_orig_tokens = total_final_tokens = total_lat = total_hits = 0
        breakdown = {}

        for session_id, session in data.items():
            for tool, stats in session.get("tools", {}).items():
                c = stats.get("calls", 0)
                oc = stats.get("original_chars", 0)
                fc = stats.get("final_chars", 0)
                ot = stats.get("original_tokens", 0)
                ft = stats.get("final_tokens", 0)
                lat = stats.get("total_latency_ms", 0)
                h = stats.get("cache_hits", 0)
                
                total_calls += c
                total_orig_chars += oc
                total_final_chars += fc
                total_orig_tokens += ot
                total_final_tokens += ft
                total_lat += lat
                total_hits += h
                
                if tool not in breakdown:
                    breakdown[tool] = {"calls": 0, "chars_saved": 0, "tokens_saved": 0, "cache_hits": 0}
                
                breakdown[tool]["calls"] += c
                breakdown[tool]["chars_saved"] += oc - fc
                breakdown[tool]["tokens_saved"] += ot - ft
                breakdown[tool]["cache_hits"] += h

        tokens_saved = total_orig_tokens - total_final_tokens
        
        print("==========================================")
        print(" 📊 Semantic-Sift: Global Dashboard")
        print("==========================================")
        print(f"Identity: {SIFT_CLIENT_ID} (Tier: {SIFT_TIER})")
        print(f"Tool Calls: {total_calls}")
        print(f"Tokens Processed: {total_orig_tokens:,}")
        
        savings_pct = (tokens_saved / total_orig_tokens * 100) if total_orig_tokens > 0 else 0
        print(f"Tokens Saved: {tokens_saved:,} ({savings_pct:.1f}%)")
        
        avg_lat = (total_lat / total_calls) if total_calls > 0 else 0
        print(f"Avg Latency: {avg_lat:.1f}ms")
        
        hit_pct = (total_hits / total_calls * 100) if total_calls > 0 else 0
        print(f"Cache Hits: {total_hits} ({hit_pct:.1f}%)")
        print("==========================================")
        print("Breakdown by Tool:")
        for tool, s in sorted(breakdown.items(), key=lambda item: item[1]["tokens_saved"], reverse=True):
            print(f"  - {tool}: {s['calls']} calls, {s['tokens_saved']:,} tokens saved ({s['cache_hits']} hits)")
            
    except Exception as e:
        print(f"Error reading telemetry: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
