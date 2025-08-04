# Minimal Python container for FrAIbot
FROM python:3.13-slim

WORKDIR /app

# Essential dependencies only
RUN pip install --no-cache-dir \
    langchain-community==0.3.13 \
    langchain-openai==0.2.14 \
    anthropic==0.59.0 \
    PyPDF2==3.0.1

# Copy core files only - NO secrets
COPY src/ ./src/

ENV PYTHONPATH=/app

# CLI ready
CMD ["python", "src/cli_claude.py", "-q", "System ready"]
