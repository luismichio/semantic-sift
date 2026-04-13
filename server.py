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
async def sift_doc(text: str, budget_tokens: int = 1000) -> str:
    """
    Condenses long documents (MDX, PDF text) using a multi-stage approach:
    1. Heuristic Sieve (Removes structural noise)
    2. LLMLingua-2 Sift (Semantically prunes to the token budget)
    """
    # Stage 1: Structural cleaning
    cleaned = await sift_logs(text)
    
    # Stage 2: Calculate target rate if text is still too long
    # (Simplified: Target 50% compression or budget)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True
        )
        
        # We protect technical tokens to ensure we don't break code/entities
        results = compressor.compress_prompt(
            [cleaned],
            rate=0.4, # Target aggressive 60% reduction for long docs
            force_tokens=['[', ']', '{', '}', '/', '\\', '.', '_'], # Protect paths/JSON
            chunk_end_tokens=['\n', '.', ';'],
            return_word_label=False
        )
        return results.get('compressed_prompt', cleaned)
    except Exception as e:
        return f"Error during document sifting: {str(e)}"

@mcp.tool()
async def sift_extraction(content: str, source_type: str = "markdown") -> str:
    """
    Specifically designed to refine outputs from Docling or LiteParse.
    Removes extraction-specific noise (debris) and prunes dense technical docs
    for high-quality RAG indexing.
    """
    # 1. Targeted Document Debris Removal (Heuristic)
    # Remove common repeating patterns often found in OCR/Long PDF extractions
    # (e.g., repeating page numbers, copyright notices, headers)
    debris_patterns = [
        r'Page \d+ of \d+',
        r'© .*? All rights reserved',
        r'---+\s*$', # Empty separator lines
        r'^\s*·\s*$', # Single bullets on lines
    ]
    
    refined = content
    for pattern in debris_patterns:
        refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)

    # 2. Semantic Sift (Keep important signal)
    # For extractions, we want to be less aggressive than chat to keep technical accuracy
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True
        )
        
        results = compressor.compress_prompt(
            [refined],
            rate=0.7, # Keep 70% (gentle sift for indexing)
            force_tokens=['\n', '|', '-', ':', '#'], # Protect Markdown structure
            chunk_end_tokens=['\n', '.'],
            return_word_label=False
        )
        return results.get('compressed_prompt', refined)
    except Exception as e:
        return f"Error during extraction sifting: {str(e)}"

if __name__ == "__main__":
    mcp.run()
