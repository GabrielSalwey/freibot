"""
Freibot Chainlit App — Frontend-only client to the Freibot API.
- Calls API /ask over HTTP
- Simulates streaming by chunking the final answer
- Supports privacy mode toggle (no logging on API)
"""

import os
import time
import requests
import chainlit as cl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = os.getenv("FREIBOT_API_BASE", "http://localhost:8001")

@cl.on_chat_start
async def start():
    """Initialize chat session and show API status."""
    cl.user_session.set("session_id", f"cl_{int(time.time())}")
    cl.user_session.set("privacy_mode", False)

    # Check API status
    try:
        h = requests.get(f"{API_BASE}/health", timeout=5)
        s = requests.get(f"{API_BASE}/stats", timeout=5)
        status = h.json() if h.ok else {"status": "unknown"}
        stats = s.json() if s.ok else {}
        await cl.Message(
            content=(
                f"🔌 API: {status.get('status', 'unknown')} | "
                f"Docs: {stats.get('chunk_count', '?')} | "
                f"Model: {stats.get('llm_model', '?')}\n\n"
                "Stellen Sie Ihre Frage – ich nutze die API im Hintergrund."
            )
        ).send()
    except Exception as e:
        await cl.Message(content=f"❌ API nicht erreichbar: {e}").send()

    # Chat settings UI (Privacy Mode toggle)
    await cl.ChatSettings([
        cl.input_widget.Switch(
            id="Privacy Mode",
            label="Privatmodus",
            initial=False,
            description="Deaktiviert Protokollierung auf API-Seite"
        )
    ]).send()

@cl.on_settings_update
async def on_settings(settings):
    """Update privacy mode from settings."""
    cl.user_session.set("privacy_mode", settings.get("Privacy Mode", False))

@cl.on_message
async def on_message(message: cl.Message):
    """Forward user message to the API and simulate streaming of the response."""
    payload = {
        "question": message.content,
        "session_id": cl.user_session.get("session_id"),
        "privacy_mode": cl.user_session.get("privacy_mode", False)
    }

    msg = cl.Message(content="")
    await msg.send()

    try:
        r = requests.post(f"{API_BASE}/ask", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        answer = data.get("answer", "")

        # Simulate streaming by chunking the final answer
        chunk_size = 300
        for i in range(0, len(answer), chunk_size):
            await msg.stream_token(answer[i:i+chunk_size])

        # Append sources if present
        sources = data.get("sources", [])
        if sources:
            await msg.stream_token("\n\nQuellen:\n")
            for s in sources:
                label = s.get("document", "Unbekannt")
                page = s.get("page")
                await msg.stream_token(f"- {label}{' (S.' + str(page) + ')' if page else ''}\n")

        await msg.update()
    except Exception as e:
        await cl.Message(content=f"❌ Fehler: {e}").send()

@cl.author_rename
def rename(orig_author: str):
    if orig_author == "Assistant":
        return "Freibot"
    return orig_author

if __name__ == "__main__":
    cl.run()
