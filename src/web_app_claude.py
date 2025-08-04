from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

# Add src to path
sys.path.append(str(Path(__file__).parent))

from document_processor_claude import FreibotRAG

# Session memory storage
conversation_memory = {}

class ConversationMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        
    def to_dict(self):
        return {"role": self.role, "content": self.content}
    
    def token_estimate(self) -> int:
        """Rough token count (4 chars ≈ 1 token)"""
        return len(self.content) // 4

def _optimize_conversation_history(history: List[ConversationMessage]) -> List[ConversationMessage]:
    """Smart sliding window with semantic importance"""
    MAX_HISTORY_TOKENS = 8000  # Reserve 12k for RAG + 180k for generation
    
    if not history:
        return history
    
    # Always keep first exchange (context) and last 3 exchanges (recency)
    protected_messages = []
    if len(history) >= 2:
        protected_messages.extend(history[:2])  # First Q&A
    if len(history) > 6:
        protected_messages.extend(history[-6:])  # Last 3 Q&A pairs
    else:
        protected_messages = history
    
    # Calculate token usage
    total_tokens = sum(msg.token_estimate() for msg in protected_messages)
    
    if total_tokens <= MAX_HISTORY_TOKENS:
        return protected_messages
    
    # Emergency fallback: keep only last 2 exchanges
    return history[-4:] if len(history) >= 4 else history

# Setup environment
def setup_environment():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

setup_environment()

app = FastAPI(title="Freibot API (Claude Edition)", description="Freiburg AI Assistant API powered by Claude", version="1.0.0")

