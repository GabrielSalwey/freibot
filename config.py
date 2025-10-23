"""
Centralized configuration for Freibot.
Modify these settings to change models and vectorstore configuration.
"""

# Voyage AI Configuration
VOYAGE_MODEL = "voyage-3.5"
VOYAGE_INPUT_TYPE_DOCUMENT = "document"
VOYAGE_INPUT_TYPE_QUERY = "query"
EMBEDDING_DIM = 1024  # voyage-3.5 dimension
EMBEDDING_DTYPE = "int8"  # Quantization type

# Qdrant Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "freiburg_docs_v1"

# LLM Configuration
LLM_MODEL = "openai/gpt-4o-mini"
