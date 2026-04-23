import os
import sys

# Ensure imports work from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sift_kernel
import server
import json
import asyncio

def test_load_file_content():
    print("Testing load_file_content...")
    # Test valid file
    content = sift_kernel.load_file_content("AGENTS.md")
    assert not content.startswith("Error"), f"Failed to load AGENTS.md: {content[:100]}"
    
    # Test invalid file
    content = sift_kernel.load_file_content("DOES_NOT_EXIST.md")
    assert content.startswith("Error: File not found at"), "Failed to return correct error for missing file."
    print("load_file_content OK.")

async def test_server_tools():
    print("Testing server tools...")
    
    # Create a dummy noisy file
    test_file = "test_noise.log"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("2026-04-22 10:00:00 INFO dfs.client: Starting process...\n" * 100)
        f.write("Critical failure occurred here.\n")
        f.write("2026-04-22 10:00:01 INFO dfs.client: Ending process...\n" * 100)

    try:
        # Test analyze
        analysis = await server.sift_analyze_file(test_file)
        assert "Context Analysis Report" in analysis
        assert "sift_read_file(type='logs')" in analysis or "sift_read_file" in analysis
        assert server.NATIVE_SIGNATURE in analysis

        # Test read
        sifted = await server.sift_read_file(test_file, type="logs")
        assert "Critical failure occurred here" in sifted
        assert "2026-04-22" not in sifted
        assert server.NATIVE_SIGNATURE in sifted

        print("server tools OK.")
    finally:
        os.remove(test_file)

def test_hook_exemption():
    print("Testing hook exemptions...")
    import subprocess
    hook_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sift_hook.py'))
    
    # Test Content Signature Bypass
    payload = {
        "result": "Some content\n" + server.NATIVE_SIGNATURE
    }
    process = subprocess.Popen([sys.executable, hook_script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = process.communicate(input=json.dumps(payload))
    assert "Distilled by Semantic-Sift" not in out # Should have bypassed
    
    # Test Structured Data Exemption
    payload2 = {
        "result": json.dumps({"key": "value " * 200}) # Large enough to trigger normally
    }
    process2 = subprocess.Popen([sys.executable, hook_script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out2, _ = process2.communicate(input=json.dumps(payload2))
    assert "Distilled by Semantic-Sift" not in out2 # Should have bypassed
    
    print("hook exemptions OK.")


if __name__ == "__main__":
    test_load_file_content()
    asyncio.run(test_server_tools())
    test_hook_exemption()
    print("All tests passed.")
