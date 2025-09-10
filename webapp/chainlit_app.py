"""
Freibot Chainlit App - Simplified RAG system with streaming responses
"""

import os
import json
from pathlib import Path
import chainlit as cl
from dotenv import load_dotenv
import tiktoken

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.embedders.voyage_embedders import VoyageTextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.utils.auth import Secret

# Load environment variables
load_dotenv()

# Configuration
VOYAGE_MODEL = "voyage-3-large"
LLM_MODEL = "openai/gpt-4o-mini"
VECTORSTORE_PATH = "./data/vectorstore"
COLLECTION_NAME = "freiburg_docs_v3large"
MAX_TOKENS = 50000

# Initialize ChromaDB store
try:
    store = ChromaDocumentStore(
        persist_path=VECTORSTORE_PATH,
        collection_name=COLLECTION_NAME
    )
    STORE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Failed to initialize vectorstore: {e}")
    store = None
    STORE_AVAILABLE = False

# Initialize tokenizer for counting
tokenizer = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    return len(tokenizer.encode(text))

def truncate_conversation(messages: list, max_tokens: int) -> list:
    """Keep conversation under max_tokens by removing oldest messages"""
    if not messages:
        return messages
    
    # Always keep system message if it exists
    system_msgs = [msg for msg in messages if msg.get("role") == "system"]
    other_msgs = [msg for msg in messages if msg.get("role") != "system"]
    
    total_tokens = sum(count_tokens(str(msg.get("content", ""))) for msg in messages)
    
    while total_tokens > max_tokens and len(other_msgs) > 1:
        removed = other_msgs.pop(0)  # Remove oldest non-system message
        total_tokens -= count_tokens(str(removed.get("content", "")))
    
    return system_msgs + other_msgs

def create_rag_components():
    """Create the Haystack RAG components"""
    if not STORE_AVAILABLE:
        return None, None, None
    
    # Create components
    text_embedder = VoyageTextEmbedder(
        model=VOYAGE_MODEL,
        api_key=Secret.from_env_var("VOYAGE_API_KEY")
    )
    
    retriever = ChromaEmbeddingRetriever(
        document_store=store,
        top_k=3
    )
    
    chat_generator = OpenRouterChatGenerator(
        api_key=Secret.from_env_var("OPENROUTER_API_KEY"),
        model=LLM_MODEL
    )
    
    return text_embedder, retriever, chat_generator

# Initialize components
text_embedder, retriever, chat_generator = create_rag_components()

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    if not STORE_AVAILABLE:
        await cl.Message(
            content="⚠️ Vectorstore nicht verfügbar. Bitte prüfen Sie die Konfiguration."
        ).send()
        return
    
    # Initialize session
    cl.user_session.set("conversation_history", [])
    cl.user_session.set("privacy_mode", False)
    
    # Welcome message
    await cl.Message(
        content="""🏛️ **Willkommen beim Freibot!**

Ich bin Ihr KI-Assistent für Fragen zu Freiburg im Breisgau. Ich kann Ihnen helfen mit:
- Stadtdaten und Statistiken
- Bevölkerungsinformationen  
- Verkehr und Transport
- Umwelt und Nachhaltigkeit
- Bürgerzufriedenheit

Stellen Sie mir gerne Ihre Frage auf Deutsch oder Englisch!

*Datenschutz: Aktivieren Sie den Privatmodus in den Einstellungen für maximale Privatsphäre.*
        """
    ).send()

@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates"""
    privacy_mode = settings.get("Privacy Mode", False)
    cl.user_session.set("privacy_mode", privacy_mode)
    
    if privacy_mode:
        await cl.Message(content="🔒 Privatmodus aktiviert").send()
    else:
        await cl.Message(content="🔓 Privatmodus deaktiviert").send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    if not text_embedder or not retriever or not chat_generator:
        await cl.Message(content="❌ RAG Komponenten nicht verfügbar").send()
        return
    
    # Get conversation history and privacy setting
    history = cl.user_session.get("conversation_history", [])
    privacy_mode = cl.user_session.get("privacy_mode", False)
    
    # Add current message to history
    history.append({"role": "user", "content": message.content})
    
    # Truncate if too long
    history = truncate_conversation(history, MAX_TOKENS)
    
    # Prepare streaming response
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # 1. Embed the query
        embedding_result = text_embedder.run(text=message.content)
        query_embedding = embedding_result["embedding"]
        
        # 2. Retrieve relevant documents
        retrieval_result = retriever.run(query_embedding=query_embedding)
        documents = retrieval_result["documents"]
        
        # 3. Create context from documents
        context = ""
        if documents:
            context = "\n\n".join([doc.text for doc in documents[:3]])
        
        # 4. Create system message with context
        system_message = f"""Du bist ein hilfsvoller Assistent für die Stadt Freiburg im Breisgau. 
Beantworte Fragen basierend auf den folgenden Dokumenten:

{context}

Antworte auf Deutsch, außer der Nutzer fragt explizit auf Englisch.
Gib immer die Quelle deiner Informationen an."""
        
        # 5. Prepare chat messages
        chat_messages = [ChatMessage.from_system(system_message)]
        for msg_item in history:
            if msg_item["role"] == "user":
                chat_messages.append(ChatMessage.from_user(msg_item["content"]))
            elif msg_item["role"] == "assistant":
                chat_messages.append(ChatMessage.from_assistant(msg_item["content"]))
        
        # 6. Generate response (non-streaming for simplicity)
        generation_kwargs = {
            "extra_headers": {
                "HTTP-Referer": "https://freibot.app",
                "X-Title": "Freibot"
            }
        }
        
        if privacy_mode:
            generation_kwargs["extra_headers"]["X-Private"] = "true"
        
        response_result = chat_generator.run(
            messages=chat_messages,
            generation_kwargs=generation_kwargs
        )
        
        # 7. Stream the response
        if "replies" in response_result:
            response_content = response_result["replies"][0].text
            
            # Stream character by character for visual effect
            for char in response_content:
                await msg.stream_token(char)
            
            # Add to conversation history
            history.append({"role": "assistant", "content": response_content})
            cl.user_session.set("conversation_history", history)
            
            # Add sources if available
            if documents:
                source_text = "\n\n**Quellen:**\n"
                for i, doc in enumerate(documents[:3], 1):
                    source_text += f"{i}. {doc.meta.get('source', 'Unbekannt')}\n"
                await msg.stream_token(source_text)
        
        await msg.update()
        
    except Exception as e:
        error_msg = f"❌ Fehler beim Verarbeiten der Anfrage: {str(e)}"
        await cl.Message(content=error_msg).send()

@cl.author_rename
def rename(orig_author: str):
    """Rename message authors"""
    if orig_author == "Assistant":
        return "Freibot"
    return orig_author

# Chat settings
@cl.on_chat_start
async def setup_settings():
    """Setup chat settings"""
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Switch(
                id="Privacy Mode",
                label="Privatmodus",
                initial=False,
                description="Aktiviert erweiterten Datenschutz"
            )
        ]
    ).send()

if __name__ == "__main__":
    cl.run()