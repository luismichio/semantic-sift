import re
import os
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Semantic-Sift")

@mcp.tool()
async def sift_logs(raw_text: str) -> str:
    """
    Sifts through raw technical logs (Vercel, GitHub, Console) 
    to remove noise and keep only the instructional signal.
    """
    lines = raw_text.splitlines()
    sifted = []
    
    # Common noise patterns to remove
    # 1. Timestamps (e.g., 2026-04-13T02:18:19Z)
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?\s*')
    
    # 2. Progress bars or repetitive build status lines
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')

    # 3. Webpacker/Vite successful module listings (too noisy)
    module_pattern = re.compile(r'^\s*[\d\.]+\s+[\w\-\.\/]+\s+\d+\s+bytes.*$')

    for line in lines:
        # Clean timestamp
        clean_line = timestamp_pattern.sub('', line).strip()
        
        # Skip if empty or matches noise
        if not clean_line:
            continue
        if progress_pattern.search(clean_line):
            continue
        if module_pattern.match(clean_line):
            continue
            
        sifted.append(clean_line)
        
    return "\n".join(sifted)

@mcp.tool()
async def sift_chat(text: str, rate: float = 0.5) -> str:
    """
    Semantically prunes conversation history using LLMLingua-2.
    Preserves instructions while stripping verbal filler.
    """
    try:
        from llmlingua import PromptCompressor
        
        # Initialize compressor with LLMLingua-2 model
        # The first run will download the model (~300MB)
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True
        )
        
        # Perform compression
        results = compressor.compress_prompt(
            [text],
            rate=rate,
            force_tokens=['\n', '?'], # Protect structure and questions
            chunk_end_tokens=['.', '\n'],
            return_word_label=False
        )
        
        return results.get('compressed_prompt', text)
    except Exception as e:
        return f"Error during semantic sifting: {str(e)}"

@mcp.tool()
async def sift_doc(text: str, focus: str = "general") -> str:
    """
    Condenses long documents (MDX, PDF text) while preserving 
    technical structure and key entities.
    """
    # Hybrid strategy: Log-style structural cleaning + Semantic chat pruning
    cleaned = await sift_logs(text)
    compressed = await sift_chat(cleaned, rate=0.4)
    return compressed

if __name__ == "__main__":
    mcp.run()
