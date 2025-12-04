# codebase_rag/embedder.py
"""Code embedding using Ollama's nomic-embed-code model on inference server."""
import functools
import json
from typing import Any

import requests


@functools.lru_cache(maxsize=1)
def get_ollama_config() -> dict[str, str]:
    """Get Ollama configuration for inference server.

    Returns:
        Dict with endpoint URL and model name
    """
    return {
        "endpoint": "http://192.168.0.121:11434",
        "model": "manutic/nomic-embed-code:7b-q8_0",
    }


def embed_code(code: str, max_length: int = 512) -> list[float]:
    """Generate code embedding using nomic-embed-code via Ollama API.

    Args:
        code: Source code to embed
        max_length: Maximum token length for input (not used with Ollama, kept for compatibility)

    Returns:
        3584-dimensional embedding as list of floats

    Raises:
        RuntimeError: If the Ollama API request fails
    """
    config = get_ollama_config()
    endpoint = config["endpoint"]
    model = config["model"]

    # Ollama embedding API endpoint
    url = f"{endpoint}/api/embeddings"

    payload = {
        "model": model,
        "prompt": code,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Ollama returns embeddings in the "embedding" field
        embedding: list[float] = result["embedding"]
        return embedding

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to generate embedding via Ollama API at {endpoint}: {e}"
        ) from e
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(
            f"Invalid response from Ollama API at {endpoint}: {e}"
        ) from e
