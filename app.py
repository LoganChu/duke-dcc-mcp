#!/usr/bin/env python3
"""
textual_chat.py
A simple Textual-based terminal chat app with a pluggable async backend.

Install:
    pip install textual rich aiohttp

To run:
    python textual_chat.py
"""

import asyncio
from typing import AsyncIterator, List, Dict, Optional

from rich.markdown import Markdown
from rich.panel import Panel
from rich.align import Align

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Input, Button, Static
from textual.widgets.scroll_view import ScrollView
from textual.reactive import reactive

# -------------------------
# Replace / implement this
# -------------------------
# send_prompt should be an async function that either:
#  - returns the assistant text as a single string
#  - or yields partial strings (async generator) for streaming output
#
# Example included below shows a fake streaming generator for demo.
#
async def fake_streaming_backend(prompt: str, history: List[Dict]) -> AsyncIterator[str]:
    """
    Demo: an async generator that yields chunks of reply (simulates streaming).
    Replace with actual integration:
      - OpenAI streaming via SSE / websocket
      - Hugging Face streaming endpoints
      - Local llama.cpp wrapper that yields tokens
    """
    reply = "Sure — I can help with that. Here's a short example reply that streams."
    # simulate streaming by splitting into words
    for w in reply.split():
        await asyncio.sleep(0.06)
        yield (w + " ")
    # final newline
    yield "\n"

# If you prefer to return a single string instead of streaming:
async def fake_single_response(prompt: str, history: List[Dict]) -> str:
    await asyncio.sleep(0.5)
    return "This is a single-shot response from the fake backend."

# ---------------------------------
# UI widgets & helper functions
# ---------------------------------
class MessageBubble(Static):
    """A simple message bubble that renders markdown inside a Panel."""
    def __init__(self, who: str, content: str, *, id: Optional[str] = None) -> None:
        super().__init__(id=id)
        self.who = who
        self.content = content

    def render(self):
        # Left-align user, right-align assistant
        title = "[cyan]You[/cyan]" if self.who == "user" else "[magenta]Assistant[/magenta]"
        body = Markdown(self.content or "_(no content)_")
        align = "left" if self.who == "user" else "right"
        p = Panel(
            Align(body, align=align),
            title=title,
            padding=(1, 1),
            expand=False,
            border_style="cyan" if self.who == "user" else "magenta",
        )
        return p

class MessagesView(ScrollView):
    """ScrollView collecting message bubbles."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: List[Dict] = []

    async def add_message(self, who: str, content: str):
        self.messages.append({"role": who, "content": content})
        bubble = MessageBubble(who, content)
        await self.mount(bubble)
        # auto-scroll to bottom
        await self.scroll_end(animate=False)

    async def update_last_message(self, who: str, content: str):
        """Replace the content of the last message that matches 'who'."""
        # naive approach: update last child widget's .update() using new Panel
        if not self.children:
            return
        last_widget = list(self.children)[-1]
        if isinstance(last_widget, MessageBubble):
            last_widget.content = content
            last_widget.refresh(layout=True)
            await self.scroll_end(animate=False)

# -------------------------
# Main App
# -------------------------
class ChatApp(App):
    CSS_PATH = None
    BINDINGS = [("ctrl+c", "quit", "Quit"), ("escape", "quit", "Quit"), ("ctrl+l", "clear", "Clear")]

    status = reactive("idle")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False, tall=False)
        with Container():
            with Vertical():
                self.messages = MessagesView(id="messages")
                yield self.messages
                # Input area
                input_row = Container(id="input_row")
                self.input = Input(placeholder="Type a message and press Enter...", id="chat_input")
                yield self.input
                yield Footer()

    async def on_mount(self) -> None:
        # focus the input on start
        await self.set_focus(self.input)
        # initial system message (optional)
        await self.messages.add_message("assistant", "Hello! I'm your terminal assistant. Type something to begin.")

    async def action_clear(self) -> None:
        # clears messages
        await self.messages.clear()
        self.messages.messages = []
        await self.messages.add_message("assistant", "Chat cleared. Say hi!")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
        # append user message
        await self.messages.add_message("user", user_text)
        self.input.value = ""  # clear input while processing
        await self.set_focus(self.input)
        # build simple history for backend (list of role/content)
        history = self.messages.messages.copy()

        # Start streaming response: add an empty assistant message then update it progressively
        await self.messages.add_message("assistant", "")  # placeholder
        self.status = "thinking"

        # Replace this with: backend = your_send_prompt(...) either streaming or single-shot
        # We detect if the backend returns an async iterator (streaming) or a single string.
        try:
            backend = fake_streaming_backend  # <-- swap to your real backend here
            result = backend(user_text, history)
            # If result is an async iterator, stream chunks
            if hasattr(result, "__aiter__"):
                # accumulate as we stream
                acc = ""
                async for chunk in result:
                    acc += chunk
                    # live update
                    await self.messages.update_last_message("assistant", acc)
                # final update ensured
                await self.messages.update_last_message("assistant", acc)
            else:
                # non-async-iterator: await single-shot
                text = await result
                await self.messages.update_last_message("assistant", text)
        except Exception as e:
            await self.messages.update_last_message("assistant", f"**Error:** {e}")
        finally:
            self.status = "idle"
            await self.set_focus(self.input)

    # nice tiny status in the title bar (optional)
    def watch_status(self, status: str) -> None:
        self.title = f"Textual Chat — {status}"

if __name__ == "__main__":
    ChatApp.run()