# Global RAG instance
rag_system = None

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    question: str

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. The API will not work properly.")
        return
        
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set. We need this for embeddings.")
        return
    
    rag_system = FreibotRAG(claude_model="claude-3-haiku-20240307")
    if rag_system.load_vectorstore():
        print("✅ RAG system with Claude initialized successfully")
    else:
        print("❌ Failed to initialize RAG system")
        rag_system = None

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Freibot - Powered by Claude</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            .claude-badge {
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                display: inline-block;
                margin-top: 10px;
                font-size: 0.9rem;
            }
            
            .chat-container {
                padding: 30px;
                min-height: 500px;
            }
            
            .chat-messages {
                max-height: 450px;
                overflow-y: auto;
                margin-bottom: 20px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            
            .message {
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 10px;
                animation: fadeIn 0.3s ease-in;
            }
            
            .user-message {
                background: #e3f2fd;
                margin-left: 20px;
            }
            
            .bot-message {
                background: #fff3e0;
                margin-right: 20px;
                border-left: 4px solid #ff6b6b;
            }
            
            .input-container {
                display: flex;
                gap: 10px;
            }
            
            #questionInput {
                flex: 1;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s;
            }
            
            #questionInput:focus {
                border-color: #ff6b6b;
            }
            
            #askButton {
                padding: 15px 30px;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                transition: transform 0.2s;
            }
            
            #askButton:hover {
                transform: translateY(-2px);
            }
            
            #askButton:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .sources {
                margin-top: 10px;
                padding: 15px;
                background: #f1f8e9;
                border-radius: 8px;
                font-size: 0.9rem;
                border-left: 4px solid #4caf50;
            }
            
            .loading {
                display: none;
                text-align: center;
                color: #666;
                padding: 20px;
            }
            
            .error {
                background: #ffebee;
                color: #c62828;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .examples {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .examples h3 {
                margin-bottom: 15px;
                color: #333;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .example-question {
                background: white;
                padding: 12px 18px;
                margin: 8px 0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                border: 1px solid #e0e0e0;
                border-left: 4px solid #ff6b6b;
            }
            
            .example-question:hover {
                background: #fff3e0;
                transform: translateX(5px);
            }
            
            .claude-features {
                background: linear-gradient(135deg, #ff6b6b20 0%, #ee5a2420 100%);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .feature-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }
            
            .feature {
                background: white;
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Freibot</h1>
                <p>Ihr KI-Assistent für Freiburg-Daten</p>
                <div class="claude-badge">🧠 Powered by Claude</div>
                <div style="display: flex; gap: 10px; justify-content: center; margin-top: 10px;">
                    <button onclick="clearMemory()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 16px; border-radius: 15px; cursor: pointer;">🗑️ Reset</button>
                    <div id="memoryIndicator" style="background: #4caf50; color: white; padding: 8px 16px; border-radius: 15px; font-size: 0.8rem;">💭 Kurz (0)</div>
                </div>
            </div>
            
            <div class="chat-container">
                <div class="claude-features">
                    <h3>🧠 Claude's Superpowers:</h3>
                    <div class="feature-list">
                        <div class="feature">📊 Detailed Analysis</div>
                        <div class="feature">🔍 Deep Understanding</div>
                        <div class="feature">🇩🇪 Excellent German</div>
                        <div class="feature">📈 Data Comparisons</div>
                    </div>
                </div>
                
                <div class="examples">
                    <h3>💡 Example Questions (Try Claude's analytical power!):</h3>
                    <div class="example-question" onclick="askExample('Analysiere die Bevölkerungsentwicklung in Freiburg über die letzten Jahre')">
                        Analysiere die Bevölkerungsentwicklung in Freiburg über die letzten Jahre
                    </div>
                    <div class="example-question" onclick="askExample('Vergleiche die Wahlergebnisse zwischen verschiedenen Stadtbezirken')">
                        Vergleiche die Wahlergebnisse zwischen verschiedenen Stadtbezirken
                    </div>
                    <div class="example-question" onclick="askExample('Was sind die wichtigsten sozialen Herausforderungen laut Sozialbericht?')">
                        Was sind die wichtigsten sozialen Herausforderungen laut Sozialbericht?
                    </div>
                    <div class="example-question" onclick="askExample('Erkläre mir die Ergebnisse der letzten Gemeinderatswahl im Detail')">
                        Erkläre mir die Ergebnisse der letzten Gemeinderatswahl im Detail
                    </div>
                    <div class="example-question" onclick="askExample('Welche demografischen Trends zeigen die neuesten Statistiken?')">
                        Welche demografischen Trends zeigen die neuesten Statistiken?
                    </div>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="message bot-message">
                        <strong>🧠 Claude:</strong> Hallo! Ich bin Claude und helfe Ihnen dabei, die Freiburg-Daten zu verstehen. Ich kann komplexe Analysen durchführen, Trends erklären und detaillierte Vergleiche anstellen. Fragen Sie mich etwas!
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    🧠 Claude analysiert die Dokumente...
                </div>
                
                <div class="input-container">
                    <input type="text" id="questionInput" placeholder="Stellen Sie Claude eine detaillierte Frage über Freiburg..." 
                           onkeypress="handleKeyPress(event)">
                    <button id="askButton" onclick="askQuestion()">Fragen</button>
                </div>
            </div>
        </div>
        
        <script>
            // Session management
            let sessionId = localStorage.getItem('freibot-session') || generateSessionId();
            localStorage.setItem('freibot-session', sessionId);
            
            function generateSessionId() {
                return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            }
            
            function clearMemory() {
                sessionId = generateSessionId();
                localStorage.setItem('freibot-session', sessionId);
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message bot-message">
                        <strong>🧠 Claude:</strong> Neue Unterhaltung gestartet! Ich bin bereit für Ihre Fragen über Freiburg.
                    </div>
                `;
                updateMemoryIndicator(0);
            }
            
            function updateMemoryIndicator(messageCount) {
                const indicator = document.getElementById('memoryIndicator');
                if (!indicator) return;
                
                const level = Math.min(3, Math.floor(messageCount / 4));
                const colors = ['#4caf50', '#ff9800', '#f44336', '#9c27b0'];
                const labels = ['Kurz', 'Mittel', 'Lang', 'Optimiert'];
                
                indicator.style.background = colors[level];
                indicator.textContent = `💭 ${labels[level]} (${messageCount})`;
            }
            
            let messageCount = 0;
            
            function addMessage(sender, message, isUser = false) {
                const chatMessages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                messageDiv.innerHTML = `<strong>${sender}:</strong> ${message.replace(/\\n/g, '<br>')}`;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function addSources(sources) {
                const chatMessages = document.getElementById('chatMessages');
                if (sources && sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'sources';
                    sourcesDiv.innerHTML = `
                        <strong>📚 Quellen:</strong><br>
                        ${sources.map((source, i) => 
                            `${i + 1}. <strong>${source.title}</strong> (${source.year})<br>
                            &nbsp;&nbsp;&nbsp;&nbsp;→ ${source.document_type}, Seite ${source.page}`
                        ).join('<br>')}
                    `;
                    chatMessages.appendChild(sourcesDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
            
            function showLoading(show) {
                document.getElementById('loading').style.display = show ? 'block' : 'none';
                document.getElementById('askButton').disabled = show;
                if (show) {
                    document.getElementById('askButton').textContent = 'Denkt...';
                } else {
                    document.getElementById('askButton').textContent = 'Fragen';
                }
            }
            
            async function askQuestion() {
                const input = document.getElementById('questionInput');
                const question = input.value.trim();
                
                if (!question) return;
                
                // Add user message
                addMessage('👤 Sie', question, true);
                messageCount += 2; // User + bot response
                updateMemoryIndicator(messageCount);
                input.value = '';
                
                showLoading(true);
                
                try {
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            question: question,
                            session_id: sessionId
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        addMessage('🧠 Claude', data.answer);
                        addSources(data.sources);
                    } else {
                        addMessage('🧠 Claude', `❌ Fehler: ${data.detail || 'Unbekannter Fehler'}`);
                    }
                } catch (error) {
                    addMessage('🧠 Claude', `❌ Verbindungsfehler: ${error.message}`);
                }
                
                showLoading(false);
            }
            
            function askExample(question) {
                document.getElementById('questionInput').value = question;
                askQuestion();
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    askQuestion();
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question with conversation memory"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Get or create session ID
    session_id = request.session_id or str(uuid4())
    
    # Get conversation history
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
    
    history = conversation_memory[session_id]
    
    # Add user message to history
    history.append(ConversationMessage("user", request.question))
    
    # Pass history to RAG system
    result = rag_system.ask_question_with_history(request.question, history)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Add assistant response to history
    history.append(ConversationMessage("assistant", result["answer"]))
    
    # Smart memory management: preserve important context
    conversation_memory[session_id] = _optimize_conversation_history(history)
    
    return QuestionResponse(**result)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_system_loaded": rag_system is not None,
        "claude_api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "model": "claude-3-haiku-20240307"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
