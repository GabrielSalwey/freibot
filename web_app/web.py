"""
Web interface for Freibot
Serves an HTML chat interface for the API
"""

from fastapi.responses import HTMLResponse

def get_web_interface() -> str:
    """Return the HTML content for the web interface."""
    return """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Freibot - Freiburg Q&A System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            background: #f9f9f9;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 10px;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            background: #667eea;
            color: white;
            margin-left: 20%;
            text-align: right;
        }
        
        .bot-message {
            background: white;
            color: #333;
            margin-right: 20%;
            border: 1px solid #e0e0e0;
        }
        
        .source {
            font-size: 0.85em;
            color: #666;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #5a67d8;
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #666;
            margin: 10px 0;
        }
        
        .stats {
            margin-top: 20px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 10px;
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Freibot</h1>
        <p class="subtitle">Ihr KI-Assistent für Freiburg Stadtdaten</p>
        
        <div class="chat-container" id="chatContainer">
            <div class="message bot-message">
                Willkommen! Ich kann Ihnen Fragen zu Freiburg beantworten. 
                Fragen Sie mich zum Beispiel nach Einwohnerzahlen, Stadtteilen oder städtischen Dienstleistungen.
            </div>
        </div>
        
        <div class="loading" id="loading">Suche nach Antwort...</div>
        
        <div class="input-container">
            <input 
                type="text" 
                id="questionInput" 
                placeholder="Stellen Sie Ihre Frage zu Freiburg..."
                onkeypress="if(event.key === 'Enter') sendQuestion()"
            >
            <button onclick="sendQuestion()" id="sendButton">Fragen</button>
        </div>
        
        <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 10px;">
            <label style="display: flex; align-items: center; font-weight: bold; color: #e74c3c;">
                <input type="checkbox" id="privacyMode" style="margin-right: 8px; transform: scale(1.2);">
                🔒 Datenschutz-Modus (schwächere Modelle, keine Protokollierung)
            </label>
        </div>
        
        <div class="stats" id="stats"></div>
    </div>
    
    <script>
        let sessionId = 'session_' + Date.now();
        
        async function sendQuestion() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            
            if (!question) return;
            
            const privacyMode = document.getElementById('privacyMode').checked;
            
            // Disable input
            input.disabled = true;
            document.getElementById('sendButton').disabled = true;
            document.getElementById('loading').style.display = 'block';
            
            // Add user message to chat
            addMessage(question, 'user');
            
            // Clear input
            input.value = '';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question,
                        privacy_mode: privacyMode,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (data.answer) {
                    addMessage(data.answer, 'bot', data.sources);
                } else if (data.error) {
                    addMessage('Fehler: ' + data.error, 'bot');
                } else {
                    addMessage('Entschuldigung, es ist ein Fehler aufgetreten.', 'bot');
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('Verbindungsfehler. Bitte versuchen Sie es später erneut.', 'bot');
            } finally {
                // Re-enable input
                input.disabled = false;
                document.getElementById('sendButton').disabled = false;
                document.getElementById('loading').style.display = 'none';
                input.focus();
            }
        }
        
        function addMessage(text, type, sources = null) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            let content = text;
            
            // Add sources if available
            if (sources && sources.length > 0 && type === 'bot') {
                content += '<div class="source">Quellen: ';
                sources.forEach((source, i) => {
                    content += `[${source.id}] ${source.document}`;
                    if (source.page) content += ` (S. ${source.page})`;
                    if (i < sources.length - 1) content += ', ';
                });
                content += '</div>';
            }
            
            messageDiv.innerHTML = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Load stats on page load
        async function loadStats() {
            try {
                const response = await fetch('/stats');
                const data = await response.json();
                document.getElementById('stats').innerHTML = 
                    `${data.pdf_count} PDFs | ${data.chunk_count} Dokumente | Modell: ${data.llm_model}`;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Privacy mode change handler
        document.getElementById('privacyMode').addEventListener('change', function() {
            if (this.checked) {
                sessionId = 'privacy_' + Date.now();
            }
        });
        
        // Initialize
        loadStats();
        document.getElementById('questionInput').focus();
    </script>
</body>
</html>
    """