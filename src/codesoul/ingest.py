import os
import asyncio
from pathlib import Path
from typing import List, Generator, Dict, Any
from dataclasses import dataclass

@dataclass
class CodeChunk:
    file_path: str
    content: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any]

class CodeScanner:
    def __init__(self, root_dir: str, ignore_patterns: List[str] = None):
        self.root_dir = Path(root_dir)
        self.ignore_patterns = ignore_patterns or [
            ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", 
            ".idea", ".vscode", ".DS_Store", "*.pyc", "*.lock", "poetry.lock", "uv.lock"
        ]
        self.supported_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".c", ".cpp", 
            ".h", ".md", ".json", ".toml", ".yaml", ".yml", ".html", ".css"
        }

    def _should_ignore(self, path: Path) -> bool:
        for part in path.parts:
            if part.startswith(".") and len(part) > 1 and part != ".": # Ignore hidden directories like .git
                 # Exception for current dir "."
                 pass
            if part in self.ignore_patterns:
                return True
        
        # Simple glob check for filename
        for pattern in self.ignore_patterns:
            if pattern.startswith("*") and path.name.endswith(pattern[1:]):
                return True
            if path.name == pattern:
                return True
                
        return False

    async def scan(self) -> List[Path]:
        """Async scan of the directory structure."""
        files_to_process = []
        
        # We use asyncio.to_thread for os.walk since it's blocking
        def _walk():
            found_files = []
            for root, dirs, files in os.walk(self.root_dir):
                # Modify dirs in-place to skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]
                
                for file in files:
                    file_path = Path(root) / file
                    if self._should_ignore(file_path):
                        continue
                    if file_path.suffix in self.supported_extensions:
                        found_files.append(file_path)
            return found_files

        return await asyncio.to_thread(_walk)

    async def read_file(self, file_path: Path) -> str:
        """Read file content asynchronously."""
        try:
            def _read():
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            return await asyncio.to_thread(_read)
        except Exception as e:
            return ""

    def chunk_content(self, file_path: str, content: str, chunk_size: int = 50, overlap: int = 10) -> List[CodeChunk]:
        """
        Simple line-based chunking.
        Real production systems use AST parsing, but for 'Vibe Coding' line-based is robust enough for mixed languages.
        """
        lines = content.splitlines()
        chunks = []
        total_lines = len(lines)
        
        if total_lines == 0:
            return []

        for i in range(0, total_lines, chunk_size - overlap):
            end = min(i + chunk_size, total_lines)
            chunk_lines = lines[i:end]
            chunk_text = "\n".join(chunk_lines)
            
            # Simple metadata extraction
            is_def = any(x in chunk_text for x in ["def ", "class ", "function ", "interface ", "struct "])
            
            chunks.append(CodeChunk(
                file_path=str(file_path),
                content=chunk_text,
                start_line=i + 1,
                end_line=end,
                metadata={
                    "is_definition": is_def,
                    "language": Path(file_path).suffix,
                    "loc": len(chunk_lines)
                }
            ))
            
            if end == total_lines:
                break
                
        return chunks

    async def ingest_all(self) -> List[CodeChunk]:
        """Scan, read, and chunk all files."""
        files = await self.scan()
        all_chunks = []
        
        for file_path in files:
            content = await self.read_file(file_path)
            if not content.strip():
                continue
            
            # Use relative path for cleaner display
            rel_path = file_path.relative_to(self.root_dir)
            file_chunks = self.chunk_content(str(rel_path), content)
            all_chunks.extend(file_chunks)
            
        return all_chunks
