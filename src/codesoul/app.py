import sys
import asyncio
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, DirectoryTree, Input, Static, Label, Markdown
from textual.reactive import reactive

from .ingest import CodeScanner
from .db import VectorDB
from .rag import RagEngine

# --- TUI Components ---

class ChatMessage(Static):
    def __init__(self, content: str, role: str = "user"):
        super().__init__()
        self.content_text = content
        self.role = role

    def compose(self) -> ComposeResult:
        yield Markdown(self.content_text)

    def on_mount(self):
        if self.role == "user":
            self.add_class("user-message")
        else:
            self.add_class("ai-message")

class CodeSoulApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    .sidebar {
        width: 30%;
        dock: left;
        height: 100%;
        border-right: solid green;
    }

    .main-content {
        width: 70%;
        height: 100%;
        padding: 1;
    }

    #chat-history {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: scroll;
    }

    #chat-input {
        dock: bottom;
        margin-top: 1;
    }

    .user-message {
        background: $primary-darken-2;
        padding: 1;
        margin: 1;
        text-align: right;
    }

    .ai-message {
        background: $secondary-darken-2;
        padding: 1;
        margin: 1;
    }
    
    LoadingIndicator {
        height: auto;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_db", "Re-index"),
    ]

    status_message = reactive("Ready")
    
    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = str(Path(target_path).resolve())
        self.db = VectorDB()
        self.rag = RagEngine(self.db)
        self.scanner = CodeScanner(root_dir=self.target_path)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Vertical(
                Label(f"Explorer: {self.target_path}", classes="header-label"),
                DirectoryTree(self.target_path),
                classes="sidebar"
            ),
            Vertical(
                Label("CodeSoul Uplink", classes="header-label"),
                ScrollableContainer(id="chat-history"),
                Input(placeholder="Type your question to the spirit...", id="chat-input", disabled=True),
                classes="main-content"
            )
        )
        yield Footer()

    async def on_mount(self):
        self.title = f"CodeSoul - {Path(self.target_path).name}"
        self.run_worker(self.index_codebase(), name="indexing")

    async def index_codebase(self):
        """Background worker to index code."""
        chat = self.query_one("#chat-history")
        await chat.mount(ChatMessage(f"🔮 Awakening the spirits in '{self.target_path}'...", "ai"))
        
        try:
            # 1. Scan
            chunks = await self.scanner.ingest_all()
            await chat.mount(ChatMessage(f"📂 Found {len(chunks)} code fragments. Absorb them into the Void...", "ai"))
            
            # 2. Embed & Store
            if chunks:
                await self.db.add_chunks(chunks)
            
            # 3. Generate Persona
            await chat.mount(ChatMessage("🧠 Calibrating personality...", "ai"))
            persona = await self.rag.generate_persona()
            await chat.mount(ChatMessage(f"👻 **Soul Manifested**:\n\n{persona}", "ai"))
            
            # Enable Input
            self.query_one("#chat-input").disabled = False
            self.query_one("#chat-input").focus()
            
            self.status_message = "Connected to CodeSoul"
        except Exception as e:
             await chat.mount(ChatMessage(f"⚠️ Error initializing soul: {str(e)}", "ai"))

    async def on_input_submitted(self, event: Input.Submitted):
        query = event.value
        if not query:
            return
            
        input_widget = self.query_one("#chat-input")
        input_widget.value = ""
        
        chat = self.query_one("#chat-history")
        await chat.mount(ChatMessage(query, "user"))
        
        self.run_worker(self.handle_chat_response(query))

    async def handle_chat_response(self, query: str):
        chat = self.query_one("#chat-history")
        response_widget = ChatMessage("...", "ai")
        await chat.mount(response_widget)
        
        full_response = ""
        try:
            async for chunk in self.rag.chat(query):
                full_response += chunk
                response_widget.query_one(Markdown).update(full_response)
                chat.scroll_end()
        except Exception as e:
             response_widget.query_one(Markdown).update(f"Error communicating: {str(e)}")

# --- CLI Entry Point ---

def cli():
    """
    CodeSoul - The Codebase Spirit Medium
    Usage: codesoul [PATH]
    """
    path = "."
    if len(sys.argv) > 1:
        path = sys.argv[1]
    
    app = CodeSoulApp(target_path=path)
    app.run()

if __name__ == "__main__":
    cli()
