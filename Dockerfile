# Minimal Python container for FrAIbot
FROM python:3.13-slim

WORKDIR /app

# Install build dependencies (for compiled Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Essential dependencies - Chroma for vectors
RUN pip install --no-cache-dir \
    langchain-community==0.3.13 \
    langchain-openai==0.2.14 \
    anthropic==0.59.0 \
    pypdf \
    fastapi==0.115.6 \
    uvicorn==0.34.0 \
    chromadb==0.4.22 \
    python-dotenv==1.0.1 \
    langchain==0.3.13 \
    numpy

# DEBUG: Check what Railway can see in build context
RUN echo "=== Build context root ==="
RUN ls -la || echo "ls failed"
RUN echo "=== Checking for data directory ==="
RUN ls -la data/ || echo "data/ directory not found"
RUN echo "=== Checking for data/vectorstore ==="
RUN ls -la data/vectorstore/ || echo "data/vectorstore/ directory not found"
RUN echo "=== File sizes if vectorstore exists ==="
RUN du -h data/vectorstore/* 2>/dev/null || echo "Cannot check vectorstore file sizes"
RUN echo "=== End debug info ==="

# Copy core files only - NO secrets  
COPY src/ ./src/
# TEMPORARILY COMMENTED OUT THE FAILING LINE
# COPY data/vectorstore/ ./data/vectorstore/

ENV PYTHONPATH=/app

# Web app ready
CMD ["python", "src/web_app_claude.py"]
