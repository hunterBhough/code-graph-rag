# codebase_rag/embedder.py
"""Code embedding using TEI (Text Embeddings Inference) with bge-m3 model."""
import functools
import json
from typing import Any

import requests


@functools.lru_cache(maxsize=1)
def get_embedding_config() -> dict[str, str]:
    """Get embedding configuration for TEI inference server.

    Returns:
        Dict with endpoint URL and model name
    """
    return {
        "endpoint": "http://192.168.0.121:8081",
        "model": "bge-m3",
    }


def embed_code(code: str, max_length: int = 512) -> list[float]:
    """Generate code embedding using bge-m3 via TEI API.

    Args:
        code: Source code to embed
        max_length: Maximum token length for input (not used with TEI, kept for compatibility)

    Returns:
        1024-dimensional embedding as list of floats

    Raises:
        RuntimeError: If the TEI API request fails
    """
    config = get_embedding_config()
    endpoint = config["endpoint"]
    model = config["model"]

    # TEI embedding API endpoint
    url = f"{endpoint}/embed"

    payload = {
        "inputs": [code],
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        # TEI returns a list of embeddings, we take the first one
        embedding: list[float] = result[0]
        return embedding

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to generate embedding via TEI API at {endpoint}: {e}"
        ) from e
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        raise RuntimeError(
            f"Invalid response from TEI API at {endpoint}: {e}"
        ) from e
