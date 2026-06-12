"""
Embedding Generation Service — OpenAI text-embedding-3-small.
Generates 1536-dimension vectors for student profiles and opportunities.
"""
from typing import Sequence

import numpy as np
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _generate_mock_embedding(text: str) -> list[float]:
    """
    Generates a deterministic 1536-dimensional unit vector based on the SHA-256 hash of the input text.
    Ensures pgvector can index and compare them, and similar/identical texts will have high similarity.
    """
    import hashlib
    # Compute sha256 hash of the text
    hasher = hashlib.sha256(text.encode("utf-8"))
    hash_bytes = hasher.digest()
    
    # Seed a random generator with the hash bytes to get deterministic random numbers
    seed = int.from_bytes(hash_bytes[:4], "big")
    rng = np.random.default_rng(seed)
    
    # Generate 1536 dimensions
    vector = rng.standard_normal(1536).astype(np.float32)
    
    # Normalize to unit vector
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
        
    return vector.tolist()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
async def generate_embedding(text: str) -> list[float]:
    """
    Generate a single embedding vector for the given text.
    Model: text-embedding-3-small (1536 dimensions) or local mock fallback.
    """
    if not settings.openai_api_key or "SECRET" in settings.openai_api_key or "your-openai-key" in settings.openai_api_key:
        return _generate_mock_embedding(text)

    client = get_openai_client()
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text.replace("\n", " ").strip(),
        dimensions=settings.openai_embedding_dimensions,
    )
    return response.data[0].embedding


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    """
    if not settings.openai_api_key or "SECRET" in settings.openai_api_key or "your-openai-key" in settings.openai_api_key:
        return [_generate_mock_embedding(t) for t in texts]

    client = get_openai_client()
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=cleaned,
        dimensions=settings.openai_embedding_dimensions,
    )
    # Sort by index to maintain order
    sorted_embeddings = sorted(response.data, key=lambda x: x.index)
    return [e.embedding for e in sorted_embeddings]


def build_profile_embedding_text(profile_data: dict) -> str:
    """
    Construct the text representation of a student profile for embedding.
    Concatenates key semantic fields.
    """
    parts = []

    if field := profile_data.get("field_of_study"):
        parts.append(f"Field of study: {field}")

    if skills := profile_data.get("skills"):
        parts.append(f"Skills: {', '.join(skills)}")

    if interests := profile_data.get("interests"):
        parts.append(f"Interests: {', '.join(interests)}")

    if goals := profile_data.get("career_goals"):
        parts.append(f"Career goals: {goals}")

    if goal_tags := profile_data.get("career_goal_tags"):
        parts.append(f"Goal areas: {', '.join(goal_tags)}")

    if languages := profile_data.get("languages"):
        parts.append(f"Languages: {', '.join(languages)}")

    # Add education context
    for edu in profile_data.get("education", []):
        if edu.get("field"):
            parts.append(f"Studied {edu['field']} at {edu.get('institution', '')}")

    return ". ".join(parts)


def build_opportunity_embedding_text(opportunity_data: dict) -> str:
    """
    Construct the text representation of an opportunity for embedding.
    """
    parts = []

    parts.append(opportunity_data.get("title", ""))

    if org := opportunity_data.get("organization"):
        parts.append(f"by {org}")

    if opp_type := opportunity_data.get("type"):
        parts.append(f"Type: {opp_type}")

    if desc := opportunity_data.get("description"):
        parts.append(desc[:1000])  # Cap at 1000 chars for token efficiency

    eligibility = opportunity_data.get("eligibility", {}) or {}
    if fos := eligibility.get("field_of_study"):
        parts.append(f"For students in: {', '.join(fos)}")

    return ". ".join(filter(None, parts))


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
